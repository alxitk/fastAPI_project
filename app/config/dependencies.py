from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.email_dependencies import get_email_sender
from app.config.settings import BaseAppSettings
from app.config.settings_dependency import get_settings
from app.database.session import get_db
from app.exceptions.exceptions import InvalidTokenError, TokenExpiredError
from app.modules.movies.services.movie_service import MovieService
from app.modules.users.models.user import User
from app.modules.users.services.auth_service import AuthService
from app.modules.users.services.password_service import PasswordService
from app.modules.users.services.registration_service import RegistrationService
from app.modules.users.services.user_service import UserService
from app.utils.interfaces import JWTAuthManagerInterface
from app.utils.token_manager import JWTAuthManager

security = HTTPBearer()


def get_jwt_auth_manager(
    settings: BaseAppSettings = Depends(get_settings),
) -> JWTAuthManagerInterface:
    """
    Return a configured JWT authentication manager.
    """
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> int:
    """
    Extract and return the current user ID from the access token.
    """
    try:
        payload = jwt_manager.decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not isinstance(user_id, int):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
        return user_id
    except (TokenExpiredError, InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Load and return the current user from the database.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_current_moderator_user(user: User = Depends(get_current_user)) -> User:
    """
    Ensure the current user has moderator privileges.
    """
    if user.group_id != 2:
        raise HTTPException(status_code=403, detail="Moderator access required")
    return user


def get_user_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    settings: BaseAppSettings = Depends(get_settings),
) -> UserService:
    """
    Provides a UserService instance.
    """
    return UserService(
        db=db,
        jwt_manager=jwt_manager,
        login_time_days=settings.LOGIN_TIME_DAYS,
    )


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    login_time_days: int = Depends(
        lambda settings=Depends(get_settings): settings.LOGIN_TIME_DAYS
    ),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    """
    Provides an AuthService instance.
    """
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
    login_time_days: int = Depends(
        lambda settings=Depends(get_settings): settings.LOGIN_TIME_DAYS
    ),
    user_service: UserService = Depends(get_user_service),
) -> RegistrationService:
    """
    Provides a RegistrationService instance.
    """
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
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    user_service: UserService = Depends(get_user_service),
    login_time_days: int = Depends(
        lambda settings=Depends(get_settings): settings.LOGIN_TIME_DAYS
    ),
    settings: BaseAppSettings = Depends(get_settings),
) -> PasswordService:
    """
    Provides a PasswordService instance.
    """
    return PasswordService(
        db=db,
        jwt_manager=jwt_manager,
        user_service=user_service,
        login_time_days=login_time_days,
        email_sender=get_email_sender(),
        base_url=settings.BASE_URL,
    )


def get_current_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the current user has admin privileges.
    """
    if user.group_id != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def get_movie_service(
    db: AsyncSession = Depends(get_db),
) -> MovieService:
    """
    Provide a MovieService instance with an injected database session.
    """
    return MovieService(db)
