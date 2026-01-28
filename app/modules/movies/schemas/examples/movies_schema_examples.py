genre_schema_example = {
    "id": 1,
    "genre": "Comedy"
}

star_schema_example = {
    "id": 1,
    "name": "Brad Pitt"
}

director_schema_example = {
    "id": 1,
    "name": "GuyRichie"
}

certification_schema_example = {
    "id": 1,
    "name": "PG-13"
}

movie_list_item_example = {
    "id": 1,
    "name": "Inception",
    "year": 2010,
    "imdb": 8.8,
    "price": "9.99"
}

movie_list_response_schema_example = {
    "movies": [
        movie_list_item_example
    ],
    "prev_page": "/theater/movies/?page=1&per_page=1",
    "next_page": "/theater/movies/?page=3&per_page=1",
    "total_pages": 9933,
    "total_items": 9933
}

movie_create_schema_example = {
    "name": "New Movie",
    "year": 2025,
    "time": 120,
    "description": "An amazing movie.",
    "price": 49.99,
    "genres": ["Action", "Adventure"],
    "stars": ["John Doe", "Jane Doe"],
    "directors": ["John Doe", "Jane Doe"]
}
