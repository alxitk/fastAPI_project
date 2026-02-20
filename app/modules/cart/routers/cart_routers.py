from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_user
from app.database.session import get_db
from app.modules.cart.schemas.cart_schema import CartSchema, CartItemSchema, CartItemAddSchema
from app.modules.cart.services.cart_service import CartService
from app.modules.users.models.user import User

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


@cart_router.get("/", response_model=CartSchema)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's cart with all items."""
    service = CartService(db)
    return await service.get_cart_with_items(current_user.id)


@cart_router.post("/items", response_model=CartItemSchema)
async def add_item(
    payload: CartItemAddSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a movie to the cart."""
    service = CartService(db)
    return await service.add_item_to_cart(current_user.id, payload.movie_id)


@cart_router.delete("/items/{movie_id}", status_code=204)
async def remove_item(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a movie from the cart."""
    service = CartService(db)
    await service.remove_item_from_cart(current_user.id, movie_id)


@cart_router.delete("/", status_code=204)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear all items from the cart."""
    service = CartService(db)
    await service.clear_cart(current_user.id)


@cart_router.post("/checkout", status_code=200)
async def checkout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pay for all items in the cart."""
    # TODO: implement when Purchase module is ready
    raise HTTPException(status_code=501, detail="Not implemented yet")
