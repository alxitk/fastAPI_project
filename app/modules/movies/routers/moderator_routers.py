from fastapi import APIRouter, Depends

from app.config.dependencies import get_current_moderator_user, get_movie_service
from app.modules.movies.models.movie_models import Genre, Star, Certification
from app.modules.movies.schemas.movie_schema import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    CertificationSchema,
    CertificationCreateSchema,
)
from app.modules.movies.services.movie_service import MovieService

moderator_router = APIRouter(prefix="/moderator", tags=["Moderator"])


@moderator_router.post(
    "/genres",
    dependencies=[Depends(get_current_moderator_user)],
    summary="Create a new genre",
    description=(
        "<h3>This endpoint allows moderators to create a new genre in the database.</h3>"
    ),
    responses={
        201: {
            "description": "Genre created successfully.",
        },
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
    },
    status_code=201,
)
async def create_genre(
    name: str,
    service: MovieService = Depends(get_movie_service),
) -> Genre:
    return await service.create_genre(name)


@moderator_router.put(
    "/genres/{genre_id}",
    dependencies=[Depends(get_current_moderator_user)],
    summary="Update an existing genre",
    description=(
        "<h3>This endpoint allows moderators to update an existing genre in the database.</h3>"
    ),
    responses={
        200: {
            "description": "Genre updated successfully.",
        },
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
        404: {
            "description": "Genre not found.",
            "content": {
                "application/json": {"example": {"detail": "Genre not found."}}
            },
        },
    },
    status_code=200,
)
async def update_genre(
    genre_id: int,
    name: str,
    service: MovieService = Depends(get_movie_service),
) -> Genre:
    return await service.update_genre(genre_id, name)


@moderator_router.delete(
    "/genres/{genre_id}",
    dependencies=[Depends(get_current_moderator_user)],
    summary="Delete a genre",
    description=(
        "<h3>This endpoint allows moderators to delete a genre from the database.</h3>"
    ),
    responses={
        200: {
            "description": "Genre deleted successfully.",
        },
        404: {
            "description": "Genre not found.",
            "content": {
                "application/json": {"example": {"detail": "Genre not found."}}
            },
        },
    },
    status_code=200,
)
async def delete_genre(
    genre_id: int,
    service: MovieService = Depends(get_movie_service),
) -> dict[str, str]:
    return await service.delete_genre(genre_id)


@moderator_router.post(
    "/movies/",
    dependencies=[Depends(get_current_moderator_user)],
    response_model=MovieDetailSchema,
    summary="Add a new movie",
    description=(
        "<h3>This endpoint allows moderators to add a new movie to the database.</h3>"
    ),
    responses={
        201: {
            "description": "Movie created successfully.",
        },
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
    },
    status_code=201,
)
async def create_movie(
    movie_data: MovieCreateSchema,
    service: MovieService = Depends(get_movie_service),
) -> MovieDetailSchema:
    movie = await service.create_movie(movie_data)
    return movie


@moderator_router.put(
    "/movies/{movie_id}",
    dependencies=[Depends(get_current_moderator_user)],
    response_model=MovieDetailSchema,
    summary="Update an existing movie",
    description=(
        "<h3>This endpoint allows moderators to update an existing movie in the database.</h3>"
    ),
    responses={
        200: {
            "description": "Movie updated successfully.",
        },
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
    },
    status_code=200,
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    service: MovieService = Depends(get_movie_service),
) -> MovieDetailSchema:
    movie = await service.update_movie(movie_id, movie_data)
    return MovieDetailSchema.model_validate(movie)


# async def delete_movie(db: AsyncSession, movie_id: int):
#     return {"detail": "Deletion disabled until purchases are implemented"}


@moderator_router.post(
    "/stars",
    dependencies=[Depends(get_current_moderator_user)],
    summary="Create a new star",
    description=(
        "<h3>This endpoint allows moderators to create a new star in the database.</h3>"
    ),
    responses={
        201: {
            "description": "Star created successfully.",
        },
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
    },
    status_code=201,
)
async def create_star(
    name: str,
    service: MovieService = Depends(get_movie_service),
) -> Star:
    return await service.create_star(name)


@moderator_router.put(
    "/stars/{star_id}",
    dependencies=[Depends(get_current_moderator_user)],
    summary="Update an existing star",
    description=(
        "<h3>This endpoint allows moderators to update an existing star in the database.</h3>"
    ),
    responses={
        200: {
            "description": "Star updated successfully.",
        },
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
        404: {
            "description": "Star not found.",
            "content": {"application/json": {"example": {"detail": "Star not found."}}},
        },
    },
    status_code=200,
)
async def update_star(
    star_id: int,
    name: str,
    service: MovieService = Depends(get_movie_service),
) -> Star:
    return await service.update_star(star_id, name)


@moderator_router.delete(
    "/stars/{star_id}",
    dependencies=[Depends(get_current_moderator_user)],
    summary="Delete a star",
    description=(
        "<h3>This endpoint allows moderators to delete a star from the database.</h3>"
    ),
    responses={
        200: {
            "description": "Star deleted successfully.",
        },
        404: {
            "description": "Star not found.",
            "content": {"application/json": {"example": {"detail": "Star not found."}}},
        },
    },
    status_code=200,
)
async def delete_star(
    star_id: int,
    service: MovieService = Depends(get_movie_service),
) -> dict[str, str]:
    return await service.delete_star(star_id)


@moderator_router.post(
    "/certification/",
    response_model=CertificationSchema,
    dependencies=[Depends(get_current_moderator_user)],
    summary="Create a new certification",
    description=(
        "<h3>This endpoint allows moderators to create a new certification in the database.</h3>"
    ),
    responses={
        201: {
            "description": "Certification created successfully.",
        },
        400: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
    },
    status_code=201,
)
async def create_certification(
    certification_name: CertificationCreateSchema,
    service: MovieService = Depends(get_movie_service),
) -> Certification:
    certification = await service.create_certification(certification_name)
    return certification
