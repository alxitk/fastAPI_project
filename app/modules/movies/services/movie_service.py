from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.movies.crud.movies_crud import count_movies, get_movies, create_movie
from app.modules.movies.models.movie_models import Movie, Certification, Genre, Star, Director
from app.modules.movies.schemas.movie_schema import MovieCreateSchema, MovieDetailSchema


class MovieService:

    def __init__(
            self,
             db: AsyncSession,
             base_url: str = "http://localhost:8000",
    ):
        self._db = db
        self._base_url = base_url


    async def get_movies_list(self, offset, limit):
        movies = await get_movies(self._db, offset, limit)
        total = await count_movies(self._db)
        return movies, total

    async def create_movie(self, movie_data: MovieCreateSchema):
        stmt = select(Movie).where(
            Movie.name == movie_data.name,
            Movie.year == movie_data.year,
            Movie.time == movie_data.time,
        )
        result = await self._db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Movie already exists")

        stmt = select(Certification).where(
            Certification.name == movie_data.certification.name
        )
        result = await self._db.execute(stmt)
        certification = result.scalars().first()
        if not certification:
            certification = Certification(name=movie_data.certification.name)
            self._db.add(certification)
            await self._db.flush()

        genres = []
        for name in movie_data.genres:
            stmt = select(Genre).where(Genre.name == name)
            result = await self._db.execute(stmt)
            genre = result.scalars().first()
            if not genre:
                genre = Genre(name=name)
                self._db.add(genre)
                await self._db.flush()
            genres.append(genre)

        stars = []
        for name in movie_data.stars:
            stmt = select(Star).where(Star.name == name)
            result = await self._db.execute(stmt)
            star = result.scalars().first()
            if not star:
                star = Star(name=name)
                self._db.add(star)
                await self._db.flush()
            stars.append(star)

        directors = []
        for name in movie_data.directors:
            stmt = select(Director).where(Director.name == name)
            result = await self._db.execute(stmt)
            director = result.scalars().first()
            if not director:
                director = Director(name=name)
                self._db.add(director)
                await self._db.flush()
            directors.append(director)


        movie = await create_movie(
            self._db,
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            description=movie_data.description,
            price=movie_data.price,
            certification=certification,
            genres=genres,
            stars=stars,
            directors=directors,
        )

        await self._db.commit()
        await self._db.refresh(movie)

        return MovieDetailSchema.from_orm(movie)
