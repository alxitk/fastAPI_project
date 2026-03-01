from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import Integer, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.database.base import Base
from app.modules.order.models.enum import OrderStatusEnum


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int]= mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="orders",
    )
    user_id: Mapped[int]= mapped_column(
        ForeignKey(
            "users.id", ondelete="CASCADE", onupdate="CASCADE"
        ), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[OrderStatusEnum] = mapped_column(
        SAEnum(OrderStatusEnum, name="order_status_enum", native_enum=False),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    order_items:Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="order_items",
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id", ondelete="CASCADE", onupdate="CASCADE"
        ), nullable=False
    )
    movie: Mapped["Movie"] = relationship(
        "Movie",
        back_populates="order_items",
    )
    movie_id: Mapped[int]= mapped_column(
        ForeignKey(
            "movies.id", ondelete="RESTRICT", onupdate="CASCADE"
        ), nullable=False
    )
    price_at_order: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )