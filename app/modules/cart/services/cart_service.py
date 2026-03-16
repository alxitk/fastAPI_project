from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.modules.cart.models.cart_models import Cart, CartItem
from app.modules.movies.models.movie_models import Movie


class CartService:
    """Service layer for cart-related business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create_cart(self, user_id: int) -> Cart:
        """Get user's cart or create if doesn't exist."""
        stmt = (
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.movie))
            .where(Cart.user_id == user_id)
        )
        result = await self._db.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=user_id)
            self._db.add(cart)
            await self._db.flush()
            await self._db.refresh(cart)

        return cart

    async def add_item_to_cart(self, user_id: int, movie_id: int) -> CartItem:
        """Add a movie to user's cart."""
        movie_stmt = select(Movie).where(Movie.id == movie_id)
        movie_result = await self._db.execute(movie_stmt)
        movie = movie_result.scalar_one_or_none()

        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        # TODO: check if movie already purchased
        # purchased = await self._db.execute(
        #     select(Purchase).where(
        #         Purchase.user_id == user_id,
        #         Purchase.movie_id == movie_id
        #     )
        # )
        # if purchased.scalar_one_or_none():
        #     raise HTTPException(status_code=400, detail="Movie already purchased")

        cart = await self.get_or_create_cart(user_id)

        item_stmt = select(CartItem).where(
            CartItem.cart_id == cart.id, CartItem.movie_id == movie_id
        )
        item_result = await self._db.execute(item_stmt)
        existing_item = item_result.scalar_one_or_none()

        if existing_item:
            raise HTTPException(status_code=400, detail="Movie already in cart")

        cart_item = CartItem(cart_id=cart.id, movie_id=movie_id)
        self._db.add(cart_item)
        try:
            await self._db.commit()
        except IntegrityError:
            await self._db.rollback()
            raise HTTPException(status_code=400, detail="Movie already in cart")

        await self._db.refresh(cart_item)

        await self._db.refresh(cart_item, ["movie"])

        return cart_item

    async def remove_item_from_cart(self, user_id: int, movie_id: int) -> None:
        """Remove a movie from user's cart."""
        cart = await self.get_or_create_cart(user_id)

        stmt = select(CartItem).where(
            CartItem.cart_id == cart.id, CartItem.movie_id == movie_id
        )
        result = await self._db.execute(stmt)
        cart_item = result.scalar_one_or_none()

        if not cart_item:
            raise HTTPException(status_code=404, detail="Item not found in cart")

        await self._db.delete(cart_item)
        await self._db.commit()

    async def clear_cart(self, user_id: int) -> None:
        """Clear all items from user's cart."""
        cart = await self.get_or_create_cart(user_id)

        await self._db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        await self._db.commit()

    async def get_cart_with_items(self, user_id: int) -> Cart:
        """Get user's cart with all items and movie details."""
        return await self.get_or_create_cart(user_id)

    async def get_all_carts(self) -> list[Cart]:
        """Get all users' carts with items (moderator only)."""
        stmt = select(Cart).options(
            selectinload(Cart.items).selectinload(CartItem.movie)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def check_movie_in_carts(self, movie_id: int) -> list[Cart]:
        """Check if movie exists in any user's cart (moderator only)."""
        stmt = (
            select(Cart)
            .join(CartItem)
            .where(CartItem.movie_id == movie_id)
            .options(selectinload(Cart.items).selectinload(CartItem.movie))
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
