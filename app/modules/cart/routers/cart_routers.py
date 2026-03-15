from fastapi import APIRouter, Depends, HTTPException

from app.config.dependencies import get_current_user, get_cart_service
from app.modules.cart.schemas.cart_schema import CartSchema, CartItemSchema, CartItemAddSchema
from app.modules.cart.services.cart_service import CartService
from app.modules.users.models.user import User

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


@cart_router.get(
    "/",
    response_model=CartSchema,
    summary="Get the current user's cart",
    description=(
        "Retrieve the shopping cart for the authenticated user, "
        "including all cart items with movie details and prices.\n\n"
        "If the user has no cart yet, an empty cart is returned."
    ),
    responses={
        200: {"description": "Cart retrieved successfully."},
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
    },
)
async def get_cart(
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    return await service.get_cart_with_items(current_user.id)


@cart_router.post(
    "/items",
    response_model=CartItemSchema,
    summary="Add a movie to the cart",
    description=(
        "Add a movie to the current user's cart by supplying its `movie_id`.\n\n"
        "If the movie is already in the cart the existing item is returned unchanged. "
        "A movie can only appear once per cart."
    ),
    responses={
        200: {"description": "Movie added to cart (or already present)."},
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found"}}
            },
        },
    },
)
async def add_item(
    payload: CartItemAddSchema,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    return await service.add_item_to_cart(current_user.id, payload.movie_id)


@cart_router.delete(
    "/items/{movie_id}",
    status_code=204,
    summary="Remove a movie from the cart",
    description=(
        "Remove the specified movie from the current user's cart.\n\n"
        "Returns **204 No Content** on success. "
        "If the movie is not in the cart the request is silently ignored."
    ),
    responses={
        204: {"description": "Movie removed from cart."},
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
    },
)
async def remove_item(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    await service.remove_item_from_cart(current_user.id, movie_id)


@cart_router.delete(
    "/",
    status_code=204,
    summary="Clear the cart",
    description=(
        "Remove **all items** from the current user's cart.\n\n"
        "Returns **204 No Content** on success."
    ),
    responses={
        204: {"description": "Cart cleared."},
        401: {
            "description": "Authentication required.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
    },
)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    await service.clear_cart(current_user.id)


@cart_router.post(
    "/checkout",
    status_code=200,
    summary="Checkout (not yet implemented)",
    description=(
        "Initiate payment for all items currently in the cart.\n\n"
        "> **Note:** This endpoint is a placeholder and will return `501 Not Implemented` "
        "until the Purchase module is complete. "
        "Use `POST /orders/` to place an order instead."
    ),
    responses={
        501: {
            "description": "Not implemented.",
            "content": {
                "application/json": {"example": {"detail": "Not implemented yet"}}
            },
        },
    },
)
async def checkout(
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    # TODO: implement when Purchase module is ready
    raise HTTPException(status_code=501, detail="Not implemented yet")
