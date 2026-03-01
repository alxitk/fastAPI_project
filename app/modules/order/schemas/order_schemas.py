from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.modules.order.models.enum import OrderStatusEnum


class OrderItemResponseSchema(BaseModel):
    id: int
    movie_id: int
    price_at_order: Decimal

    model_config = ConfigDict(
        from_attributes=True
    )


class OrderResponseSchema(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: Decimal
    order_items: List[OrderItemResponseSchema]

    model_config = ConfigDict(
        from_attributes=True
    )


class OrderListResponseSchema(BaseModel):
    """Paginated list of orders."""
    items: List[OrderResponseSchema]
    total: int
    page: int
    page_size: int


class OrderCancelResponseSchema(BaseModel):
    id: int
    status: OrderStatusEnum

    model_config = ConfigDict(
        from_attributes=True
    )


class OrderAdminFilter(BaseModel):
    user_id: Optional[int] = None
    status: Optional[OrderStatusEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 20


class OrderCreateResponseSchema(BaseModel):
    """Returned after order is placed; contains redirect URL for payment."""
    order: OrderResponseSchema
    payment_url: str
