from fastapi import APIRouter, Depends

from app.config.dependencies import get_password_service, get_current_user_id
from app.modules.users.schemas.password_schema import (
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    ChangePasswordSchema,
)
from app.modules.users.schemas.user_schema import MessageResponseSchema
from app.modules.users.services.password_service import PasswordService

password_router = APIRouter(prefix="/auth", tags=["Password"])


@password_router.post(
    "/password-reset/request",
    response_model=MessageResponseSchema,
    summary="Request a password-reset email",
    description=(
        "Send a **password-reset email** to the given address.\n\n"
        "The email contains a one-time token valid for **1 hour**. "
        "Use it with `POST /auth/password-reset/complete` to set a new password.\n\n"
        "For security reasons the response is the same whether or not the "
        "email address exists in the system."
    ),
    responses={
        200: {"description": "Reset email sent (if the address is registered)."},
    },
)
async def request_reset(
    data: PasswordResetRequestSchema,
    service: PasswordService = Depends(get_password_service),
) -> MessageResponseSchema:
    await service.send_password_reset_email(data.email)
    return MessageResponseSchema(
        message="If you are registered, you will receive an email."
    )


@password_router.post(
    "/password-reset/complete",
    response_model=MessageResponseSchema,
    summary="Complete password reset using the emailed token",
    description=(
        "Set a new password using the **email** and the **reset token** "
        "received by email.\n\n"
        "The token expires after **1 hour**. "
        "Request a new one via `POST /auth/password-reset/request`.\n\n"
        "Password requirements:\n"
        "- Minimum 8 characters\n"
        "- At least one uppercase letter, one digit, one special character"
    ),
    responses={
        200: {"description": "Password reset successfully."},
        400: {
            "description": "Invalid or expired reset token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired reset token."}
                }
            },
        },
    },
)
async def complete_reset(
    data: PasswordResetCompleteRequestSchema,
    service: PasswordService = Depends(get_password_service),
) -> MessageResponseSchema:
    await service.reset_password_by_token(
        data.email,
        data.token,
        data.new_password,
    )
    return MessageResponseSchema(message="Password reset successfully.")


@password_router.post(
    "/change-password",
    response_model=MessageResponseSchema,
    summary="Change password (authenticated user)",
    description=(
        "Change the password for the currently authenticated user.\n\n"
        "Requires:\n"
        "- A valid **Bearer access token** in the `Authorization` header\n"
        "- The current `old_password`\n"
        "- The new `new_password` (must meet strength requirements)\n\n"
        "All active sessions remain valid after this call. "
        "Use `POST /auth/logout-all` to revoke them if needed."
    ),
    responses={
        200: {"description": "Password changed successfully."},
        400: {
            "description": "Old password is incorrect or new password is too weak.",
            "content": {
                "application/json": {
                    "example": {"detail": "Old password is incorrect."}
                }
            },
        },
        401: {
            "description": "Access token missing or invalid.",
            "content": {
                "application/json": {"example": {"detail": "Invalid or expired token"}}
            },
        },
    },
)
async def change_password(
    data: ChangePasswordSchema,
    user_id: int = Depends(get_current_user_id),
    service: PasswordService = Depends(get_password_service),
) -> MessageResponseSchema:
    await service.change_password(
        user_id=user_id,
        old_password=data.old_password,
        new_password=data.new_password,
    )
    return MessageResponseSchema(message="Password changed successfully.")
