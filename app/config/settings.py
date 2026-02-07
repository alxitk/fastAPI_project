import os
import binascii
from pathlib import Path

from pydantic.v1 import BaseSettings


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent

    LOGIN_TIME_DAYS: int = 7

    BASE_URL: str = "http://localhost:8000"

    model_config = {
        "case_sensitive": False,
    }


class Settings(BaseAppSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_DB_PORT: int = int(os.getenv("POSTGRES_DB_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "fastapi_db")

    SECRET_KEY_ACCESS: str = (
        os.getenv("SECRET_KEY_ACCESS") or binascii.hexlify(os.urandom(32)).decode()
    )
    SECRET_KEY_REFRESH: str = (
        os.getenv("SECRET_KEY_REFRESH") or binascii.hexlify(os.urandom(32)).decode()
    )
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")


class TestingSettings(BaseAppSettings):
    SECRET_KEY_ACCESS: str = "SECRET_KEY_ACCESS"
    SECRET_KEY_REFRESH: str = "SECRET_KEY_REFRESH"
    JWT_SIGNING_ALGORITHM: str = "HS256"
