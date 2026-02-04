from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dependencies import get_current_user
from app.database.session import get_db
from app.modules.movies.schemas.movie_schema import (
    MovieListResponseSchema,
    MovieDetailSchema,
    GenreWithCountSchema,
)
from app.modules.movies.services.movie_service import MovieService
from app.modules.users.models.user import User

movies_router = APIRouter(prefix="/cinema", tags=["Movies"])


@movies_router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    summary="Get a paginated list of movies",
    description=(
        "<h3>This endpoint retrieves a paginated list of movies from the database. "
        "Clients can specify the `page` number and the number of items per page using `per_page`. "
        "The response includes details about the movies, total pages, and total items, "
        "along with links to the previous and next pages if applicable.</h3>"
    ),
    responses={
        404: {
            "description": "No movies found.",
            "content": {
                "application/json": {"example": {"detail": "No movies found."}}
            },
        }
    },
)
async def get_movie_list(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    year_from: int | None = Query(None, description="Filter by release year"),
    year_to: int | None = Query(None, description="Filter by release year"),
    imdb: float | None = Query(
        None, ge=0, le=10, description="Filter by minimum IMDb rating"
    ),
    sort_by: str | None = Query(None, enum=["price", "year", "imdb"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    search: str | None = Query(None, min_length=2),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:

    offset = (page - 1) * per_page

    service = MovieService(db)
    movies, total_items = await service.get_movies_list(
        offset=offset,
        limit=per_page,
        year_from=year_from,
        year_to=year_to,
        imdb=imdb,
        sort_by=sort_by,
        order=order,
        search=search,
    )

    total_pages = (total_items + per_page - 1) // per_page

    return MovieListResponseSchema(
        movies=movies,
        prev_page=(
            f"/cinema/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
        ),
        next_page=(
            f"/cinema/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@movies_router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    summary="Retrieve details of a single movie by ID",
    description="Get all information for a specific movie by its ID.",
    responses={
        404: {
            "description": "Movie not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found"}
                }
            },
        }
    },
)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    service = MovieService(db)
    movie = await service.get_movie_by_id(movie_id)
    return movie


@movies_router.post(
    "/movies/{movie_id}/like",
    summary="Like or dislike a movie",
    description="Add or update the current user's like for a movie.",
    responses={
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        404: {
            "description": "Movie not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found"}
                }
            },
        },
    },
)
async def like_movie(
    movie_id: int,
    like: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MovieService(db)
    movie_like = await service.like_movie(current_user.id, movie_id, like)
    return {"movie_id": movie_id, "value": movie_like.value}


@movies_router.post(
    "/movies/{movie_id}/favorite",
    summary="Add movie to favorites",
    description="Add the specified movie to the current user's favorites list.",
    responses={
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        404: {
            "description": "Movie not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found"}
                }
            },
        },
    },
)
async def add_favorite(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MovieService(db)
    favorite = await service.add_to_favorites(current_user.id, movie_id)
    return favorite


@movies_router.delete(
    "/movies/{movie_id}/favorite",
    summary="Remove movie from favorites",
    description="Remove the specified movie from the current user's favorites list.",
    responses={
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        404: {
            "description": "Movie not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found"}
                }
            },
        },
    },
)
async def remove_favorite(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MovieService(db)
    favorite = await service.remove_from_favorites(current_user.id, movie_id)
    return favorite


@movies_router.get(
    "/movies/favorites",
    summary="Get user's favorite movies",
    description="Retrieve a paginated list of movies added to the current user's favorites.",
    responses={
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        }
    },
)
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    year_from: int | None = Query(None),
    year_to: int | None = Query(None),
    imdb: float | None = Query(None, ge=0, le=10),
    sort_by: str | None = Query(None, pattern="^(price|year|imdb)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    search: str | None = Query(None),
):
    service = MovieService(db)
    favorites = await service.get_favorites(
        user_id=current_user.id,
        offset=offset,
        limit=limit,
        year_from=year_from,
        year_to=year_to,
        imdb=imdb,
        sort_by=sort_by,
        order=order,
        search=search,
    )
    return favorites


@movies_router.post(
    "/movies/{movie_id}/comments",
    summary="Add a comment to a movie",
    description="Create a new comment for a movie or reply to an existing comment.",
    responses={
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        404: {
            "description": "Movie or parent comment not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found"}
                }
            },
        },
    },
)
async def add_comment(
    movie_id: int,
    text: str,
    parent_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MovieService(db)
    return await service.add_comment(
        user_id=current_user.id,
        movie_id=movie_id,
        text=text,
        parent_id=parent_id,
    )


@movies_router.get(
    "/genres/",
    response_model=list[GenreWithCountSchema],
    summary="List movie genres",
    description="Retrieve all movie genres with the number of movies in each genre.",
    responses={
        404: {
            "description": "Genres not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Genres not found"}
                }
            },
        }
    },
)
async def list_genres(db: AsyncSession = Depends(get_db)):
    service = MovieService(db)
    return await service.list_genres()


@movies_router.get(
    "/genres/{genre_id}/movies",
    summary="List movies by genre",
    description="Retrieve a paginated list of movies belonging to a specific genre.",
    responses={
        404: {
            "description": "Genre not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre not found"}
                }
            },
        }
    },
)
async def movies_by_genre(
    genre_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    service = MovieService(db)
    offset = (page - 1) * per_page
    return await service.get_movies_by_genre(genre_id, offset, per_page)
