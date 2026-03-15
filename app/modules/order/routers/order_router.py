from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_user
from app.database.session import get_db
from app.modules.order.schemas.order_schemas import (
    OrderCreateResponseSchema,
    OrderListResponseSchema,
    OrderResponseSchema,
    OrderCancelResponseSchema,
)
from app.modules.order.services.order_service import OrderService

order_router = APIRouter(prefix="/orders", tags=["Orders"])
service = OrderService()


@order_router.post(
    "/",
    response_model=OrderCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order from the cart",
    description=(
        "Convert the current user's cart into a new **order**.\n\n"
        "- All items from the cart are transferred to the order.\n"
        "- The cart is cleared after a successful order is created.\n"
        "- A **Stripe payment URL** is returned so the user can complete payment.\n\n"
        "After placing an order, complete payment via `POST /payments/{order_id}`."
    ),
    responses={
        201: {"description": "Order created, payment URL returned."},
        400: {
            "description": "Cart is empty or contains unavailable items.",
            "content": {"application/json": {"example": {"detail": "Cart is empty."}}},
        },
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
    },
)
async def create_order(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    order, payment_url = await service.create_order(session, user_id=current_user.id)
    return OrderCreateResponseSchema(order=order, payment_url=payment_url)


@order_router.get(
    "/",
    response_model=OrderListResponseSchema,
    summary="List the current user's orders",
    description=(
        "Retrieve a **paginated list** of orders placed by the authenticated user, "
        "sorted by creation date descending.\n\n"
        "Use `page` and `page_size` query parameters for pagination."
    ),
    responses={
        200: {"description": "Paginated order list returned."},
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
    },
)
async def list_my_orders(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user=Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
):
    orders, total = await service.get_user_orders(
        session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return OrderListResponseSchema(
        items=orders,
        total=total,
        page=page,
        page_size=page_size,
    )


@order_router.get(
    "/{order_id}",
    response_model=OrderResponseSchema,
    summary="Get a specific order by ID",
    description=(
        "Retrieve full details of a single order.\n\n"
        "The order must belong to the authenticated user — "
        "users cannot view each other's orders."
    ),
    responses={
        200: {"description": "Order details returned."},
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        404: {
            "description": "Order not found or belongs to another user.",
            "content": {
                "application/json": {"example": {"detail": "Order not found."}}
            },
        },
    },
)
async def get_order(
    order_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    orders, _ = await service.get_user_orders(session, user_id=current_user.id)
    order = next((o for o in orders if o.id == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


@order_router.patch(
    "/{order_id}/cancel",
    response_model=OrderCancelResponseSchema,
    summary="Cancel a pending order",
    description=(
        "Cancel an order that is still in **PENDING** status.\n\n"
        "Orders that have already been paid or shipped cannot be cancelled via this endpoint. "
        "Only the order owner can cancel their own order."
    ),
    responses={
        200: {"description": "Order cancelled successfully."},
        400: {
            "description": "Order cannot be cancelled (already paid or shipped).",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot cancel a paid order."}
                }
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
async def cancel_order(
    order_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    return await service.cancel_order(
        session, order_id=order_id, user_id=current_user.id
    )


@order_router.post(
    "/{order_id}/revalidate",
    response_model=OrderResponseSchema,
    summary="Revalidate order total before payment",
    description=(
        "Recalculate and update the **total amount** of an order based on current movie prices.\n\n"
        "Call this endpoint before initiating payment to ensure the amount is up to date, "
        "especially if significant time has passed since the order was created."
    ),
    responses={
        200: {"description": "Order total revalidated."},
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
async def revalidate_order(
    order_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    return await service.revalidate_total(
        session, order_id=order_id, user_id=current_user.id
    )


@order_router.post(
    "/{order_id}/paid",
    response_model=OrderResponseSchema,
    summary="Mark order as paid (payment gateway webhook)",
    include_in_schema=False,  # hide from public docs
)
async def webhook_paid(
    order_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    # TODO: verify webhook signature here
    return await service.mark_as_paid(session, order_id=order_id)
