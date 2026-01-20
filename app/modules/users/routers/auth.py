from fastapi import APIRouter, Depends, status, HTTPException

from app.config.dependencies import get_auth_service, get_current_user_id
from app.modules.users.schemas.token_schema import TokenRefreshResponseSchema, TokenRefreshRequestSchema, \
    TokenResendActivationRequestSchema
from app.modules.users.schemas.user_schema import UserLoginResponseSchema, UserLoginRequestSchema, MessageResponseSchema, UserRegistrationRequestSchema, UserActivationRequestSchema
from app.modules.users.schemas.password_schema import (
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema, ChangePasswordSchema,
)
from app.modules.users.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/login",
    response_model=UserLoginResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="User Login",
)
async def login(
    data: UserLoginRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login a user and return access + refresh tokens.
    """
    access_token, refresh_token = await auth_service.login(
        email=data.email,
        password=data.password,
    )
    return UserLoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
    )


@auth_router.post(
    "/register",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
)
async def register(
    data: UserRegistrationRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user and send activation email.
    """
    await auth_service.register_user(
        email=data.email,
        password=data.password,
    )
    return MessageResponseSchema(
        message="Registration successful. Please check your email to activate your account."
    )


@auth_router.post(
    "/refresh",
    response_model=TokenRefreshResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using refresh token",
)
async def refresh_token(
    data: TokenRefreshRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token using a valid refresh token.
    """
    new_access_token = await auth_service.refresh_access_token(data.refresh_token)
    return TokenRefreshResponseSchema(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=3600,
    )


@auth_router.post(
    "/logout",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Logout user from current device (delete refresh token)",
)
async def logout(
    data: TokenRefreshRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout(data.refresh_token)
    return MessageResponseSchema(message="Logged out successfully.")


@auth_router.post(
    "/logout-all",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Logout user from all devices (delete all refresh tokens)",
)
async def logout_all(
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout_all_current_user(user_id)
    return MessageResponseSchema(message="Logged out from all devices.")


@auth_router.post(
    "/activate",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Activate user account using activation token",
)
async def activate_account(
    data: UserActivationRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Activate a user account using the activation token from email.
    """
    await auth_service.activate_user(data.email, data.token)
    return MessageResponseSchema(
        message="Account activated successfully. You can now login."
    )


@auth_router.post(
    "/password-reset/request",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Request password reset email",
)
async def request_password_reset(
    data: PasswordResetRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.send_password_reset_email(data.email)
    return MessageResponseSchema(
        message="If you are registered, you will receive an email with instructions."
    )


@auth_router.post(
    "/password-reset/complete",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Complete password reset using token",
)
async def complete_password_reset(
    data: PasswordResetCompleteRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.reset_password_by_token(
        email=data.email,
        token=data.token,
        new_password=data.new_password,
    )
    return MessageResponseSchema(message="Password reset successfully.")


@auth_router.post("/resend-activation")
async def resend_activation(data: TokenResendActivationRequestSchema, auth_service: AuthService = Depends(get_auth_service)):
    await auth_service.resend_activation_token(data.email)
    return {"detail": "If your email exists, a new activation link has been sent."}


@auth_router.post("/change-password")
async def change_password(
        data: ChangePasswordSchema,
        auth_service: AuthService = Depends(get_auth_service),
        user_id: int = Depends(get_current_user_id),
):
    user = await auth_service._get_user_by_id(user_id)

    await auth_service.change_password(
        user=user,
        old_password=data.old_password,
        new_password=data.new_password,
    )

    return MessageResponseSchema(
        message="Password changed successfully."
    )
