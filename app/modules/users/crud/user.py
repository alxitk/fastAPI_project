from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete as sql_delete

from app.modules.users.models.user import User


async def create_user(
    db: AsyncSession,
    email: str,
    hashed_password: str,
    is_active: bool = False
) -> User:
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        is_active=is_active
)
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def exists_by_email(db: AsyncSession, email: str) -> bool:
    stmt = select(User.id).where(User.email == email).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def activate(db: AsyncSession, user_id: int) -> bool:
    stmt = update(User).where(User.id == user_id).values(is_active=True)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def deactivate(db: AsyncSession, user_id: int) -> bool:
    stmt = update(User).where(User.id == user_id).values(is_active=False)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def set_password(db: AsyncSession, user_id: int, hashed_password: str) -> bool:
    stmt = update(User).where(User.id == user_id).values(hashed_password=hashed_password)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def change_group(db: AsyncSession, user_id: int, group_id: int) -> bool:
    stmt = update(User).where(User.id == user_id).values(group_id=group_id)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def delete(db: AsyncSession, user_id: int) -> bool:
    stmt = sql_delete(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.rowcount > 0
