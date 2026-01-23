from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.exceptions.exceptions import TokenExpiredError
from app.modules.users.crud import token as token_crud
from app.modules.users.models.token import PasswordResetTokenModel
from app.modules.users.models.user import User
from app.modules.users.services.user_service import UserService
from app.notifications.interfaces import EmailSenderInterface
from app.utils.interfaces import JWTAuthManagerInterface
from app.utils.security import hash_password, validate_strong_password, verify_password


class PasswordService:
    """
    Authentication service.
    Contains business logic for authentication and token handling.
    """

    def __init__(
        self,
        db: AsyncSession,
        user_service: UserService,
        jwt_manager: JWTAuthManagerInterface,
        login_time_days: int,
        email_sender: EmailSenderInterface | None = None,
        base_url: str = "http://localhost:8000",
    ):
        self._db = db
        self._user_service = user_service
        self._jwt_manager = jwt_manager
        self._login_time_days = login_time_days
        self._email_sender = email_sender
        self._base_url = base_url


    async def reset_password_by_token(
                self,
                email: str,
                token: str,
                new_password: str,
        ) -> None:
            """Reset password using token from email."""
            user = await self._user_service._get_user_by_email(email)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            password_reset_token = await token_crud.get_password_reset_by_token(self._db, token)
            if not password_reset_token:
                raise HTTPException(status_code=400, detail="Invalid or expired token")

            if password_reset_token.user_id != user.id:
                raise HTTPException(status_code=400, detail="Token does not match user")

            if password_reset_token.expires_at < datetime.now(timezone.utc):
                raise TokenExpiredError

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


    async def change_password(
            self,
            user_id: int,
            old_password: str,
            new_password: str
    ) -> None:
            user = await self._user_service._get_user_by_id(user_id)
            if not verify_password(old_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Old password is incorrect")

            if old_password == new_password:
                raise HTTPException(status_code=400, detail="New password must be different")

            validate_strong_password(new_password)

            user.hashed_password = hash_password(new_password)
            await self._db.commit()


    async def send_password_reset_email(
            self,
            email: str
    ) -> None:
        """Send password reset email to user."""
        user = await self._user_service._get_user_by_email(email)
        if not user:
            return

        password_reset_token = await token_crud.create_password_reset_token(self._db, user.id)
        await self._db.commit()

        if self._email_sender:
            reset_link = f"{self._base_url}/auth/password-reset/complete?email={email}&token={password_reset_token.token}"
            await self._email_sender.send_password_reset_email(email, reset_link)


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