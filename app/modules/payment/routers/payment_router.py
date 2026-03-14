from datetime import datetime
from typing import Optional

import stripe
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_user
from app.config.email_dependencies import get_email_sender
from app.config.settings import BaseAppSettings
from app.config.settings_dependency import get_settings
from app.database.session import get_db
from app.modules.payment.models.payment_enum import PaymentStatusEnum
from app.modules.payment.services.payment_service import PaymentService
from app.modules.users.models.user import User
from app.notifications.email_sender import EmailSender

payment_router = APIRouter(prefix="/payments", tags=["payments"])


@payment_router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
    settings: BaseAppSettings = Depends(get_settings),
):
    """
    Stripe webhook endpoint.
    Receives events from Stripe and updates payment status.
    Must be defined before /{order_id} to avoid route conflict.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    try:
        await PaymentService.handle_webhook(
            db=db,
            event=event,
            background_tasks=background_tasks,
            email_sender=email_sender,
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )

    return {"status": "ok"}


@payment_router.post("/{order_id}", status_code=status.HTTP_201_CREATED)
async def create_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: BaseAppSettings = Depends(get_settings),
):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        payment = await PaymentService.create_payment(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
        )
        external_id = await PaymentService.create_stripe_payment_intent(
            db=db,
            payment=payment,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "payment_id": payment.id,
        "amount": payment.amount,
        "status": payment.status,
        "external_payment_id": external_id,
    }


@payment_router.get("/my")
async def get_my_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payment_status: Optional[PaymentStatusEnum] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    payments = await PaymentService.get_user_payments(
        db=db,
        user_id=current_user.id,
        status=payment_status,
        date_from=date_from,
        date_to=date_to,
    )
    return {"items": payments, "total": len(payments)}
