from decimal import Decimal
from typing import List

from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.movies.models.associations import movie_genres
from app.modules.movies.models.movie_models import Movie, Genre, Star, Director, Certification, MovieLike, \
    MovieFavorites, MovieComment
from app.modules.movies.schemas.movie_schema import MovieUpdateSchema


async def count_movies(
    db: AsyncSession,
    year_from: int | None = None,
    year_to: int | None = None,
    imdb: float | None = None,
    search: str | None = None
):
    stmt = (
        select(func.count(func.distinct(Movie.id)))
        .select_from(Movie)
        .outerjoin(Movie.stars)
        .outerjoin(Movie.directors)
    )

    if year_from is not None:
        stmt = stmt.where(Movie.year >= year_from)

    if year_to is not None:
        stmt = stmt.where(Movie.year <= year_to)

    if imdb is not None:
        stmt = stmt.where(Movie.imdb >= imdb)
    
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Movie.name.ilike(pattern),
                Movie.description.ilike(pattern),
                Star.name.ilike(pattern),
                Director.name.ilike(pattern),
            )
        )
    
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
    search: str | None = None,

):
    stmt = (
        select(Movie)
        .distinct()
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.stars),
            selectinload(Movie.directors),
            selectinload(Movie.certification),
        )
        .outerjoin(Movie.stars)
        .outerjoin(Movie.directors)
    )

    if year_from is not None:
        stmt = stmt.where(Movie.year >= year_from)

    if year_to is not None:
        stmt = stmt.where(Movie.year <= year_to)

    if imdb is not None:
        stmt = stmt.where(Movie.imdb >= imdb)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(
            Movie.name.ilike(pattern),
            Movie.description.ilike(pattern),
            Star.name.ilike(pattern),
            Director.name.ilike(pattern),
        ))

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


async def update_movie(
        db: AsyncSession,
        movie_id: int,
        movie_data: MovieUpdateSchema
):
    stmt = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.stars),
            selectinload(Movie.directors),
        )
    )
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        return None

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        if field not in ("genres", "stars", "directors"):
            setattr(movie, field, value)

    if movie_data.genres is not None:
        movie.genres.clear()
        for name in movie_data.genres:
            result = await db.execute(select(Genre).where(Genre.name == name))
            genre = result.scalar_one_or_none()
            if not genre:
                genre = Genre(name=name)
                db.add(genre)
                await db.flush()
            movie.genres.append(genre)

    if movie_data.stars is not None:
        movie.stars.clear()
        for name in movie_data.stars:
            result = await db.execute(select(Star).where(Star.name == name))
            star = result.scalar_one_or_none()
            if not star:
                star = Star(name=name)
                db.add(star)
                await db.flush()
            movie.stars.append(star)

    if movie_data.directors is not None:
        movie.directors.clear()
        for name in movie_data.directors:
            result = await db.execute(select(Director).where(Director.name == name))
            director = result.scalar_one_or_none()
            if not director:
                director = Director(name=name)
                db.add(director)
                await db.flush()
            movie.directors.append(director)

    await db.commit()
    await db.refresh(movie)
    return movie


async def delete_movie(db: AsyncSession, movie_id: int):
    return {"detail": "Deletion disabled until purchases are implemented"}


async def create_certification(db: AsyncSession, name: str):
    certification = Certification(name=name)
    db.add(certification)
    await db.commit()
    await db.refresh(certification)
    return certification


async def get_movie_detail(db: AsyncSession, movie_id: int):
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.stars),
            selectinload(Movie.directors),
            selectinload(Movie.certification),
            selectinload(Movie.comments)
                .selectinload(MovieComment.replies),
        )
        .where(Movie.id == movie_id)
    )

    result = await db.execute(stmt)
    return result.scalars().first()


async def add_movie_like(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    value: int
):
    stmt = select(MovieLike).where(
        MovieLike.user_id == user_id,
        MovieLike.movie_id == movie_id
    )
    result = await db.execute(stmt)
    like = result.scalars().first()

    if like:
        like.value = value
    else:
        like = MovieLike(user_id=user_id, movie_id=movie_id, value=value)
        db.add(like)

    await db.commit()
    await db.refresh(like)
    return like


async def get_favorite(db: AsyncSession, user_id: int, movie_id: int):
    stmt = select(MovieFavorites).where(
        MovieFavorites.user_id == user_id,
        MovieFavorites.movie_id == movie_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_favorite(db: AsyncSession, user_id: int, movie_id: int):
    fav = MovieFavorites(user_id=user_id, movie_id=movie_id)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)
    return fav


async def delete_favorite(db: AsyncSession, user_id: int, movie_id: int):
    stmt = select(MovieFavorites).where(
        MovieFavorites.user_id == user_id,
        MovieFavorites.movie_id == movie_id
    )
    result = await db.execute(stmt)
    favorite = result.scalar_one_or_none()
    if favorite:
        await db.delete(favorite)
        await db.commit()
    return favorite


async def list_favorites(
        db: AsyncSession,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        year_from: int | None = None,
        year_to: int | None = None,
        imdb: int | None = None,
        sort_by: str | None = None,
        order: str = "asc",
        search: str | None = None,
):
    stmt = (
        select(Movie)
        .join(MovieFavorites, Movie.id == MovieFavorites.movie_id)
        .where(MovieFavorites.user_id == user_id)
        .outerjoin(Movie.stars)
        .outerjoin(Movie.directors)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.stars),
            selectinload(Movie.directors),
            selectinload(Movie.certification),
        )
        .distinct()
    )

    if year_from is not None:
        stmt = stmt.where(Movie.year >= year_from)
    if year_to is not None:
        stmt = stmt.where(Movie.year <= year_to)
    if imdb is not None:
        stmt = stmt.where(Movie.imdb >= imdb)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Movie.name.ilike(pattern),
                Movie.description.ilike(pattern),
                Star.name.ilike(pattern),
                Director.name.ilike(pattern),
            )
        )

    sort_map = {
        "price": Movie.price,
        "year": Movie.year,
        "imdb": Movie.imdb,
    }

    if sort_by in sort_map:
        column = sort_map[sort_by]
        stmt = stmt.order_by(desc(column) if order == "desc" else asc(column))

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


async def create_comment(
        db: AsyncSession,
        user_id: int,
        movie_id: int,
        text: str,
        parent_id: int | None = None,
):
    comment = MovieComment(
        user_id=user_id,
        movie_id=movie_id,
        text=text,
        parent_id=parent_id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def list_genres_with_count(db: AsyncSession):
    stmt = (
        select(
            Genre.id,
            Genre.name,
            func.count(movie_genres.c.movie_id).label("movie_count")
        )
        .join(movie_genres, movie_genres.c.genre_id == Genre.id, isouter=True)
        .group_by(Genre.id)
    )
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.all()]


async def get_movies_by_genre(db: AsyncSession, genre_id: int, offset: int = 0, limit: int = 20):
    stmt = (
        select(Movie)
        .join(movie_genres, movie_genres.c.movie_id == Movie.id)
        .where(movie_genres.c.genre_id == genre_id)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
