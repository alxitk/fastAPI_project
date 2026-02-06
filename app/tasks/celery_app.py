import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "app",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-expired-tokens-every-hour": {
            "task": "app.tasks.cleanup_tokens.cleanup_expired_tokens",
            "schedule": 60 * 60,
        },
    },
)


import app.tasks.cleanup_tokens  # noqa
