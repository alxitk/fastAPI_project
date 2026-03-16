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


@payment_router.post(
    "/{order_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Create a Stripe payment intent for an order",
    description=(
        "Initiate a **Stripe payment intent** for the specified order.\n\n"
        "Steps:\n"
        "1. Call `POST /orders/` to create an order from your cart.\n"
        "2. Call this endpoint with the returned `order_id`.\n"
        "3. Use the returned `external_payment_id` (Stripe PaymentIntent ID) "
        "in your frontend with Stripe.js to complete payment.\n\n"
        "Stripe will send a webhook event to `POST /payments/webhook` once the "
        "payment is confirmed, which will automatically update the order status."
    ),
    responses={
        201: {
            "description": "Payment intent created.",
            "content": {
                "application/json": {
                    "example": {
                        "payment_id": 42,
                        "amount": 29.99,
                        "status": "pending",
                        "external_payment_id": "pi_3OxABC123",
                    }
                }
            },
        },
        400: {
            "description": "Order already paid or invalid state.",
            "content": {
                "application/json": {"example": {"detail": "Order is already paid."}}
            },
        },
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        404: {
            "description": "Order not found.",
            "content": {
                "application/json": {"example": {"detail": "Order not found."}}
            },
        },
    },
)
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


@payment_router.get(
    "/my",
    summary="List the current user's payments",
    description=(
        "Retrieve all payments made by the authenticated user.\n\n"
        "Optional query filters:\n"
        "- `payment_status` — filter by status (`pending`, `succeeded`, `failed`, `refunded`)\n"
        "- `date_from` / `date_to` — filter by creation date range (ISO 8601 format)\n\n"
        "Returns a list of payment objects and the total count."
    ),
    responses={
        200: {
            "description": "Payment list returned.",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "order_id": 5,
                                "amount": 14.99,
                                "status": "succeeded",
                                "created_at": "2024-01-15T10:30:00Z",
                            }
                        ],
                        "total": 1,
                    }
                }
            },
        },
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
    },
)
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
