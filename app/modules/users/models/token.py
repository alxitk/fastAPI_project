from datetime import datetime, timezone, timedelta

from sqlalchemy import Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base
from app.modules.users.models.user import User
from app.utils.tokens import generate_secure_token


class TokenBaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        default=generate_secure_token
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1)
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class ActivationTokenModel(TokenBaseModel):
    __tablename__ = "activation_tokens"

    user: Mapped[User] = relationship("User", back_populates="activation_tokens", lazy="selectin")


class PasswordResetTokenModel(TokenBaseModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped[User] = relationship("User", back_populates="password_reset_tokens", lazy="selectin")


class RefreshTokenModel(TokenBaseModel):
    __tablename__ = "refresh_tokens"

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens", lazy="selectin")
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        default=generate_secure_token
    )
