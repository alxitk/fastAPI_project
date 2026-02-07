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
    Password management service.

    Responsible for:
    - Changing password for authenticated users
    - Handling password reset flow via email tokens
    - Validating password strength
    - Sending password-related notification emails
    """

    def __init__(
        self,
        db: AsyncSession,
        user_service: UserService,
        jwt_manager: JWTAuthManagerInterface,
        login_time_days: int,
        email_sender: EmailSenderInterface | None = None,
        base_url: str = "http://localhost:8000",
    ) -> None:
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
        """
        Reset user password using a password reset token.

        This method is used when a user forgot their password and follows
        the reset link sent via email.

        Args:
            email (str): User email address.
            token (str): Password reset token from email.
            new_password (str): New password to set.

        Raises:
            HTTPException: If user or token is invalid.
            TokenExpiredError: If reset token has expired.
        """
        # Fetch user from database
        user = await self._user_service._get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        password_reset_token = await token_crud.get_password_reset_by_token(
            self._db, token
        )
        if not password_reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        if password_reset_token.user_id != user.id:
            raise HTTPException(status_code=400, detail="Token does not match user")

        if password_reset_token.expires_at < datetime.now(timezone.utc):
            raise TokenExpiredError

        # Validate password rules
        user.set_password(new_password)

        # Remove used password reset tokens
        await self._db.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.id == password_reset_token.id
            )
        )
        await self._db.commit()

        if self._email_sender:
            login_link = f"{self._base_url}/auth/login"
            await self._email_sender.send_password_reset_complete_email(
                email, login_link
            )

    async def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> None:
        """
        Change password for an authenticated user.

        This method requires the user to provide their current password
        and a new password. It is intended for logged-in users.

        Args:
            user_id (int): ID of the authenticated user.
            old_password (str): Current password.
            new_password (str): New password.

        Raises:
            HTTPException: If old password is incorrect or new password is invalid.
        """
        # Fetch user from database
        user = await self._user_service._get_user_by_id(user_id)
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=400,
                detail="Old password is incorrect"
            )

        if old_password == new_password:
            raise HTTPException(
                status_code=400,
                detail="New password must be different"
            )

        # Validate password rules
        validate_strong_password(new_password)

        user.hashed_password = hash_password(new_password)
        await self._db.commit()

    async def send_password_reset_email(self, email: str) -> None:
        """
        Send a password reset email to the user.

        If the email does not exist, the method silently returns
        to avoid leaking user existence.

        Args:
            email (str): User email address.
        """
        # Fetch user from database
        user = await self._user_service._get_user_by_email(email)
        if not user:
            return

        password_reset_token = await token_crud.create_password_reset_token(
            self._db, user.id
        )
        await self._db.commit()

        if self._email_sender:
            reset_link = (f""
                          f"{self._base_url}/auth/password-reset/complete?email="
                          f"{email}&token={password_reset_token.token}"
                          )
            await self._email_sender.send_password_reset_email(email, reset_link)

    async def reset_password(
        self,
        user_id: int,
        new_password: str,
    ) -> None:
        """
        Reset user password by user ID.

        This method is intended for internal/admin usage where password
        can be reset without old password verification.

        Args:
            user_id (int): User ID.
            new_password (str): New password to set.

        Raises:
            HTTPException: If user is not found.
        """
        # Fetch user from database
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate password rules
        user.set_password(new_password)

        # Remove used password reset tokens
        await self._db.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.user_id == user_id
            )
        )
        await self._db.commit()
