from app.modules.movies.crud.movies_crud import count_movies, get_movies


async def get_movies_list(db, offset, limit):
    movies = await get_movies(db, offset, limit)
    total = await count_movies(db)
    return movies, total