from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import BaseAppSettings
from app.config.settings_dependency import get_settings
from app.database.session import get_db
from app.exceptions.exceptions import InvalidTokenError, TokenExpiredError
from app.modules.users.models.user import User
from app.modules.users.services.auth_service import AuthService
from app.modules.users.services.password_service import PasswordService
from app.modules.users.services.registration_service import RegistrationService
from app.modules.users.services.user_service import UserService
from app.notifications.email_sender import EmailSender
from app.notifications.interfaces import EmailSenderInterface
from app.utils.interfaces import JWTAuthManagerInterface
from app.utils.token_manager import JWTAuthManager

security = HTTPBearer()


def get_jwt_auth_manager(settings: BaseAppSettings = Depends(get_settings)) -> JWTAuthManagerInterface:
    """
    Create and return a JWT authentication manager instance.
    """
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM
    )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> int:
    """
    Get current user ID from JWT access token.
    """
    try:
        payload = jwt_manager.decode_access_token(credentials.credentials)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        return user_id
    except (TokenExpiredError, InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current user from database.
    """
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_email_sender() -> EmailSenderInterface:
    return EmailSender(
        hostname="mailhog",
        port=1025,
        email="noreply@example.com",
        password="",
        use_tls=False,
        template_dir="app/templates/emails",
        activation_email_template_name="activation_request.html",
        activation_complete_email_template_name="activation_complete.html",
        password_email_template_name="password_reset_request.html",
        password_complete_email_template_name="password_reset_complete.html",
    )


def get_user_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    settings = Depends(get_settings),
) -> UserService:
    return UserService(
        db=db,
        jwt_manager=jwt_manager,
        login_time_days=settings.LOGIN_TIME_DAYS,
    )


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    login_time_days: int = Depends(lambda settings=Depends(get_settings): settings.LOGIN_TIME_DAYS),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(
        db=db,
        jwt_manager=jwt_manager,
        login_time_days=login_time_days,
        user_service=user_service,
        email_sender=get_email_sender(),
        base_url="http://localhost:8000",
    )


def get_registration_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    login_time_days: int = Depends(lambda settings=Depends(get_settings): settings.LOGIN_TIME_DAYS),
    user_service: UserService = Depends(get_user_service),
) -> RegistrationService:
    return RegistrationService(
        db=db,
        jwt_manager=jwt_manager,
        login_time_days=login_time_days,
        user_service=user_service,
        email_sender=get_email_sender(),
        base_url="http://localhost:8000",
    )


def get_password_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager = Depends(get_jwt_auth_manager),
    user_service: UserService = Depends(get_user_service),
    login_time_days: int = Depends(lambda settings=Depends(get_settings): settings.LOGIN_TIME_DAYS),
    settings = Depends(get_settings),
) -> PasswordService:
    return PasswordService(
        db=db,
        jwt_manager=jwt_manager,
        user_service=user_service,
        login_time_days=login_time_days,
        email_sender=get_email_sender(),
        base_url=settings.BASE_URL,
    )


def get_current_admin_user(
    user=Depends(get_current_user),
):
    if user.group_id != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
