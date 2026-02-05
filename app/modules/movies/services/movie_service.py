from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.dependencies import get_email_sender
from app.modules.movies.crud.genre_crud import (
    create_genre,
    get_genre,
    update_genre,
    delete_genre,
)
from app.modules.movies.crud.movies_crud import (
    count_movies,
    get_movies,
    create_movie,
    create_certification,
    add_movie_like,
    get_favorite,
    create_favorite,
    delete_favorite,
    list_favorites,
    create_comment,
    list_genres_with_count,
    get_movies_by_genre,
    get_movie_detail,
    update_movie,
)
from app.modules.movies.crud.star_crud import (
    create_star,
    get_star_list,
    get_star,
    update_star,
    delete_star,
    get_star_by_name,
    list_stars_with_count,
    get_movies_by_star,
)
from app.modules.movies.models.movie_models import (
    Movie,
    Certification,
    Genre,
    Star,
    Director,
    MovieComment,
)
from app.modules.movies.schemas.movie_schema import (
    MovieCreateSchema,
    MovieDetailSchema,
    CertificationCreateSchema,
    MovieUpdateSchema,
    StarWithCountSchema,
)
from app.modules.movies.services.comment_notification_service import (
    CommentNotificationService,
)


class MovieService:
    """Service layer for movie-related business logic."""

    def __init__(
        self,
        db: AsyncSession,
        base_url: str = "http://localhost:8000",
    ):
        self._db = db
        self._base_url = base_url

    async def _get_or_create_entity(self, model, name: str):
        """Get model or create new one by name."""
        stmt = select(model).where(model.name == name)
        result = await self._db.execute(stmt)
        entity = result.scalars().first()

        if not entity:
            entity = model(name=name)
            self._db.add(entity)
            await self._db.flush()

        return entity

    async def create_certification(self, certification_data: CertificationCreateSchema):
        """Create a new certification."""
        stmt = select(Certification).where(
            Certification.name == certification_data.name
        )
        result = await self._db.execute(stmt)

        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Certification already exists")

        certification = await create_certification(
            db=self._db,
            name=certification_data.name,
        )

        return certification

    async def get_movies_list(
        self,
        offset: int = 0,
        limit: int = 100,
        year_from: int | None = None,
        year_to: int | None = None,
        imdb: float | None = None,
        sort_by: str | None = None,
        order: str = "asc",
        search: str | None = None,
    ):
        """Get paginated list of movies with filters."""
        movies = await get_movies(
            db=self._db,
            offset=offset,
            limit=limit,
            year_from=year_from,
            year_to=year_to,
            imdb=imdb,
            sort_by=sort_by,
            order=order,
            search=search,
        )
        total = await count_movies(
            self._db,
            year_from=year_from,
            year_to=year_to,
            imdb=imdb,
            search=search,
        )
        return movies, total

    async def create_movie(self, movie_data: MovieCreateSchema):
        """Create a new movie with genres, stars, and directors."""
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
            raise HTTPException(status_code=400, detail="Certification does not exist")

        genres = [
            await self._get_or_create_entity(Genre, name) for name in movie_data.genres
        ]
        stars = [
            await self._get_or_create_entity(Star, name) for name in movie_data.stars
        ]
        directors = [
            await self._get_or_create_entity(Director, name)
            for name in movie_data.directors
        ]

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

    async def update_movie(self, movie_id: int, data: MovieUpdateSchema):
        """Update an existing movie."""
        movie = await update_movie(self._db, movie_id, data)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie

    async def get_movie_by_id(self, movie_id: int):
        """Get movie details by ID."""
        movie = await get_movie_detail(self._db, movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie

    async def like_movie(self, user_id: int, movie_id: int, like: bool):
        """Add like or dislike to a movie."""
        await self.get_movie_by_id(movie_id)
        value = 1 if like else -1
        return await add_movie_like(self._db, user_id, movie_id, value)

    async def add_to_favorites(self, user_id: int, movie_id: int):
        """Add movie to user's favorites."""
        await self.get_movie_by_id(movie_id)
        exists = await get_favorite(self._db, user_id, movie_id)
        if exists:
            return exists
        return await create_favorite(self._db, user_id, movie_id)

    async def remove_from_favorites(self, user_id: int, movie_id: int):
        """Remove movie from user's favorites."""
        return await delete_favorite(self._db, user_id, movie_id)

    async def get_favorites(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        year_from: int | None = None,
        year_to: int | None = None,
        imdb: float | None = None,
        sort_by: str | None = None,
        order: str = "asc",
        search: str | None = None,
    ):
        """Get user's favorite movies with filters."""
        return await list_favorites(
            self._db,
            user_id,
            offset=offset,
            limit=limit,
            year_from=year_from,
            year_to=year_to,
            imdb=imdb,
            sort_by=sort_by,
            order=order,
            search=search,
        )

    async def add_comment(
        self,
        user_id: int,
        movie_id: int,
        text: str,
        parent_id: int | None = None,
    ):
        """Add a comment to a movie and notify parent comment author if it's a reply."""
        movie = await self.get_movie_by_id(movie_id)

        comment = await create_comment(
            self._db,
            user_id=user_id,
            movie_id=movie_id,
            text=text,
            parent_id=parent_id,
        )

        if parent_id:
            stmt = (
                select(MovieComment)
                .options(selectinload(MovieComment.user))
                .where(MovieComment.id == parent_id)
            )
            result = await self._db.execute(stmt)
            parent_comment = result.scalar_one_or_none()

            if parent_comment and parent_comment.user_id != user_id:
                notification_service = CommentNotificationService(
                    email_sender=get_email_sender()
                )
                await notification_service.notify_reply(
                    parent_user_email=parent_comment.user.email,
                    reply_text=text,
                    movie_name=movie.name,
                )

        return comment

    async def create_genre(self, name: str) -> Genre:
        """Create a new genre."""
        return await create_genre(self._db, name)

    async def list_genres(self) -> list[Genre]:
        """Get list of all genres with movie counts."""
        return await list_genres_with_count(self._db)

    async def get_genre(self, genre_id: int) -> Genre:
        """Get genre by ID."""
        genre = await get_genre(self._db, genre_id)
        if not genre:
            raise HTTPException(status_code=404, detail="Genre not found")
        return genre

    async def update_genre(self, genre_id: int, name: str) -> Genre:
        """Update genre name."""
        genre = await update_genre(self._db, genre_id, name)
        if not genre:
            raise HTTPException(status_code=404, detail="Genre not found")
        return genre

    async def delete_genre(self, genre_id: int) -> dict:
        """Delete a genre."""
        success = await delete_genre(self._db, genre_id)
        if not success:
            raise HTTPException(status_code=404, detail="Genre not found")
        return {"detail": "Genre deleted"}

    async def get_movies_by_genre(
        self, genre_id: int, offset: int = 0, limit: int = 20
    ):
        """Get movies filtered by genre."""
        return await get_movies_by_genre(self._db, genre_id, offset, limit)

    async def create_star(self, name: str) -> Star:
        """Create a new star."""
        existing = await get_star_by_name(db=self._db, name=name)
        if existing:
            raise HTTPException(status_code=400, detail="Star already exists")
        return await create_star(self._db, name)

    async def list_stars(self) -> list[Star]:
        """Get list of all stars."""
        return await get_star_list(self._db)

    async def list_stars_with_count(self) -> list[StarWithCountSchema]:
        """Get list of stars with movie counts."""
        rows = await list_stars_with_count(self._db)
        return [StarWithCountSchema(**row) for row in rows]

    async def get_star(self, star_id: int) -> Star:
        """Get star by ID."""
        star = await get_star(self._db, star_id)
        if not star:
            raise HTTPException(status_code=404, detail="Star not found")
        return star

    async def update_star(self, star_id: int, name: str) -> Star:
        """Update star name."""
        star = await update_star(self._db, star_id, name)
        if not star:
            raise HTTPException(status_code=404, detail="Star not found")
        return star

    async def delete_star(self, star_id: int) -> dict:
        """Delete a star."""
        success = await delete_star(self._db, star_id)
        if not success:
            raise HTTPException(status_code=404, detail="Star not found")
        return {"detail": "Star deleted"}

    async def get_movies_by_star(self, star_id: int, offset: int = 0, limit: int = 20):
        """Get movies filtered by star."""
        return await get_movies_by_star(self._db, star_id, offset, limit)
