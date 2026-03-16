from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.movies.models.movie_models import Genre


async def create_genre(db: AsyncSession, name: str) -> Genre:
    """
    Create and persist a new genre in the database.
    """
    genre = Genre(name=name)
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return genre


async def list_genres(db: AsyncSession) -> Sequence[Genre]:
    """
    Retrieve all genres from the database.
    """
    result = await db.execute(select(Genre))
    return result.scalars().all()


async def get_genre(db: AsyncSession, genre_id: int) -> Genre | None:
    """
    Retrieve a single genre by its ID.
    """
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    return result.scalar_one_or_none()


async def update_genre(db: AsyncSession, genre_id: int, name: str) -> Genre | None:
    """
    Update the name of an existing genre by its ID.
    """
    genre = await get_genre(db, genre_id)
    if genre:
        genre.name = name
        await db.commit()
        await db.refresh(genre)
    return genre


async def delete_genre(db: AsyncSession, genre_id: int) -> bool:
    """
    Delete a genre by its ID.
    """
    genre = await get_genre(db, genre_id)
    if not genre:
        return False
    await db.delete(genre)
    await db.commit()
    return True
