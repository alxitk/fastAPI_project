from datetime import datetime, timezone

from sqlalchemy import delete

from app.database.session import async_session_local
from app.modules.users.models.token import ActivationTokenModel, PasswordResetTokenModel
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.cleanup_tokens.cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Delete expired activation & password reset tokens."""
    now = datetime.now(timezone.utc)

    async def _cleanup():
        async with async_session_local() as session:
            await session.execute(
                delete(ActivationTokenModel).where(
                    ActivationTokenModel.expires_at < now
                )
            )
            await session.execute(
                delete(PasswordResetTokenModel).where(
                    PasswordResetTokenModel.expires_at < now
                )
            )
            await session.commit()

    import asyncio
    asyncio.run(_cleanup())
