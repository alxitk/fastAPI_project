from pydantic import BaseModel, EmailStr, field_validator

from app.utils.security import validate_strong_password


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = {"extra": "forbid"}

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)


class UserRegistrationRequestSchema(BaseEmailPasswordSchema): ...


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}


class UserActivationRequestSchema(BaseModel):
    email: EmailStr
    token: str

    model_config = {"extra": "forbid"}


class UserLoginRequestSchema(BaseEmailPasswordSchema):
    pass


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    model_config = {"extra": "forbid"}


class MessageResponseSchema(BaseModel):
    message: str
