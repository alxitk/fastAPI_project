import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.exceptions.exceptions import TokenExpiredError
from app.modules.users.crud import token as token_crud
from app.modules.users.models.enums import UserGroupEnum
from app.modules.users.models.token import ActivationTokenModel
from app.modules.users.models.user import User, UserGroupModel
from app.modules.users.services.user_service import UserService
from app.notifications.interfaces import EmailSenderInterface
from app.utils.interfaces import JWTAuthManagerInterface
from app.utils.security import pwd_context


class RegistrationService:
    """
    Authentication service.
    Contains business logic for authentication and token handling.
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

    async def register_user(self, email: str, password: str) -> User:
        """
        Register a new user with default USER group and inactive status.

        This method:
        - Checks email uniqueness.
        - Assigns the default USER group.
        - Hashes the password securely.
        - Creates an inactive user.
        - Generates and sends an activation email with a token (if email sender is configured).

        Args:
            email (str): User email address.
            password (str): Plain-text password provided by the user.

        Returns:
            User: Newly created user instance.

        Raises:
            HTTPException: If user already exists or default group is missing.
        """
        user_stmt = select(User).where(User.email == email)
        result = await self._db.execute(user_stmt)
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")

        group_stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
        result = await self._db.execute(group_stmt)
        user_group = result.scalars().first()
        if not user_group:
            raise HTTPException(status_code=500, detail="Default user group not found")

        hashed_password = pwd_context.hash(password)
        new_user = User(
            email=email,
            _hashed_password=hashed_password,
            is_active=False,
            group_id=user_group.id,
        )

        self._db.add(new_user)
        await self._db.commit()
        await self._db.refresh(new_user)

        if self._email_sender:
            activation_token = await token_crud.create_activation_token(
                self._db, new_user.id
            )
            await self._db.commit()
            activation_link = f"{self._base_url}/auth/activate?email={email}&token={activation_token.token}"
            await self._email_sender.send_activation_email(email, activation_link)

        return new_user

    async def activate_user(self, email: str, token: str) -> None:
        """
        Activate a user account using an activation token.

        This method validates:
        - User existence.
        - Token validity and ownership.
        - Token expiration time.

        After successful validation:
        - Marks the user as active.
        - Deletes the activation token.
        - Sends a confirmation email (if email sender is configured).

        Args:
            email (str): User email address.
            token (str): Activation token received via email.

        Returns:
            None

        Raises:
            HTTPException: If user or token is invalid.
            TokenExpiredError: If activation token has expired.
        """
        user = await self._user_service._get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        activation_token = await token_crud.get_by_token(self._db, token)
        if not activation_token:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        if activation_token.user_id != user.id:
            raise HTTPException(status_code=400, detail="Token does not match user")

        if activation_token.expires_at < datetime.now(timezone.utc):
            raise TokenExpiredError

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

    async def resend_activation_token(self, email: str) -> None:
        """
        Resend account activation token to the user's email.

        This method is used when a user did not activate their account
        within the token expiration time (24 hours). If a valid activation
        token still exists, it will be reused. Otherwise, a new token is
        generated and sent.

        The method is idempotent:
        - If the user does not exist → silently returns.
        - If the user is already active → silently returns.

        Args:
            email (str): User email address.

        Returns:
            None
        """
        user = await self._user_service._get_user_by_email(email)

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

        activation_link = f"{self._base_url}/auth/activate?email={email}&token={token}"

        if self._email_sender:
            await self._email_sender.send_activation_email(email, activation_link)
