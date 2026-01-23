from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.exceptions.exceptions import InvalidCredentialsError, UserNotActiveError, TokenNotFoundError
from app.modules.users.models.token import RefreshTokenModel
from app.modules.users.models.user import User
from app.modules.users.services.user_service import UserService
from app.notifications.interfaces import EmailSenderInterface
from app.utils.interfaces import JWTAuthManagerInterface


class AuthService:
    def __init__(
        self,
        db: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        login_time_days: int,
        user_service: UserService,
        email_sender: EmailSenderInterface | None = None,
        base_url: str = "http://localhost:8000",
    ):
        self._db = db
        self._jwt_manager = jwt_manager
        self._login_time_days = login_time_days
        self._user_service = user_service
        self._email_sender = email_sender
        self._base_url = base_url


    async def login(self, email: str, password: str) -> tuple[str, str]:
        user = await self._user_service._get_user_by_email(email)

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
