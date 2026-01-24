from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete as sql_delete

from app.modules.users.models.user import User


async def create_user(
    db: AsyncSession, email: str, hashed_password: str, is_active: bool = False
) -> User:
    """
    Create a new user in the database.

    Args:
        db: Async SQLAlchemy session.
        email: User email address.
        hashed_password: Hashed user password.
        is_active: Whether the user is active on creation.

    Returns:
        Created User instance.
    """
    db_user = User(email=email, hashed_password=hashed_password, is_active=is_active)
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Get a user by email.

    Args:
        db: Async SQLAlchemy session.
        email: User email address.

    Returns:
        User instance if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    """
    Get a user by ID.

    Args:
        db: Async SQLAlchemy session.
        user_id: User ID.

    Returns:
        User instance if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def exists_by_email(db: AsyncSession, email: str) -> bool:
    """
    Check if a user with the given email exists.

    Args:
        db: Async SQLAlchemy session.
        email: User email address.

    Returns:
        True if user exists, otherwise False.
    """
    stmt = select(User.id).where(User.email == email).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def activate(db: AsyncSession, user_id: int) -> bool:
    """
    Activate a user account.

    Args:
        db: Async SQLAlchemy session.
        user_id: User ID.

    Returns:
        True if user was activated, otherwise False.
    """
    stmt = update(User).where(User.id == user_id).values(is_active=True)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def deactivate(db: AsyncSession, user_id: int) -> bool:
    """
    Deactivate a user account.

    Args:
        db: Async SQLAlchemy session.
        user_id: User ID.

    Returns:
        True if user was deactivated, otherwise False.
    """
    stmt = update(User).where(User.id == user_id).values(is_active=False)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def set_password(db: AsyncSession, user_id: int, hashed_password: str) -> bool:
    """
    Update user's password.

    Args:
        db: Async SQLAlchemy session.
        user_id: User ID.
        hashed_password: New hashed password.

    Returns:
        True if password was updated, otherwise False.
    """
    stmt = (
        update(User).where(User.id == user_id).values(hashed_password=hashed_password)
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def change_group(db: AsyncSession, user_id: int, group_id: int) -> bool:
    """
    Change user's group.

    Args:
        db: Async SQLAlchemy session.
        user_id: User ID.
        group_id: New group ID.

    Returns:
        True if group was changed, otherwise False.
    """
    stmt = update(User).where(User.id == user_id).values(group_id=group_id)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def delete(db: AsyncSession, user_id: int) -> bool:
    """
    Delete a user from the database.

    Args:
        db: Async SQLAlchemy session.
        user_id: User ID.

    Returns:
        True if user was deleted, otherwise False.
    """
    stmt = sql_delete(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.rowcount > 0
