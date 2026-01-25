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


@password_router.post("/password-reset/request", response_model=MessageResponseSchema)
async def request_reset(
    data: PasswordResetRequestSchema,
    service: PasswordService = Depends(get_password_service),
):
    await service.send_password_reset_email(data.email)
    return MessageResponseSchema(
        message="If you are registered, you will receive an email."
    )


@password_router.post("/password-reset/complete", response_model=MessageResponseSchema)
async def complete_reset(
    data: PasswordResetCompleteRequestSchema,
    service: PasswordService = Depends(get_password_service),
):
    await service.reset_password_by_token(
        data.email,
        data.token,
        data.new_password,
    )
    return MessageResponseSchema(message="Password reset successfully.")


@password_router.post("/change-password", response_model=MessageResponseSchema)
async def change_password(
    data: ChangePasswordSchema,
    user_id: int = Depends(get_current_user_id),
    service: PasswordService = Depends(get_password_service),
):
    await service.change_password(
        user_id=user_id,
        old_password=data.old_password,
        new_password=data.new_password,
    )
    return MessageResponseSchema(message="Password changed successfully.")
