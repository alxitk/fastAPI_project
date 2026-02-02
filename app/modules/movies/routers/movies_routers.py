from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.movies.schemas.movie_schema import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema, CertificationSchema, CertificationCreateSchema,
)
from app.modules.movies.services.movie_service import MovieService

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
                "application/json": {
                    "example": {"detail": "No movies found."}
                }
            },
        }
    }
)
async def get_movie_list(
        page: int = Query(1, ge=1, description="Page number (1-based index)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
        year_from: int | None = Query(None, description="Filter by release year"),
        year_to: int | None = Query(None, description="Filter by release year"),
        imdb: float | None = Query(None, ge=0, le=10, description="Filter by minimum IMDb rating"),
        sort_by: str | None = Query(None, enum=["price", "year", "imdb"]),
        order: str = Query("asc", enum=["asc", "desc"]),
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
    )

    total_pages = (total_items + per_page - 1) // per_page


    return MovieListResponseSchema(
        movies=movies,
        prev_page=f"/cinema/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/cinema/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )


@movies_router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    summary="Add a new movie",
    description=(
            "<h3>This endpoint allows clients to add a new movie to the database.</h3>"
    ),
    responses={
        201: {
            "description": "Movie created successfully.",
        },
        400: {
            "description": "Invalid input.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input data."}
                }
            },
        }
    },
    status_code=201
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    service = MovieService(db)
    movie = await service.create_movie(movie_data)
    return movie


@movies_router.post(
    "/certification/",
    response_model=CertificationSchema,
)
async def create_certification(
        certification_name: CertificationCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    service = MovieService(db)
    certification = await service.create_certification(certification_name)
    return certification


@movies_router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    service = MovieService(db)
    movie = await service.get_movie_by_id(movie_id)
    return movie