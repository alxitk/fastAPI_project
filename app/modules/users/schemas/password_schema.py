from pydantic import BaseModel, EmailStr, field_validator

from app.utils.security import validate_strong_password


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr

    model_config = {"extra": "forbid"}


class PasswordResetCompleteRequestSchema(BaseModel):
    email: EmailStr
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):
        return validate_strong_password(value)

    model_config = {"extra": "forbid"}
