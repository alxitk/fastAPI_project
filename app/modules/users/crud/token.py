from datetime import datetime, timezone
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models.token import ActivationTokenModel, RefreshTokenModel, PasswordResetTokenModel


async def create_activation_token(db: AsyncSession, user_id: int) -> ActivationTokenModel:
    """Creates a new activation token for user."""
    token = ActivationTokenModel(user_id=user_id)
    db.add(token)
    await db.flush()
    await db.refresh(token)
    return token


async def get_by_token(db: AsyncSession, token: str) -> ActivationTokenModel | None:
    """Gets activation token by token string."""
    result = await db.execute(
        select(ActivationTokenModel).where(ActivationTokenModel.token == token)
    )
    return result.scalar_one_or_none()


async def is_token_valid(db: AsyncSession, token: str) -> bool:
    """Checks if token exists and is not expired."""
    result = await db.execute(
        select(ActivationTokenModel)
        .where(ActivationTokenModel.token == token)
        .where(ActivationTokenModel.expires_at > datetime.now(timezone.utc))
    )
    return result.scalar_one_or_none() is not None


async def delete_by_user_id(db: AsyncSession, user_id: int) -> int:
    """Deletes all activation tokens for user. Returns count of deleted tokens."""
    result = await db.execute(
        delete(ActivationTokenModel).where(ActivationTokenModel.user_id == user_id)
    )
    return result.rowcount or 0


async def delete_expired(db: AsyncSession) -> int:
    """Deletes all expired activation tokens. Returns count of deleted tokens."""
    result = await db.execute(
        delete(ActivationTokenModel).where(
            ActivationTokenModel.expires_at < datetime.now(timezone.utc)
        )
    )
    return result.rowcount or 0


async def exists_valid(db: AsyncSession, user_id: int) -> bool:
    """Checks if user has any valid (non-expired) activation token."""
    result = await db.execute(
        select(func.count())
        .select_from(ActivationTokenModel)
        .where(ActivationTokenModel.user_id == user_id)
        .where(ActivationTokenModel.expires_at > datetime.now(timezone.utc))
    )
    return (result.scalar() or 0) > 0


async def create_password_reset_token(db: AsyncSession, user_id: int) -> PasswordResetTokenModel:
    """Creates a new password reset token for user."""
    token = PasswordResetTokenModel(user_id=user_id)
    db.add(token)
    await db.flush()
    await db.refresh(token)
    return token


async def get_password_reset_by_token(db: AsyncSession, token: str) -> PasswordResetTokenModel | None:
    """Gets password reset token by token string."""
    result = await db.execute(
        select(PasswordResetTokenModel).where(PasswordResetTokenModel.token == token)
    )
    return result.scalar_one_or_none()


async def is_password_reset_token_valid(db: AsyncSession, token: str) -> bool:
    """Checks if password reset token exists and is not expired."""
    result = await db.execute(
        select(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.token == token)
        .where(PasswordResetTokenModel.expires_at > datetime.now(timezone.utc))
    )
    return result.scalar_one_or_none() is not None


async def delete_password_reset_by_user_id(db: AsyncSession, user_id: int) -> int:
    """Deletes all password reset tokens for user. Returns count of deleted tokens."""
    result = await db.execute(
        delete(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user_id)
    )
    return result.rowcount or 0


async def delete_expired_password_reset_tokens(db: AsyncSession) -> int:
    """Deletes all expired password reset tokens. Returns count of deleted tokens."""
    result = await db.execute(
        delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.expires_at < datetime.now(timezone.utc)
        )
    )
    return result.rowcount or 0


async def exists_valid_password_reset_token(db: AsyncSession, user_id: int) -> bool:
    """Checks if user has any valid (non-expired) password reset token."""
    result = await db.execute(
        select(func.count())
        .select_from(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.user_id == user_id)
        .where(PasswordResetTokenModel.expires_at > datetime.now(timezone.utc))
    )
    return (result.scalar() or 0) > 0


async def create_refresh_token(db: AsyncSession, user_id: int, token: str, expires_at: datetime) -> RefreshTokenModel:
    """Creates a new refresh token for user."""
    refresh = RefreshTokenModel(user_id=user_id, token=token, expires_at=expires_at)
    db.add(refresh)
    await db.flush()
    await db.refresh(refresh)
    return refresh


async def get_refresh_token_by_token(db: AsyncSession, token: str) -> RefreshTokenModel | None:
    """Gets refresh token by token string."""
    result = await db.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.token == token)
    )
    return result.scalar_one_or_none()


async def is_refresh_token_valid(db: AsyncSession, token: str) -> bool:
    """Checks if refresh token exists and is not expired."""
    result = await db.execute(
        select(RefreshTokenModel)
        .where(RefreshTokenModel.token == token)
        .where(RefreshTokenModel.expires_at > datetime.now(timezone.utc))
    )
    return result.scalar_one_or_none() is not None


async def delete_refresh_token_by_user_id(db: AsyncSession, user_id: int) -> int:
    """Deletes all refresh tokens for user. Returns count of deleted tokens."""
    result = await db.execute(
        delete(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
    )
    return result.rowcount or 0


async def delete_expired_refresh_tokens(db: AsyncSession) -> int:
    """Deletes all expired refresh tokens. Returns count of deleted tokens."""
    result = await db.execute(
        delete(RefreshTokenModel).where(
            RefreshTokenModel.expires_at < datetime.now(timezone.utc)
        )
    )
    return result.rowcount or 0


async def exists_valid_refresh_token(db: AsyncSession, user_id: int) -> bool:
    """Checks if user has any valid (non-expired) refresh token."""
    result = await db.execute(
        select(func.count())
        .select_from(RefreshTokenModel)
        .where(RefreshTokenModel.user_id == user_id)
        .where(RefreshTokenModel.expires_at > datetime.now(timezone.utc))
    )
    return (result.scalar() or 0) > 0
