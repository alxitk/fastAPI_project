from decimal import Decimal
from typing import List

from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.movies.models.movie_models import Movie, Genre, Star, Director, Certification


async def count_movies(
    db: AsyncSession,
    year_from: int | None = None,
    year_to: int | None = None,
    imdb: float | None = None
):
    stmt = select(func.count()).select_from(Movie)

    if year_from is not None:
        stmt = stmt.where(Movie.year >= year_from)

    if year_to is not None:
        stmt = stmt.where(Movie.year <= year_to)

    if imdb is not None:
        stmt = stmt.where(Movie.imdb >= imdb)

    return await db.scalar(stmt)


async def get_movies(
        db: AsyncSession,
        offset: int = 0,
        limit: int = 100,
        year_from: int | None = None,
        year_to: int | None = None,
        imdb: int | None = None,
        sort_by: str | None = None,
        order: str = "asc",

):
    stmt = select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.stars),
        selectinload(Movie.directors),
        selectinload(Movie.certification),
    )

    if year_from is not None:
        stmt = stmt.where(Movie.year >= year_from)

    if year_to is not None:
        stmt = stmt.where(Movie.year <= year_to)

    if imdb is not None:
        stmt = stmt.where(Movie.imdb >= imdb)

    sort_map = {
        "price": Movie.price,
        "year": Movie.year,
        "imdb": Movie.imdb,
    }
    if sort_by:
        column = sort_map.get(sort_by)
        if column:
            stmt = stmt.order_by(
                desc(column) if order == "desc" else asc(column),
            )

    stmt = stmt.offset(offset).limit(limit)

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


async def get_movie_detail(db: AsyncSession, movie_id: int):
    stmt = (select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.stars),
        selectinload(Movie.directors),
        selectinload(Movie.certification)
    )
        .where(Movie.id == movie_id))
    result = await db.execute(stmt)
    return result.scalars().first()


