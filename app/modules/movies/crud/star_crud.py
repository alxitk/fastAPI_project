from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.movies.models.movie_models import Star


async def create_star(db: AsyncSession, name: str) -> Star:
    """
    Create a new star by its name.
    """
    star = Star(name=name)
    db.add(star)
    await db.commit()
    await db.refresh(star)
    return star


async def get_star(db: AsyncSession, star_id: int) -> Star | None:
    """
    Get a star by its ID.
    """
    result = await db.execute(select(Star).where(Star.id == star_id))
    return result.scalar_one_or_none()


async def get_star_list(db: AsyncSession) -> list[Star]:
    """
    Get a list of stars.
    """
    result = await db.execute(select(Star))
    return result.scalars().all()


async def update_star(db: AsyncSession, star_id: int, name: str) -> Star | None:
    """
    Update a star by its ID.
    """
    star = await get_star(db, star_id)
    if star:
        star.name = name
        await db.commit()
        await db.refresh(star)
    return star


async def delete_star(db: AsyncSession, star_id: int) -> bool:
    """
    Delete a star by its ID.
    """
    star = await get_star(db, star_id)
    if not star:
        return False
    await db.delete(star)
    await db.commit()
    return True


async def get_star_by_name(db: AsyncSession, name: str) -> Star | None:
    """
    Retrieve a star by its name.
    """
    result = await db.execute(select(Star).where(Star.name == name))
    return result.scalar_one_or_none()
