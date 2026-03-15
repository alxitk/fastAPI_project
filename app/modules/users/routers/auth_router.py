from fastapi import APIRouter, Depends

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


@auth_router.post(
    "/login",
    response_model=UserLoginResponseSchema,
    summary="Log in and obtain JWT tokens",
    description=(
        "Authenticate with **email** and **password**.\n\n"
        "On success returns an **access token** (valid 1 hour) and a "
        "**refresh token** (valid 7 days).\n\n"
        "Pass the access token in subsequent requests as:\n"
        "```\nAuthorization: Bearer <access_token>\n```"
    ),
    responses={
        200: {"description": "Tokens issued successfully."},
        401: {
            "description": "Invalid credentials.",
            "content": {
                "application/json": {"example": {"detail": "Invalid credentials."}}
            },
        },
    },
)
async def login(
    data: UserLoginRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserLoginResponseSchema:
    access, refresh = await auth_service.login(data.email, data.password)
    return UserLoginResponseSchema(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=3600,
    )


@auth_router.post(
    "/refresh",
    response_model=TokenRefreshResponseSchema,
    summary="Refresh the access token",
    description=(
        "Exchange a valid **refresh token** for a new **access token**.\n\n"
        "The refresh token itself is **not** rotated — the same refresh token "
        "remains valid until it expires or is revoked via logout."
    ),
    responses={
        200: {"description": "New access token issued."},
        401: {
            "description": "Refresh token is invalid or expired.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired refresh token."}
                }
            },
        },
    },
)
async def refresh_token(
    data: TokenRefreshRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenRefreshResponseSchema:
    access = await auth_service.refresh_access_token(data.refresh_token)
    return TokenRefreshResponseSchema(
        access_token=access,
        token_type="bearer",
        expires_in=3600,
    )


@auth_router.post(
    "/logout",
    response_model=MessageResponseSchema,
    summary="Log out from the current device",
    description=(
        "Revoke the supplied **refresh token**, invalidating the current session.\n\n"
        "The access token remains technically valid until it expires (≤ 1 hour), "
        "but the refresh token can no longer be used to obtain new access tokens."
    ),
    responses={
        200: {"description": "Logged out successfully."},
        401: {
            "description": "Refresh token is invalid.",
            "content": {
                "application/json": {"example": {"detail": "Invalid token."}}
            },
        },
    },
)
async def logout(
    data: TokenRefreshRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponseSchema:
    await auth_service.logout(data.refresh_token)
    return MessageResponseSchema(message="Logged out successfully.")


@auth_router.post(
    "/logout-all",
    response_model=MessageResponseSchema,
    summary="Log out from all devices",
    description=(
        "Revoke **all active refresh tokens** for the currently authenticated user, "
        "terminating every active session across all devices.\n\n"
        "Requires a valid **Bearer access token** in the `Authorization` header."
    ),
    responses={
        200: {"description": "Logged out from all devices."},
        401: {
            "description": "Access token missing or invalid.",
            "content": {
                "application/json": {"example": {"detail": "Invalid or expired token"}}
            },
        },
    },
)
async def logout_all(
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponseSchema:
    await auth_service.logout_all_current_user(user_id)
    return MessageResponseSchema(message="Logged out from all devices.")