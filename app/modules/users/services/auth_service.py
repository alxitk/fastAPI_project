from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.exceptions.exceptions import (
    InvalidCredentialsError,
    UserNotActiveError,
    TokenNotFoundError,
)
from app.modules.users.models.token import RefreshTokenModel
from app.modules.users.services.user_service import UserService
from app.notifications.interfaces import EmailSenderInterface
from app.utils.interfaces import JWTAuthManagerInterface


class AuthService:
    """
    Service responsible for handling authentication-related operations such as login,
    token refresh, and logout. It manages user credentials verification, token creation,
    and token revocation.
    """
    def __init__(
        self,
        db: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        login_time_days: int,
        user_service: UserService,
        email_sender: EmailSenderInterface | None = None,
        base_url: str = "http://localhost:8000",
    ) -> None:
        self._db = db
        self._jwt_manager = jwt_manager
        self._login_time_days = login_time_days
        self._user_service = user_service
        self._email_sender = email_sender
        self._base_url = base_url

    async def login(self, email: str, password: str) -> tuple[str, str]:
        """
        Authenticate a user using email and password, then generate and store
        JWT access and refresh tokens.

        Args:
            email (str): The user's email address.
            password (str): The user's password.

        Returns:
            tuple[str, str]: A tuple containing the access token and refresh token.

        Raises:
            InvalidCredentialsError: If the email or password is incorrect.
            UserNotActiveError: If the user account is not active.
        """
        user = await self._user_service._get_user_by_email(email)

        if not user or not user.verify_password(password):
            raise InvalidCredentialsError

        if not user.is_active:
            raise UserNotActiveError

        access_token = self._jwt_manager.create_access_token({"user_id": user.id})

        refresh_token = self._jwt_manager.create_refresh_token({"user_id": user.id})

        expires_at = datetime.now(timezone.utc) + timedelta(days=self._login_time_days)

        await self._create_refresh_token(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )

        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate a new access token using a valid refresh token.

        Args:
            refresh_token (str): The refresh token to validate and use.

        Returns:
            str: A new access token.

        Raises:
            TokenNotFoundError: If the refresh token does not exist or is invalid.
        """
        payload = self._jwt_manager.decode_refresh_token(refresh_token)
        user_id: int = payload["user_id"]

        token_exists = await self._refresh_token_exists(refresh_token)
        if not token_exists:
            raise TokenNotFoundError

        return self._jwt_manager.create_access_token({"user_id": user_id})

    async def logout(self, refresh_token: str) -> None:
        """
        Invalidate a specific refresh token, effectively logging out the session
        associated with that token.

        Args:
            refresh_token (str): The refresh token to be invalidated.
        """
        stmt = delete(RefreshTokenModel).where(RefreshTokenModel.token == refresh_token)
        await self._db.execute(stmt)
        await self._db.commit()

    async def logout_all(self, user_id: int) -> None:
        """
        Invalidate all refresh tokens for a given user, logging out from all devices.

        Args:
            user_id (int): The ID of the user whose tokens are to be invalidated.
        """
        stmt = delete(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
        await self._db.execute(stmt)
        await self._db.commit()

    async def logout_all_current_user(self, user_id: int) -> None:
        """
        Logout the current user from all devices by invalidating all their refresh tokens.

        Args:
            user_id (int): The ID of the current user.
        """
        await self.logout_all(user_id)

    async def _create_refresh_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> None:
        """
        Internal helper to create and store a refresh token in the database.

        Args:
            user_id (int): The ID of the user.
            token (str): The refresh token string.
            expires_at (datetime): The expiration datetime of the token.
        """
        refresh = RefreshTokenModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self._db.add(refresh)
        await self._db.commit()

    async def _refresh_token_exists(self, token: str) -> bool:
        """
        Internal helper to check if a refresh token exists in the database.

        Args:
            token (str): The refresh token string to check.

        Returns:
            bool: True if the token exists, False otherwise.
        """
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        result = await self._db.execute(stmt)
        return result.scalars().first() is not None
