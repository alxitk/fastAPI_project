from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.movies.crud.movies_crud import count_movies, get_movies, create_movie, create_certification
from app.modules.movies.models.movie_models import Movie, Certification, Genre, Star, Director
from app.modules.movies.schemas.movie_schema import MovieCreateSchema, MovieDetailSchema, CertificationCreateSchema


class MovieService:

    def __init__(
            self,
             db: AsyncSession,
             base_url: str = "http://localhost:8000",
    ):
        self._db = db
        self._base_url = base_url


    async def create_certification(self, certification_data: CertificationCreateSchema):
        stmt = select(Certification).where(Certification.name == certification_data.name)
        result = await self._db.execute(stmt)

        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Certification already exists")

        certification = await create_certification(
            db=self._db,
            name= certification_data.name,
        )

        return certification

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

        cert_stmt = select(Certification).where(
            Certification.id == movie_data.certification_id
        )
        result = await self._db.execute(cert_stmt)
        certification = result.scalar_one_or_none()

        if not certification:
            raise HTTPException(
                status_code=400,
                detail="Certification does not exist"
            )

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
            certification_id=movie_data.certification_id,
            genres=genres,
            stars=stars,
            directors=directors,
        )

        await self._db.commit()
        await self._db.refresh(movie)

        return MovieDetailSchema.from_orm(movie)
