from celery import Celery


celery_app = Celery(
    "app",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
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
