from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import BaseAppSettings
from app.config.settings_dependency import get_settings
from app.database.session import get_db
from app.modules.users.services.auth_service import AuthService
from app.utils.interfaces import JWTAuthManagerInterface
from app.utils.token_manager import JWTAuthManager


def get_jwt_auth_manager(settings: BaseAppSettings = Depends(get_settings)) -> JWTAuthManagerInterface:
    """
    Create and return a JWT authentication manager instance.
    """
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM
    )


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    login_time_days: int = Depends(lambda settings=Depends(get_settings): settings.LOGIN_TIME_DAYS),
) -> AuthService:
    return AuthService(
        db=db,
        jwt_manager=jwt_manager,
        login_time_days=login_time_days,
    )
