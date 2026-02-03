import decimal
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.modules.movies.schemas.examples.movies_schema_examples import director_schema_example, star_schema_example, \
    genre_schema_example, certification_schema_example, movie_list_response_schema_example, movie_list_item_example, \
    movie_create_schema_example, movie_detail_schema_example


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                genre_schema_example
            ]
        }
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                star_schema_example
            ]
        }
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                director_schema_example
            ]
        }
    }


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                certification_schema_example
            ]
        }
    }


class CertificationCreateSchema(BaseModel):
    name: str


class MovieCommentSchema(BaseModel):
    id: int
    text: str
    user_id: int
    parent_id: int | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1888)
    time: int
    imdb: float = Field(..., ge=0, le=10)
    votes: int
    description: str = Field(..., max_length=255)
    price: decimal.Decimal = Field(..., max_digits=10, decimal_places=2)

    model_config = {
        "from_attributes": True
    }


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    price: Decimal

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_list_item_example
            ]
        }
    }


class MovieDetailSchema(MovieBaseSchema):
    genres: list[GenreSchema]
    stars: list[StarSchema]
    directors: list[DirectorSchema]
    certification: CertificationSchema | None

    comments: list[MovieCommentSchema] = []

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_detail_schema_example
            ]
        }
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_list_response_schema_example
            ]
        }
    }


class MovieCreateSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    description: str
    certification_id: int
    price: Decimal
    genres: list[str]
    stars: list[str]
    directors: list[str]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_create_schema_example
            ]
        }
    }


class GenreWithCountSchema(BaseModel):
    id: int
    name: str
    movie_count: int

    model_config = {
        "from_attributes": True
    }
