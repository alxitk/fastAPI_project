import os
from pathlib import Path

from pydantic.v1 import BaseSettings


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent


class Settings(BaseAppSettings):
    POSTGRES_USER = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_DB_PORT = int(os.getenv("POSTGRES_DB_PORT", 5432))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "test_db")


class TestingSettings(BaseAppSettings):
    SECRET_KEY_ACCESS: str = "SECRET_KEY_ACCESS"
    SECRET_KEY_REFRESH: str = "SECRET_KEY_REFRESH"
    JWT_SIGNING_ALGORITHM: str = "HS256"
