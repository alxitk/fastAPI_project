from typing import Dict

from fastapi import FastAPI

from app.modules.movies.routers.moderator_routers import moderator_router
from app.modules.movies.routers.movies_routers import movies_router
from app.modules.users.routers.auth_router import auth_router
from app.modules.users.routers.password_router import password_router
from app.modules.users.routers.registration_router import reg_router


app = FastAPI()


@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"message": "Hello, World!"}


app.include_router(auth_router)
app.include_router(password_router)
app.include_router(reg_router)
app.include_router(movies_router)
app.include_router(moderator_router)
