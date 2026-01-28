from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.movies.models.movie_models import Movie


async def count_movies(db: AsyncSession):
    movies = select(func.count()).select_from(Movie)
    return await db.scalar(movies)


async def get_movies(db: AsyncSession, offset: int = 0, limit: int = 100):
    stmt = select(Movie).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
