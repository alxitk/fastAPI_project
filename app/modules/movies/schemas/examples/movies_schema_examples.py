genre_schema_example = {"id": 1, "genre": "Comedy"}

star_schema_example = {"id": 1, "name": "Brad Pitt"}

director_schema_example = {"id": 1, "name": "GuyRichie"}

certification_schema_example = {"id": 1, "name": "PG-13"}

movie_list_item_example = {
    "id": 1,
    "name": "Inception",
    "year": 2010,
    "imdb": 8.8,
    "price": "9.99",
}

movie_list_response_schema_example = {
    "movies": [movie_list_item_example],
    "prev_page": "/theater/movies/?page=1&per_page=1",
    "next_page": "/theater/movies/?page=3&per_page=1",
    "total_pages": 9933,
    "total_items": 9933,
}

movie_create_schema_example = {
    "name": "New Movie",
    "year": 2025,
    "time": 120,
    "imdb": 8.8,
    "votes": 124532,
    "description": "An amazing movie.",
    "certification_id": 12,
    "price": 49.99,
    "genres": ["Action", "Adventure"],
    "stars": ["John Doe", "Jane Doe"],
    "directors": ["John Doe", "Jane Doe"],
}

movie_detail_schema_example = {
    "name": "New Movie",
    "year": 2025,
    "time": 120,
    "imdb": 8.8,
    "votes": 124532,
    "description": "Some Description",
    "price": 49.99,
    "genres": [genre_schema_example],
    "stars": [star_schema_example],
    "directors": [director_schema_example],
    "certification": certification_schema_example,
    "comments": [
        {
            "id": 1,
            "text": "Some text",
            "user_id": 2,
            "parent_id": None,
            "created_at": "2025-01-15T10:30:00",
        }
    ],
}

movie_comment_schema_example = {
    "id": 12,
    "text": "Great movie!",
    "user_id": 3,
    "parent_id": None,
    "created_at": "2024-05-01T14:32:10",
}

genre_with_count_schema_example = {"id": 1, "name": "Action", "movie_count": 15}

star_with_count_schema_example = {
    "id": 2,
    "name": "Leonardo DiCaprio",
    "movie_count": 7,
}
