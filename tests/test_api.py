import pytest
import asyncio
from app.api import get_movies


@pytest.mark.asyncio
async def test_get_movies_returns_valid_structure():
    movies = await get_movies(page=1)
    assert isinstance(movies, list), "get_movies должен возвращать список"

    if movies:
        movie = movies[0]
        assert "id" in movie, "Отсутствует ключ 'id'"
        assert "title" in movie, "Отсутствует ключ 'title'"
        assert "description" in movie, "Отсутствует ключ 'description'"
        assert "poster_url" in movie, "Отсутствует ключ 'poster_url'"
