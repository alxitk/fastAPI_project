import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional

import stripe
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.payment.models.payment_models import Payment, PaymentItem
from app.modules.payment.models.payment_enum import PaymentStatusEnum
from app.modules.order.models.order_models import Order, OrderItem
from app.modules.order.models.enum import OrderStatusEnum
from app.notifications.email_sender import EmailSender

# Statuses from which payment is allowed
PAYABLE_ORDER_STATUSES = {OrderStatusEnum.PENDING}

# Terminal payment statuses — webhook must not overwrite these
TERMINAL_PAYMENT_STATUSES = {
    PaymentStatusEnum.SUCCESS,
    PaymentStatusEnum.RETURNED,
}


class PaymentService:

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        user_id: int,
        order_id: int,
    ) -> Payment:
        # Lock order row to prevent race condition
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError("Order not found")

        if order.user_id != user_id:
            raise ValueError("Order does not belong to user")

        # Check order status allows payment
        if order.status not in PAYABLE_ORDER_STATUSES:
            raise ValueError(
                f"Order cannot be paid in status '{order.status.value}'"
            )

        # Check for existing pending payment (with lock to prevent race condition)
        existing_result = await db.execute(
            select(Payment)
            .where(
                Payment.order_id == order_id,
                Payment.status == PaymentStatusEnum.PENDING,
            )
            .with_for_update()
        )
        if existing_result.scalars().first():
            raise ValueError("Payment already pending for this order")

        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        order_items = items_result.scalars().all()

        if not order_items:
            raise ValueError("Order has no items")

        total_amount = sum(item.price_at_order for item in order_items)

        payment = Payment(
            user_id=user_id,
            order_id=order_id,
            amount=Decimal(total_amount),
            status=PaymentStatusEnum.PENDING,
        )

        db.add(payment)
        await db.flush()

        payment_items = [
            PaymentItem(
                payment_id=payment.id,
                order_item_id=item.id,
                price_at_payment=item.price_at_order,
            )
            for item in order_items
        ]

        db.add_all(payment_items)
        await db.flush()

        return payment

    @staticmethod
    async def create_stripe_payment_intent(
        db: AsyncSession,
        payment: Payment,
    ) -> str:
        """
        Creates a real Stripe PaymentIntent and stores external_payment_id.
        Requires stripe.api_key to be set in app config before calling.
        Uses asyncio.to_thread to avoid blocking the event loop.
        Uses Decimal arithmetic to avoid float precision issues.
        """
        amount_cents = int(payment.amount * Decimal("100"))

        intent = await asyncio.to_thread(
            stripe.PaymentIntent.create,
            amount=amount_cents,
            currency="usd",
            metadata={"payment_id": payment.id, "order_id": payment.order_id},
        )

        payment.external_payment_id = intent["id"]
        db.add(payment)
        await db.flush()

        return intent["id"]

    @staticmethod
    async def handle_webhook(
        db: AsyncSession,
        event: dict,
        background_tasks: BackgroundTasks,
        email_sender: EmailSender,
    ) -> None:
        """
        Handles Stripe webhook events and updates payment and order statuses.
        - Looks up Payment by metadata.payment_id as recommended by Stripe.
        - Idempotent: skips update if payment is already in a terminal status.
        - Email is sent via BackgroundTasks to avoid blocking webhook response.
        - Safely handles missing metadata.
        """
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        # Safely extract payment_id from metadata
        metadata = data.get("metadata") or {}
        raw_payment_id = metadata.get("payment_id")

        if not raw_payment_id:
            return

        try:
            payment_id = int(raw_payment_id)
        except (ValueError, TypeError):
            return

        result = await db.execute(
            select(Payment)
            .where(Payment.id == payment_id)
            .options(selectinload(Payment.user))
        )
        payment = result.scalar_one_or_none()

        if not payment:
            return

        # Idempotency: skip if already in terminal status
        if payment.status in TERMINAL_PAYMENT_STATUSES:
            return

        if event_type == "payment_intent.succeeded":
            payment.status = PaymentStatusEnum.SUCCESS

            order = await db.get(Order, payment.order_id)
            if order:
                order.status = OrderStatusEnum.PAID
                db.add(order)

            if payment.user and payment.user.email:
                html_content = (
                    f"<p>Your payment of <b>${payment.amount}</b> "
                    f"for order #{payment.order_id} was successful.</p>"
                    f"<p>Payment ID: {payment.id}</p>"
                    f"<p>Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}</p>"
                )
                background_tasks.add_task(
                    email_sender.send_email,
                    recipient=payment.user.email,
                    subject="Payment Confirmation",
                    html_content=html_content,
                )

        elif event_type == "payment_intent.payment_failed":
            payment.status = PaymentStatusEnum.CANCELLED

            if payment.user and payment.user.email:
                html_content = (
                    f"<p>Your payment of <b>${payment.amount}</b> "
                    f"for order #{payment.order_id} was declined.</p>"
                    f"<p>Please try a different payment method.</p>"
                )
                background_tasks.add_task(
                    email_sender.send_email,
                    recipient=payment.user.email,
                    subject="Payment Failed",
                    html_content=html_content,
                )

        elif event_type == "charge.refunded":
            payment.status = PaymentStatusEnum.RETURNED

        db.add(payment)
        await db.flush()

    @staticmethod
    async def get_user_payments(
        db: AsyncSession,
        user_id: int,
        status: Optional[PaymentStatusEnum] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> list[Payment]:
        """
        Returns payment history for a user with optional filters.
        Includes payment_items for detailed view.
        """
        query = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .options(selectinload(Payment.payment_items))
            .order_by(Payment.created_at.desc())
        )

        if status is not None:
            query = query.where(Payment.status == status)

        if date_from is not None:
            query = query.where(Payment.created_at >= date_from)

        if date_to is not None:
            query = query.where(Payment.created_at <= date_to)

        result = await db.execute(query)
        return result.scalars().all()


class AdminPaymentService:

    @staticmethod
    async def get_all_payments(
        db: AsyncSession,
        user_id: Optional[int] = None,
        status: Optional[PaymentStatusEnum] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> list[Payment]:
        """
        Returns all payments with optional filters by user, status, and date.
        For admin use only.
        """
        query = (
            select(Payment)
            .options(selectinload(Payment.payment_items))
            .order_by(Payment.created_at.desc())
        )

        if user_id is not None:
            query = query.where(Payment.user_id == user_id)

        if status is not None:
            query = query.where(Payment.status == status)

        if date_from is not None:
            query = query.where(Payment.created_at >= date_from)

        if date_to is not None:
            query = query.where(Payment.created_at <= date_to)

        result = await db.execute(query)
        return result.scalars().all()
