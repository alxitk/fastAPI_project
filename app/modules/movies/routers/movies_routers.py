from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.movies.schemas.movie_schema import MovieListResponseSchema
from app.modules.movies.services.movie_service import get_movies_list

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
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:

    offset = (page - 1) * per_page

    movies, total_items = await get_movies_list(
        db=db,
        offset=offset,
        limit=per_page,
    )

    total_pages = (total_items + per_page - 1) // per_page

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=f"/cinema/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/cinema/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )