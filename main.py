from typing import Dict

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app.exceptions.exceptions import InvalidCredentialsError
from app.modules.cart.routers.cart_routers import cart_router
from app.modules.movies.routers.moderator_routers import moderator_router
from app.modules.movies.routers.movies_routers import movies_router
from app.modules.order.routers.order_router import order_router

from app.modules.users.routers.auth_router import auth_router
from app.modules.users.routers.password_router import password_router
from app.modules.users.routers.registration_router import reg_router


app = FastAPI()


@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"message": "Hello, World!"}


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    request: Request,
    exc: InvalidCredentialsError,
):
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
