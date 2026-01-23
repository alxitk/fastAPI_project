from fastapi import APIRouter, Depends, status

from app.config.dependencies import get_auth_service, get_current_user_id
from app.modules.users.schemas.token_schema import (
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
)
from app.modules.users.schemas.user_schema import (
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    MessageResponseSchema,
)
from app.modules.users.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login", response_model=UserLoginResponseSchema)
async def login(
    data: UserLoginRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    access, refresh = await auth_service.login(data.email, data.password)
    return UserLoginResponseSchema(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=3600,
    )


@auth_router.post("/refresh", response_model=TokenRefreshResponseSchema)
async def refresh_token(
    data: TokenRefreshRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    access = await auth_service.refresh_access_token(data.refresh_token)
    return TokenRefreshResponseSchema(
        access_token=access,
        token_type="bearer",
        expires_in=3600,
    )


@auth_router.post("/logout", response_model=MessageResponseSchema)
async def logout(
    data: TokenRefreshRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout(data.refresh_token)
    return MessageResponseSchema(message="Logged out successfully.")


@auth_router.post("/logout-all", response_model=MessageResponseSchema)
async def logout_all(
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout_all_current_user(user_id)
    return MessageResponseSchema(message="Logged out from all devices.")
