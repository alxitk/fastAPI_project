import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.exceptions.exceptions import InvalidCredentialsError, UserNotActiveError, TokenNotFoundError
from app.modules.users.crud import token as token_crud
from app.modules.users.models.enums import UserGroupEnum
from app.modules.users.models.token import RefreshTokenModel, PasswordResetTokenModel, ActivationTokenModel
from app.modules.users.models.user import User, UserGroupModel
from app.notifications.interfaces import EmailSenderInterface
from app.utils.interfaces import JWTAuthManagerInterface
from app.utils.security import pwd_context


class AuthService:
    """
    Authentication service.
    Contains business logic for authentication and token handling.
    """

    def __init__(
        self,
        db: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        login_time_days: int,
        email_sender: EmailSenderInterface | None = None,
        base_url: str = "http://localhost:8000",
    ):
        self._db = db
        self._jwt_manager = jwt_manager
        self._login_time_days = login_time_days
        self._email_sender = email_sender
        self._base_url = base_url

    async def register_user(self, email: str, password: str) -> User:
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")

        stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
        result = await self._db.execute(stmt)
        user_group = result.scalars().first()
        if not user_group:
            raise HTTPException(status_code=500, detail="Default user group not found")

        hashed_password = pwd_context.hash(password)
        new_user = User(
            email=email,
            _hashed_password=hashed_password,
            is_active=False,
            group_id=user_group.id
        )

        self._db.add(new_user)
        await self._db.commit()
        await self._db.refresh(new_user)

        if self._email_sender:
            activation_token = await token_crud.create_activation_token(self._db, new_user.id)
            await self._db.commit()
            activation_link = f"{self._base_url}/auth/activate?email={email}&token={activation_token.token}"
            await self._email_sender.send_activation_email(email, activation_link)

        return new_user


    async def login(self, email: str, password: str) -> tuple[str, str]:
        user = await self._get_user_by_email(email)

        if not user or not user.verify_password(password):
            raise InvalidCredentialsError

        if not user.is_active:
            raise UserNotActiveError

        access_token = self._jwt_manager.create_access_token(
            {"user_id": user.id}
        )

        refresh_token = self._jwt_manager.create_refresh_token(
            {"user_id": user.id}
        )

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self._login_time_days
        )

        await self._create_refresh_token(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )

        return access_token, refresh_token


    async def refresh_access_token(self, refresh_token: str) -> str:
        payload = self._jwt_manager.decode_refresh_token(refresh_token)
        user_id: int = payload["user_id"]

        token_exists = await self._refresh_token_exists(refresh_token)
        if not token_exists:
            raise TokenNotFoundError

        return self._jwt_manager.create_access_token(
            {"user_id": user_id}
        )


    async def logout(self, refresh_token: str) -> None:
        stmt = delete(RefreshTokenModel).where(
            RefreshTokenModel.token == refresh_token
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def logout_all(self, user_id: int) -> None:
        stmt = delete(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def logout_all_current_user(self, user_id: int) -> None:
        """Logout current user from all devices."""
        await self.logout_all(user_id)


    async def reset_password(
        self,
        user_id: int,
        new_password: str,
    ) -> None:
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.set_password(new_password)

        await self._db.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.user_id == user_id
            )
        )
        await self._db.commit()


    async def _get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def _create_refresh_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> None:
        refresh = RefreshTokenModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self._db.add(refresh)
        await self._db.commit()

    async def _refresh_token_exists(self, token: str) -> bool:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token == token
        )
        result = await self._db.execute(stmt)
        return result.scalars().first() is not None

    async def send_password_reset_email(self, email: str) -> None:
        """Send password reset email to user."""
        user = await self._get_user_by_email(email)
        if not user:
            return

        password_reset_token = await token_crud.create_password_reset_token(self._db, user.id)
        await self._db.commit()

        if self._email_sender:
            reset_link = f"{self._base_url}/auth/password-reset/complete?email={email}&token={password_reset_token.token}"
            await self._email_sender.send_password_reset_email(email, reset_link)


    async def reset_password_by_token(
        self,
        email: str,
        token: str,
        new_password: str,
    ) -> None:
        """Reset password using token from email."""
        user = await self._get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        password_reset_token = await token_crud.get_password_reset_by_token(self._db, token)
        if not password_reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        if password_reset_token.user_id != user.id:
            raise HTTPException(status_code=400, detail="Token does not match user")

        if password_reset_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Token has expired")

        user.set_password(new_password)

        await self._db.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.id == password_reset_token.id
            )
        )
        await self._db.commit()

        if self._email_sender:
            login_link = f"{self._base_url}/auth/login"
            await self._email_sender.send_password_reset_complete_email(email, login_link)

    async def activate_user(self, email: str, token: str) -> None:
        """Activate user account using activation token."""
        user = await self._get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        activation_token = await token_crud.get_by_token(self._db, token)
        if not activation_token:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        if activation_token.user_id != user.id:
            raise HTTPException(status_code=400, detail="Token does not match user")

        if activation_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Token has expired")

        user.is_active = True

        await self._db.execute(
            delete(ActivationTokenModel).where(
                ActivationTokenModel.id == activation_token.id
            )
        )
        await self._db.commit()

        if self._email_sender:
            login_link = f"{self._base_url}/auth/login"
            await self._email_sender.send_activation_complete_email(email, login_link)

    async def resend_activation_token(self, email: str):
        user = await self._get_user_by_email(email)
        if not user or user.is_active:
            return

        now = datetime.now(timezone.utc)

        result = await self._db.execute(
            select(ActivationTokenModel)
            .where(
                ActivationTokenModel.user_id == user.id,
                ActivationTokenModel.expires_at > now,
            )
            .order_by(ActivationTokenModel.expires_at.desc())
        )
        token_obj = result.scalars().first()

        if token_obj:
            token = token_obj.token
        else:
            await self._db.execute(
                delete(ActivationTokenModel).where(
                    ActivationTokenModel.user_id == user.id
                )
            )

            token = secrets.token_urlsafe(32)
            new_token = ActivationTokenModel(
                user_id=user.id,
                token=token,
                expires_at=now + timedelta(hours=24),
            )
            self._db.add(new_token)
            await self._db.commit()

        activation_link = (
            f"{self._base_url}/auth/activate?email={email}&token={token}"
        )

        if self._email_sender:
            await self._email_sender.send_activation_email(email, activation_link)
