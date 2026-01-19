from pydantic import BaseModel, EmailStr


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenResendActivationRequestSchema(BaseModel):
    email: EmailStr

    model_config = {"extra": "forbid"}