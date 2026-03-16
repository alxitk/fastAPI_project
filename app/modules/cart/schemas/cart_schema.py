from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator, Field


class CartMovieSchema(BaseModel):
    id: int
    name: str
    year: int
    price: Decimal
    genres: list[str] = Field(default_factory=list)

    @field_validator("genres", mode="before")
    @classmethod
    def extract_genre_names(cls, v):
        if v and isinstance(v[0], str):
            return v
        return [genre.name for genre in v]

    model_config = {"from_attributes": True}


class CartItemSchema(BaseModel):
    id: int
    movie_id: int
    movie: CartMovieSchema
    added_at: datetime

    model_config = {"from_attributes": True}


class CartSchema(BaseModel):
    id: int
    user_id: int
    items: list[CartItemSchema]

    model_config = {"from_attributes": True}


class CartItemAddSchema(BaseModel):
    movie_id: int


class UserCartSchema(BaseModel):
    id: int
    user_id: int
    items: list[CartItemSchema]

    model_config = {"from_attributes": True}
