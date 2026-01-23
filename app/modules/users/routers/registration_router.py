from fastapi import APIRouter, Depends, status

from app.config.dependencies import get_registration_service, get_user_service, get_current_admin_user
from app.modules.users.schemas.user_schema import (
    UserRegistrationRequestSchema,
    UserActivationRequestSchema,
    MessageResponseSchema,
)
from app.modules.users.schemas.token_schema import TokenResendActivationRequestSchema
from app.modules.users.services.registration_service import RegistrationService
from app.modules.users.services.user_service import UserService

reg_router = APIRouter(prefix="/auth", tags=["Registration"])


@reg_router.post("/register", response_model=MessageResponseSchema)
async def register(
    data: UserRegistrationRequestSchema,
    registration_service: RegistrationService = Depends(get_registration_service),
):
    await registration_service.register_user(
        email=data.email,
        password=data.password,
    )
    return MessageResponseSchema(
        message="Registration successful. Please check your email."
    )


@reg_router.post("/activate", response_model=MessageResponseSchema)
async def activate(
    data: UserActivationRequestSchema,
    registration_service: RegistrationService = Depends(get_registration_service),
):
    await registration_service.activate_user(data.email, data.token)
    return MessageResponseSchema(message="Account activated successfully.")


@reg_router.post("/resend-activation", response_model=MessageResponseSchema)
async def resend_activation(
    data: TokenResendActivationRequestSchema,
    registration_service: RegistrationService = Depends(get_registration_service),
):
    await registration_service.resend_activation_token(data.email)
    return MessageResponseSchema(
        message="If your email exists, a new activation link has been sent."
    )


@reg_router.post("/{user_id}/activate", response_model=MessageResponseSchema,)
async def admin_activate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    admin=Depends(get_current_admin_user),
):
    await user_service.activate_user_by_admin(user_id)
    return MessageResponseSchema(
        message="User activated successfully by admin."
    )



@reg_router.post(
    "/{user_id}/change-group",
    response_model=MessageResponseSchema,
)
async def admin_change_user_group(
    user_id: int,
    group_id: int,
    user_service: UserService = Depends(get_user_service),
    admin=Depends(get_current_admin_user),
):
    await user_service.change_user_group(
        user_id=user_id,
        group_id=group_id,
    )
    return MessageResponseSchema(
        message="User group updated successfully."
    )
