from datetime import datetime, date
from typing import Optional
from sqlalchemy import Enum as SAEnum

from sqlalchemy import Integer, String, Boolean, DateTime, func, ForeignKey, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.modules.users.models.enums import UserGroupEnum, GenderEnum


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[UserGroupEnum] = mapped_column(
        SAEnum(UserGroupEnum, name="user_group_enum", native_enum=False),
        nullable=False,
        unique=True,
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="group",
        lazy="selectin",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    _hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False
    )

    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )

    activation_tokens: Mapped[list["ActivationTokenModel"]] = relationship(
        "ActivationTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    password_reset_tokens: Mapped[list["PasswordResetTokenModel"]] = (
        relationship(  # ← исправлено
            "PasswordResetTokenModel",
            back_populates="user",
            cascade="all, delete-orphan",
        )
    )

    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    profile: Mapped[Optional["UserProfileModel"]] = relationship(
        "UserProfileModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

    likes = relationship("MovieLike", back_populates="user")
    favorites = relationship("MovieFavorites", back_populates="user")
    movie_comments = relationship(
        "MovieComment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def hashed_password(self) -> str:
        """Get hashed password."""
        return self._hashed_password

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        """Set hashed password directly (already hashed)."""
        self._hashed_password = value

    def set_password(self, raw_password: str) -> None:
        """Hash and set password."""
        from app.utils.security import hash_password

        self._hashed_password = hash_password(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        """Verify password against hash."""
        from app.utils.security import verify_password

        return verify_password(raw_password, self._hashed_password)


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[GenderEnum]] = mapped_column(
        SAEnum(GenderEnum, name="gender_enum", native_enum=False)
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    info: Mapped[Optional[str]] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="profile", uselist=False, lazy="joined"
    )
