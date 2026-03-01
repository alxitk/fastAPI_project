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
    summary="Place an order from cart",
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
    summary="List current user's orders",
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
    summary="Get a specific order",
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
    summary="Revalidate total amount before payment",
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
