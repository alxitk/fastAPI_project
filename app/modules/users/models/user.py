from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime, func, ForeignKey, Date, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.modules.users.models.enums import UserGroupEnum, GenderEnum


class UserGroupModel(Base):
    __tablename__ = 'user_groups'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[UserGroupEnum] = mapped_column(Enum(UserGroupEnum), nullable=False, unique=True)

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="group",
        lazy="selectin",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[String] = mapped_column(String(255), unique=True, nullable=False, index=True)
    _hashed_password: Mapped[String] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    group: Mapped["UserGroupModel"] = relationship("UserGroupModel", back_populates="users")


    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False)

    activation_tokens: Mapped[list["ActivationTokenModel"]] = relationship(
        "ActivationTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    password_reset_token: Mapped[list["PasswordResetTokenModel"]] = relationship(
        "PasswordResetTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    #
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    profile: Mapped[Optional["UserProfileModel"]] = relationship(
        "UserProfileModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined"
    )


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    info: Mapped[Optional[str]] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="profile",
        uselist=False,
        lazy="joined"
    )

    __table_args__ = (UniqueConstraint("user_id"),)
