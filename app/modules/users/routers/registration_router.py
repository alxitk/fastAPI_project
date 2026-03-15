from fastapi import APIRouter, Depends

from app.config.dependencies import (
    get_registration_service,
    get_user_service,
    get_current_admin_user,
)
from app.modules.users.models.user import User
from app.modules.users.schemas.user_schema import (
    UserRegistrationRequestSchema,
    UserActivationRequestSchema,
    MessageResponseSchema,
)
from app.modules.users.schemas.token_schema import TokenResendActivationRequestSchema
from app.modules.users.services.registration_service import RegistrationService
from app.modules.users.services.user_service import UserService

reg_router = APIRouter(prefix="/auth", tags=["Registration"])


@reg_router.post(
    "/register",
    response_model=MessageResponseSchema,
    summary="Register a new user account",
    description=(
        "Create a new user account with **email** and **password**.\n\n"
        "Password requirements:\n"
        "- Minimum 8 characters\n"
        "- At least one uppercase letter\n"
        "- At least one digit\n"
        "- At least one special character\n\n"
        "After registration a **confirmation email** is sent to the provided address. "
        "The activation link expires after **24 hours**. "
        "The account cannot be used until activated."
    ),
    responses={
        200: {"description": "Registration successful, activation email sent."},
        400: {
            "description": "Email already registered or password too weak.",
            "content": {
                "application/json": {
                    "example": {"detail": "User with this email already exists."}
                }
            },
        },
    },
)
async def register(
    data: UserRegistrationRequestSchema,
    registration_service: RegistrationService = Depends(get_registration_service),
) -> MessageResponseSchema:
    await registration_service.register_user(
        email=data.email,
        password=data.password,
    )
    return MessageResponseSchema(
        message="Registration successful. Please check your email."
    )


@reg_router.post(
    "/activate",
    response_model=MessageResponseSchema,
    summary="Activate user account via email token",
    description=(
        "Activate a registered account using the **email** and the **activation token** "
        "received in the confirmation email.\n\n"
        "The token is valid for **24 hours** after registration. "
        "Use `POST /auth/resend-activation` to request a new token if it has expired."
    ),
    responses={
        200: {"description": "Account activated successfully."},
        400: {
            "description": "Invalid or expired activation token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired activation token."}
                }
            },
        },
    },
)
async def activate(
    data: UserActivationRequestSchema,
    registration_service: RegistrationService = Depends(get_registration_service),
) -> MessageResponseSchema:
    await registration_service.activate_user(data.email, data.token)
    return MessageResponseSchema(message="Account activated successfully.")


@reg_router.post(
    "/resend-activation",
    response_model=MessageResponseSchema,
    summary="Resend account activation email",
    description=(
        "Request a new activation email for an **unactivated** account.\n\n"
        "For security reasons the response is identical regardless of whether "
        "the email address exists in the system."
    ),
    responses={
        200: {"description": "Activation email sent (if the address is registered)."},
    },
)
async def resend_activation(
    data: TokenResendActivationRequestSchema,
    registration_service: RegistrationService = Depends(get_registration_service),
) -> MessageResponseSchema:
    await registration_service.resend_activation_token(data.email)
    return MessageResponseSchema(
        message="If your email exists, a new activation link has been sent."
    )


@reg_router.post(
    "/{user_id}/activate",
    response_model=MessageResponseSchema,
    summary="[Admin] Manually activate a user account",
    description=(
        "Allows an **admin** to activate any user account without requiring the user "
        "to click the email link.\n\n"
        "Useful for support scenarios or bulk onboarding.\n\n"
        "> Requires **Admin** role (`group_id = 3`)."
    ),
    responses={
        200: {"description": "User activated by admin."},
        403: {
            "description": "Caller does not have admin privileges.",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
        },
        404: {
            "description": "User not found.",
            "content": {
                "application/json": {"example": {"detail": "User not found"}}
            },
        },
    },
)
async def admin_activate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    admin: User = Depends(get_current_admin_user),
) -> MessageResponseSchema:
    await user_service.activate_user_by_admin(user_id)
    return MessageResponseSchema(message="User activated successfully by admin.")


@reg_router.post(
    "/{user_id}/change-group",
    response_model=MessageResponseSchema,
    summary="[Admin] Change user role / group",
    description=(
        "Update the **role group** of any user.\n\n"
        "Available groups:\n"
        "| group_id | Role |\n"
        "|----------|----------|\n"
        "| 1 | USER |\n"
        "| 2 | MODERATOR |\n"
        "| 3 | ADMIN |\n\n"
        "> Requires **Admin** role (`group_id = 3`)."
    ),
    responses={
        200: {"description": "User group updated."},
        403: {
            "description": "Caller does not have admin privileges.",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
        },
        404: {
            "description": "User or group not found.",
            "content": {
                "application/json": {"example": {"detail": "User not found"}}
            },
        },
    },
)
async def admin_change_user_group(
    user_id: int,
    group_id: int,
    user_service: UserService = Depends(get_user_service),
    admin: User = Depends(get_current_admin_user),
) -> MessageResponseSchema:
    await user_service.change_user_group(
        user_id=user_id,
        group_id=group_id,
    )
    return MessageResponseSchema(message="User group updated successfully.")
