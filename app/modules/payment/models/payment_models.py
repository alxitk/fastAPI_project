from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import Integer, ForeignKey, DateTime, func, Numeric, String, Index
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column

from app.database.base import Base
from app.modules.payment.models.payment_enum import PaymentStatusEnum
from sqlalchemy import Enum as SAEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.order.models.order_models import OrderItem, Order
    from app.modules.users.models.user import User


class PaymentItem(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    payment: Mapped["Payment"] = relationship(
        "Payment",
        back_populates="payment_items",
    )
    payment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "payments.id",
            ondelete="CASCADE",
            onupdate="RESTRICT",
        ),
        nullable=False,
    )
    order_item: Mapped["OrderItem"] = relationship(
        "OrderItem",
        back_populates="payment_items",
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "order_items.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    price_at_payment: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="payments",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="payments",
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[PaymentStatusEnum] = mapped_column(
        SAEnum(PaymentStatusEnum, name="payment_status_enum", native_enum=False),
        nullable=False,
        default=PaymentStatusEnum.PENDING,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    payment_items: Mapped[List[PaymentItem]] = relationship(
        "PaymentItem",
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    external_payment_id: Mapped[str] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index("ix_payments_user_id", "user_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_created_at", "created_at"),
    )
