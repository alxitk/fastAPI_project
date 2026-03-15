"""
Cinema API — test data seed script.

Populates the database with realistic fixtures so a mentor or reviewer
can exercise every part of the API without manual data entry.

Credentials created by this script
───────────────────────────────────
  admin@cinema.local      / Admin123!   (ADMIN)
  moderator@cinema.local  / Moder123!   (MODERATOR)
  user@cinema.local       / User1234!   (USER)

Usage
─────
    python seed_data.py

The script is idempotent: running it more than once will skip rows that
already exist rather than raising duplicate-key errors.
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.database.session import async_session_local

# Import ALL models so SQLAlchemy can resolve every relationship before the
# first query is compiled.  Order matters: independent models first.
import app.modules.users.models.token  # noqa: F401
from app.modules.users.models.user import User, UserGroupModel, UserProfileModel
from app.modules.users.models.enums import GenderEnum, UserGroupEnum
import app.modules.cart.models.cart_models  # noqa: F401
import app.modules.order.models.order_models  # noqa: F401
import app.modules.payment.models.payment_models  # noqa: F401
from app.modules.movies.models.movie_models import (
    Certification,
    Director,
    Genre,
    Movie,
    Star,
)

# ── Fixture data ──────────────────────────────────────────────────────────────

USERS = [
    {
        "email": "admin@cinema.local",
        "password": "Admin123!",
        "is_active": True,
        "group": UserGroupEnum.ADMIN,
        "profile": {
            "first_name": "Alice",
            "last_name": "Admin",
            "gender": GenderEnum.WOMAN,
            "info": "Platform administrator account.",
        },
    },
    {
        "email": "moderator@cinema.local",
        "password": "Moder123!",
        "is_active": True,
        "group": UserGroupEnum.MODERATOR,
        "profile": {
            "first_name": "Bob",
            "last_name": "Moderator",
            "gender": GenderEnum.MAN,
            "info": "Content moderator account.",
        },
    },
    {
        "email": "user@cinema.local",
        "password": "User1234!",
        "is_active": True,
        "group": UserGroupEnum.USER,
        "profile": {
            "first_name": "Carol",
            "last_name": "User",
            "gender": GenderEnum.WOMAN,
            "info": "Regular cinema-fan account.",
        },
    },
]

CERTIFICATIONS = ["G", "PG", "PG-13", "R", "NC-17"]

GENRES = [
    "Action",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Horror",
    "Romance",
    "Sci-Fi",
    "Thriller",
]

DIRECTORS = [
    "Christopher Nolan",
    "Denis Villeneuve",
    "Quentin Tarantino",
    "Ridley Scott",
    "Steven Spielberg",
]

STARS = [
    "Anne Hathaway",
    "Brad Pitt",
    "Cillian Murphy",
    "Leonardo DiCaprio",
    "Matthew McConaughey",
    "Meryl Streep",
    "Scarlett Johansson",
    "Timothée Chalamet",
    "Tom Hanks",
    "Zendaya",
]

# Each entry maps to a real movie.  Stars/genres are test fixtures so they
# may not perfectly reflect real cast lists.
MOVIES = [
    {
        "name": "Inception",
        "year": 2010,
        "time": 148,
        "imdb": 8.8,
        "votes": 2_400_000,
        "meta_score": 74.0,
        "gross": 836_836_967.0,
        "description": (
            "A thief who steals corporate secrets through dream-sharing technology "
            "is given the inverse task of planting an idea into the mind of a C.E.O."
        ),
        "price": Decimal("9.99"),
        "certification": "PG-13",
        "genres": ["Action", "Sci-Fi", "Thriller"],
        "directors": ["Christopher Nolan"],
        "stars": ["Leonardo DiCaprio", "Cillian Murphy"],
    },
    {
        "name": "Oppenheimer",
        "year": 2023,
        "time": 180,
        "imdb": 8.9,
        "votes": 950_000,
        "meta_score": 88.0,
        "gross": 952_300_000.0,
        "description": (
            "The story of J. Robert Oppenheimer and his role in the development "
            "of the atomic bomb during World War II."
        ),
        "price": Decimal("12.99"),
        "certification": "R",
        "genres": ["Drama", "Thriller"],
        "directors": ["Christopher Nolan"],
        "stars": ["Cillian Murphy"],
    },
    {
        "name": "Interstellar",
        "year": 2014,
        "time": 169,
        "imdb": 8.7,
        "votes": 1_900_000,
        "meta_score": 74.0,
        "gross": 701_728_960.0,
        "description": (
            "A team of explorers travel through a wormhole in space in an "
            "attempt to ensure humanity's survival."
        ),
        "price": Decimal("9.99"),
        "certification": "PG-13",
        "genres": ["Sci-Fi", "Drama"],
        "directors": ["Christopher Nolan"],
        "stars": ["Matthew McConaughey", "Anne Hathaway"],
    },
    {
        "name": "Dune: Part Two",
        "year": 2024,
        "time": 166,
        "imdb": 8.5,
        "votes": 620_000,
        "meta_score": 90.0,
        "gross": 711_000_000.0,
        "description": (
            "Paul Atreides unites with Chani and the Fremen while on a warpath "
            "of revenge against the conspirators who destroyed his family."
        ),
        "price": Decimal("14.99"),
        "certification": "PG-13",
        "genres": ["Sci-Fi", "Action", "Drama"],
        "directors": ["Denis Villeneuve"],
        "stars": ["Timothée Chalamet", "Zendaya"],
    },
    {
        "name": "Blade Runner 2049",
        "year": 2017,
        "time": 164,
        "imdb": 8.0,
        "votes": 580_000,
        "meta_score": 81.0,
        "gross": 92_054_159.0,
        "description": (
            "A young blade runner discovers a long-buried secret that has the "
            "potential to plunge what's left of society into chaos."
        ),
        "price": Decimal("8.99"),
        "certification": "R",
        "genres": ["Sci-Fi", "Thriller", "Drama"],
        "directors": ["Denis Villeneuve"],
        "stars": ["Zendaya"],
    },
    {
        "name": "Pulp Fiction",
        "year": 1994,
        "time": 154,
        "imdb": 8.9,
        "votes": 2_100_000,
        "meta_score": 94.0,
        "gross": 214_179_088.0,
        "description": (
            "The lives of two mob hitmen, a boxer, a gangster and his wife "
            "intertwine in four tales of violence and redemption."
        ),
        "price": Decimal("7.99"),
        "certification": "R",
        "genres": ["Crime", "Drama", "Thriller"],
        "directors": ["Quentin Tarantino"],
        "stars": ["Brad Pitt", "Scarlett Johansson"],
    },
    {
        "name": "Once Upon a Time in Hollywood",
        "year": 2019,
        "time": 161,
        "imdb": 7.6,
        "votes": 780_000,
        "meta_score": 83.0,
        "gross": 142_502_728.0,
        "description": (
            "A faded television actor and his stunt double strive to achieve "
            "fame in the final years of Hollywood's Golden Age in 1969 Los Angeles."
        ),
        "price": Decimal("8.99"),
        "certification": "R",
        "genres": ["Comedy", "Drama", "Crime"],
        "directors": ["Quentin Tarantino"],
        "stars": ["Brad Pitt", "Leonardo DiCaprio"],
    },
    {
        "name": "Gladiator",
        "year": 2000,
        "time": 155,
        "imdb": 8.5,
        "votes": 1_500_000,
        "meta_score": 67.0,
        "gross": 457_640_427.0,
        "description": (
            "A former Roman general sets out to exact vengeance against the corrupt "
            "emperor who murdered his family and sold him into slavery."
        ),
        "price": Decimal("7.99"),
        "certification": "R",
        "genres": ["Action", "Drama"],
        "directors": ["Ridley Scott"],
        "stars": ["Scarlett Johansson", "Brad Pitt"],
    },
    {
        "name": "Saving Private Ryan",
        "year": 1998,
        "time": 169,
        "imdb": 8.6,
        "votes": 1_400_000,
        "meta_score": 91.0,
        "gross": 482_349_603.0,
        "description": (
            "Following the Normandy Landings, a group of U.S. soldiers go behind "
            "enemy lines to retrieve a paratrooper whose brothers have been killed "
            "in action."
        ),
        "price": Decimal("7.99"),
        "certification": "R",
        "genres": ["Action", "Drama"],
        "directors": ["Steven Spielberg"],
        "stars": ["Tom Hanks"],
    },
    {
        "name": "Schindler's List",
        "year": 1993,
        "time": 195,
        "imdb": 9.0,
        "votes": 1_350_000,
        "meta_score": 94.0,
        "gross": 321_365_567.0,
        "description": (
            "In German-occupied Poland during World War II, industrialist Oskar "
            "Schindler gradually becomes concerned for his Jewish workforce after "
            "witnessing their persecution by the Nazis."
        ),
        "price": Decimal("6.99"),
        "certification": "R",
        "genres": ["Drama", "Crime"],
        "directors": ["Steven Spielberg"],
        "stars": ["Meryl Streep", "Anne Hathaway"],
    },
]


# ── Seed logic ────────────────────────────────────────────────────────────────


async def _get_or_create(session, model, **kwargs):
    """Return existing row or create and flush a new one."""
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalar_one_or_none()
    if instance is None:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
        return instance, True
    return instance, False


async def seed() -> None:
    async with async_session_local() as session:

        # 1. User groups ──────────────────────────────────────────────────────
        print("── User groups ──")
        group_map: dict[UserGroupEnum, UserGroupModel] = {}
        for enum_val in UserGroupEnum:
            group, created = await _get_or_create(
                session, UserGroupModel, name=enum_val
            )
            group_map[enum_val] = group
            if created:
                print(f"  + {enum_val.value}")
            else:
                print(f"  = {enum_val.value} (exists)")

        # 2. Users ────────────────────────────────────────────────────────────
        print("\n── Users ──")
        for ud in USERS:
            result = await session.execute(
                select(User).where(User.email == ud["email"])
            )
            if result.scalar_one_or_none():
                print(f"  = {ud['email']} (exists)")
                continue

            user = User(
                email=ud["email"],
                is_active=ud["is_active"],
                group_id=group_map[ud["group"]].id,
            )
            user.set_password(ud["password"])
            session.add(user)
            await session.flush()

            profile = UserProfileModel(user_id=user.id, **ud["profile"])
            session.add(profile)
            print(f"  + {ud['email']}  [{ud['group'].value}]")

        # 3. Certifications ───────────────────────────────────────────────────
        print("\n── Certifications ──")
        cert_map: dict[str, Certification] = {}
        for name in CERTIFICATIONS:
            cert, created = await _get_or_create(session, Certification, name=name)
            cert_map[name] = cert
            print(f"  {'+' if created else '='} {name}")

        # 4. Genres ───────────────────────────────────────────────────────────
        print("\n── Genres ──")
        genre_map: dict[str, Genre] = {}
        for name in GENRES:
            genre, created = await _get_or_create(session, Genre, name=name)
            genre_map[name] = genre
            print(f"  {'+' if created else '='} {name}")

        # 5. Directors ────────────────────────────────────────────────────────
        print("\n── Directors ──")
        director_map: dict[str, Director] = {}
        for name in DIRECTORS:
            director, created = await _get_or_create(session, Director, name=name)
            director_map[name] = director
            print(f"  {'+' if created else '='} {name}")

        # 6. Stars ────────────────────────────────────────────────────────────
        print("\n── Stars ──")
        star_map: dict[str, Star] = {}
        for name in STARS:
            star, created = await _get_or_create(session, Star, name=name)
            star_map[name] = star
            print(f"  {'+' if created else '='} {name}")

        # 7. Movies ───────────────────────────────────────────────────────────
        print("\n── Movies ──")
        for md in MOVIES:
            result = await session.execute(
                select(Movie).where(
                    Movie.name == md["name"],
                    Movie.year == md["year"],
                )
            )
            if result.scalar_one_or_none():
                print(f"  = {md['name']} ({md['year']}) (exists)")
                continue

            movie = Movie(
                name=md["name"],
                year=md["year"],
                time=md["time"],
                imdb=md["imdb"],
                votes=md["votes"],
                meta_score=md.get("meta_score"),
                gross=md.get("gross"),
                description=md["description"],
                price=md["price"],
                certification_id=cert_map[md["certification"]].id,
            )
            movie.genres = [genre_map[g] for g in md["genres"]]
            movie.directors = [director_map[d] for d in md["directors"]]
            movie.stars = [star_map[s] for s in md["stars"]]
            session.add(movie)
            print(f"  + {md['name']} ({md['year']})")

        await session.commit()
        print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
