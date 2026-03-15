import secrets
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config.settings import Settings
from app.exceptions.exceptions import InvalidCredentialsError
from app.modules.cart.routers.cart_routers import cart_router
from app.modules.movies.routers.moderator_routers import moderator_router
from app.modules.movies.routers.movies_routers import movies_router
from app.modules.order.routers.order_router import order_router
from app.modules.payment.routers.payment_admin_router import admin_payment_router
from app.modules.payment.routers.payment_router import payment_router
from app.modules.users.routers.auth_router import auth_router
from app.modules.users.routers.password_router import password_router
from app.modules.users.routers.registration_router import reg_router


app = FastAPI(
    title="Cinema API",
    version="1.0.0",
    description=(
        "## Cinema API\n\n"
        "A full-featured REST API for a cinema platform built with **FastAPI**.\n\n"
        "### Key capabilities\n"
        "- **Authentication** — JWT access & refresh tokens, email-based activation\n"
        "- **Movies** — browse, search, filter, like, comment, favourites\n"
        "- **Cart** — add/remove movies, clear cart\n"
        "- **Orders** — place orders from cart, cancel, revalidate totals\n"
        "- **Payments** — Stripe integration, webhook processing\n"
        "- **Admin / Moderator** — manage movies, genres, stars, certifications, users\n\n"
        "### Authentication\n"
        "Protected endpoints require a **Bearer JWT** token.\n"
        "Obtain a token via `POST /auth/login` and pass it in the "
        "`Authorization: Bearer <token>` header.\n\n"
        "> **Documentation access** is restricted to authorised staff only."
    ),
    docs_url=None,  # disable default /docs
    redoc_url=None,  # disable default /redoc
    openapi_url=None,  # disable default /openapi.json
    contact={
        "name": "Cinema API Support",
        "email": "support@cinema-api.example.com",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Login, logout, token refresh.",
        },
        {
            "name": "Registration",
            "description": "User registration, email activation, admin account management.",
        },
        {
            "name": "Password",
            "description": "Change password, password-reset flow.",
        },
        {
            "name": "Movies",
            "description": "Browse movies, genres, stars. Like, favourite, comment.",
        },
        {
            "name": "Moderator",
            "description": (
                "Moderator-only actions: create/update/delete movies, genres, stars, "
                "certifications; inspect carts and orders."
            ),
        },
        {
            "name": "Cart",
            "description": "Shopping cart management for the current user.",
        },
        {
            "name": "Orders",
            "description": "Place orders from the cart, view order history, cancel orders.",
        },
        {
            "name": "payments",
            "description": "Stripe payment intents, webhook processing, payment history.",
        },
        {
            "name": "admin-payments",
            "description": "Admin-only view of all payments with filtering.",
        },
    ],
)


_http_basic = HTTPBasic()
_settings = Settings()


def _verify_docs_credentials(
    credentials: HTTPBasicCredentials = Depends(_http_basic),
) -> None:
    """Verify HTTP Basic credentials for documentation endpoints."""
    correct_username = secrets.compare_digest(
        credentials.username.encode(), _settings.DOCS_USERNAME.encode()
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode(), _settings.DOCS_PASSWORD.encode()
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid documentation credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/openapi.json", include_in_schema=False)
async def openapi_schema(
    _: None = Depends(_verify_docs_credentials),
) -> JSONResponse:
    """Return the OpenAPI schema (protected)."""
    return JSONResponse(
        get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            contact=app.contact,
            license_info=app.license_info,
            tags=app.openapi_tags,
            routes=app.routes,
        )
    )


@app.get("/docs", include_in_schema=False)
async def swagger_ui(
    _: None = Depends(_verify_docs_credentials),
) -> HTMLResponse:
    """Swagger UI (protected — requires HTTP Basic Auth)."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} — Swagger UI",
        swagger_ui_parameters={"persistAuthorization": True},
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_ui(
    _: None = Depends(_verify_docs_credentials),
) -> HTMLResponse:
    """ReDoc UI (protected — requires HTTP Basic Auth)."""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} — ReDoc",
    )


@app.get("/", tags=["Health"])
async def read_root() -> Dict[str, str]:
    """Health-check endpoint."""
    return {
        "message": "Cinema API is running. Docs available at /docs (authorised staff only)."
    }


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    request: Request,
    exc: InvalidCredentialsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


app.include_router(auth_router)
app.include_router(password_router)
app.include_router(reg_router)
app.include_router(movies_router)
app.include_router(moderator_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(payment_router)
app.include_router(admin_payment_router)
