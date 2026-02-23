from __future__ import annotations
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
if TYPE_CHECKING:
    from app.modules.users.models.user import User


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    cart: Mapped["Cart"] = relationship(
        "Cart",
        back_populates="items",
    )
    cart_id: Mapped[int] = mapped_column(
        ForeignKey(
            "carts.id", ondelete="CASCADE", onupdate="CASCADE"
        ), nullable=False
    )
    movie = relationship(
        "Movie",
        back_populates="cart_items",
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="uq_cart_movie"),
    )


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="cart",
        uselist=False,
    )
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
    )