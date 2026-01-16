from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.exceptions.exceptions import InvalidCredentialsError, UserNotActiveError, TokenNotFoundError
from app.modules.users.models.token import RefreshTokenModel, PasswordResetTokenModel
from app.modules.users.models.user import User
from app.utils.interfaces import JWTAuthManagerInterface
from app.utils.security import verify_password, hash_password


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
    ):
        self._db = db
        self._jwt_manager = jwt_manager
        self._login_time_days = login_time_days


    async def login(self, email: str, password: str) -> tuple[str, str]:
        user = await self._get_user_by_email(email)

        if not user or not verify_password(password, user.password):
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


    async def reset_password(
        self,
        user_id: int,
        new_password: str,
    ) -> None:
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalars().first()

        user.password = hash_password(new_password)

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
