import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Integer,
    String,
    Float,
    Text,
    Numeric,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.modules.cart.models.cart_models import CartItem
from app.modules.movies.models.associations import (
    movie_genres,
    movie_stars,
    movie_directors,
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
        lazy="selectin",
    )


class Star(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_stars,
        back_populates="stars",
        lazy="selectin",
    )


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_directors,
        back_populates="directors",
        lazy="selectin",
    )


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        "Movie",
        back_populates="certification",
        lazy="selectin",
    )


class Movie(Base):
    __tablename__ = "movies"

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uq_movie_name_year_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[float] = mapped_column(Float, nullable=True)
    gross: Mapped[float] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    likes = relationship("MovieLike", back_populates="movie")
    favorites = relationship("MovieFavorites", back_populates="movie")
    comments = relationship(
        "MovieComment",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    certification: Mapped[Certification] = relationship(
        "Certification",
        back_populates="movies",
    )
    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id", ondelete="RESTRICT"), nullable=False
    )

    genres: Mapped[list[Genre]] = relationship(
        secondary=movie_genres,
        back_populates="movies",
        lazy="selectin",
    )

    stars: Mapped[list[Star]] = relationship(
        secondary=movie_stars,
        back_populates="movies",
        lazy="selectin",
    )

    directors: Mapped[list[Director]] = relationship(
        secondary=movie_directors,
        back_populates="movies",
        lazy="selectin",
    )
    cart_items : Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="movie",
    )


class MovieLike(Base):
    __tablename__ = "movie_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))
    value: Mapped[int] = mapped_column(default=1)  # 1 = like, -1 = dislike

    user = relationship("User", back_populates="likes")
    movie = relationship("Movie", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_like"),
    )


class MovieFavorites(Base):
    __tablename__ = "movie_favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))

    user = relationship("User", back_populates="favorites")
    movie = relationship("Movie", back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "movie_id", name="uq_user_favorite"),)


class MovieComment(Base):
    __tablename__ = "movie_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("movie_comments.id", ondelete="CASCADE"),
        nullable=True,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user = relationship("User", back_populates="movie_comments")
    movie = relationship("Movie", back_populates="comments")

    parent = relationship(
        "MovieComment",
        remote_side=[id],
        foreign_keys=[parent_id],
        back_populates="replies",
    )

    replies = relationship(
        "MovieComment",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )
