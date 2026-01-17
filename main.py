from fastapi import FastAPI

from app.modules.users.routers.auth import auth_router

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


app.include_router(auth_router)
