from decimal import Decimal
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.movies.models.movie_models import Movie, Genre, Star, Director, Certification


async def count_movies(db: AsyncSession):
    movies = select(func.count()).select_from(Movie)
    return await db.scalar(movies)


async def get_movies(db: AsyncSession, offset: int = 0, limit: int = 100):
    stmt = select(Movie).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_movie(
    db: AsyncSession,
    *,
    name: str,
    year: int,
    time: int,
    imdb: float,
    votes: int,
    description: str,
    price: Decimal,
    certification_id: int,
    genres: List[Genre],
    stars: List[Star],
    directors: List[Director],
):

    movie = Movie(
        name=name,
        year=year,
        time=time,
        imdb=imdb,
        votes=votes,
        description=description,
        price=price,
        certification_id=certification_id,
        genres=genres,
        stars=stars,
        directors=directors,
    )
    db.add(movie)
    await db.flush()
    return movie


async def create_certification(db: AsyncSession, name: str):
    certification = Certification(name=name)
    db.add(certification)
    await db.commit()
    await db.refresh(certification)
    return certification

