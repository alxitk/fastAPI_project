from decimal import Decimal
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions.exceptions import BadRequestException, NotFoundException
from app.modules.cart.models.cart_models import CartItem, Cart
from app.modules.order.models.enum import OrderStatusEnum
from app.modules.order.models.order_models import Order, OrderItem
from app.modules.order.schemas.order_schemas import OrderAdminFilter


class OrderService:
    """Service layer for order business logic."""

    async def _get_order_or_404(
            self,
            session: AsyncSession,
            order_id: int,
            user_id: int | None = None,
            options=(),
    ) -> Order:
        stmt = select(Order).where(Order.id == order_id).options(*options)
        order = (await session.execute(stmt)).scalar_one_or_none()
        if not order:
            raise NotFoundException("Order not found.")

        if user_id is not None and order.user_id != user_id:
            raise NotFoundException("Order not found.")

        return order

    async def create_order(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> tuple[Order, str]:
        """
        1. Load cart items for the user.
        2. Run all validations.
        3. Create Order + OrderItems.
        4. Clear cart.
        5. Return order + payment gateway URL.
        """
        cart_stmt = (
            select(CartItem)
            .join(CartItem.cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(CartItem.movie))
        )
        cart_items: List[CartItem] = (await session.execute(cart_stmt)).scalars().all()

        if not cart_items:
            raise BadRequestException("Cart is empty.")

        available_items = [item for item in cart_items if item.movie is not None]
        excluded = len(cart_items) - len(available_items)
        if not available_items:
            raise BadRequestException(
                "None of the movies in your cart are available for purchase."
            )

        movie_ids = [item.movie_id for item in available_items]

        owned_stmt = (
            select(OrderItem.movie_id)
            .join(OrderItem.order)
            .where(
                Order.user_id == user_id,
                Order.status == OrderStatusEnum.PAID,
                OrderItem.movie_id.in_(movie_ids),
            )
        )
        owned_ids = set((await session.execute(owned_stmt)).scalars().all())
        available_items = [
            item for item in available_items if item.movie_id not in owned_ids
        ]
        if not available_items:
            raise BadRequestException(
                "All movies in your cart have already been purchased."
            )

        movie_ids = [item.movie_id for item in available_items]

        pending_stmt = (
            select(func.count())
            .select_from(OrderItem)
            .join(OrderItem.order)
            .where(
                Order.user_id == user_id,
                Order.status == OrderStatusEnum.PENDING,
                OrderItem.movie_id.in_(movie_ids),
            )
        )
        pending_count = (await session.execute(pending_stmt)).scalar_one()
        if pending_count:
            raise BadRequestException(
                "You already have a pending order containing one or more of these movies."
            )

        total = sum(
            (item.movie.price for item in available_items),
            Decimal("0.00"),
        )

        order = Order(
            user_id=user_id,
            status=OrderStatusEnum.PENDING,
            total_amount=total,
        )
        session.add(order)
        await session.flush()

        for item in available_items:
            session.add(
                OrderItem(
                    order_id=order.id,
                    movie_id=item.movie_id,
                    price_at_order=item.movie.price,
                )
            )

        for item in cart_items:
            await session.delete(item)

        await session.commit()
        await session.refresh(order, ["order_items"])

        payment_url = self._build_payment_url(order)

        # Optionally notify user about excluded movies
        if excluded:
            pass  # emit notification / log

        return order, payment_url

    @staticmethod
    def _build_payment_url(order: Order) -> str:
        """Replace with real Stripe / PayPal SDK call."""
        return f"https://payment.example.com/pay?order_id={order.id}"

    async def revalidate_total(
            self,
            session: AsyncSession,
            order_id: int,
            user_id: int,
    ) -> Order:
        """Recalculate total_amount from current movie prices before charging."""

        order = await self._get_order_or_404(
            session,
            order_id,
            user_id=user_id,
            options=(selectinload(Order.order_items).selectinload(OrderItem.movie),),
        )

        if order.status != OrderStatusEnum.PENDING:
            raise BadRequestException("Only pending orders can be revalidated.")

        order.total_amount = sum(
            (item.movie.price for item in order.order_items if item.movie is not None),
            Decimal("0.00"),
        )

        await session.commit()
        await session.refresh(order)
        return order

    async def cancel_order(
        self,
        session: AsyncSession,
        order_id: int,
        user_id: int,
    ) -> Order:
        order = await self._get_order_or_404(session, order_id, user_id=user_id)

        if order.user_id != user_id:
            raise NotFoundException("Order not found.")
        if order.status == OrderStatusEnum.PAID:
            raise BadRequestException(
                "Paid orders cannot be canceled directly. Please submit a refund request."
            )
        if order.status == OrderStatusEnum.CANCELLED:
            raise BadRequestException("Order is already canceled.")

        order.status = OrderStatusEnum.CANCELLED
        await session.commit()
        await session.refresh(order)
        return order

    async def get_user_orders(
        self,
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Order], int]:
        base = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.order_items))
        )
        total = (
            await session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()

        orders = (
            (
                await session.execute(
                    base.order_by(Order.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )

        return list(orders), total

    async def get_all_orders(
        self,
        session: AsyncSession,
        filters: OrderAdminFilter,
    ) -> tuple[List[Order], int]:
        stmt = select(Order).options(selectinload(Order.order_items))

        if filters.user_id:
            stmt = stmt.where(Order.user_id == filters.user_id)
        if filters.status:
            stmt = stmt.where(Order.status == filters.status)
        if filters.date_from:
            stmt = stmt.where(Order.created_at >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Order.created_at <= filters.date_to)

        total = (
            await session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        orders = (
            (
                await session.execute(
                    stmt.order_by(Order.created_at.desc())
                    .offset((filters.page - 1) * filters.page_size)
                    .limit(filters.page_size)
                )
            )
            .scalars()
            .all()
        )

        return list(orders), total

    async def mark_as_paid(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> Order:
        """Called by payment gateway webhook after successful charge."""
        order = await self._get_order_or_404(session, order_id)
        if order.status != OrderStatusEnum.PENDING:
            raise BadRequestException("Only pending orders can be marked as paid.")

        order.status = OrderStatusEnum.PAID
        await session.commit()
        await session.refresh(order)

        # TODO: send confirmation email (e.g. via Celery / background task)
        return order
