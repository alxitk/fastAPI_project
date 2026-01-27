import decimal

from pydantic import BaseModel, Field

from app.modules.movies.schemas.examples.movies_schema_examples import director_schema_example, star_schema_example, \
    genre_schema_example, certification_schema_example


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
