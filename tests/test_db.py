import os
import pytest
from app.database import Database


@pytest.fixture
def db():
    # Перед тестами удаляем старую БД
    if os.path.exists("videofetcher.db"):
        os.remove("videofetcher.db")
    return Database()


def test_add_and_remove_favorite(db):
    db.add_favorite(
        id_="123",
        title="Тестовый фильм",
        description="Описание тестового фильма",
        poster_url="http://example.com/poster.jpg",
        user_note="Это мой комментарий",
    )

    favorites = db.get_favorites()
    assert len(favorites) == 1, "Фильм не добавлен в избранное"
    assert favorites[0][0] == "123", "ID фильма не совпадает"
    assert favorites[0][1] == "Тестовый фильм", "Название не совпадает"
    assert favorites[0][4] == "Это мой комментарий", "Комментарий не совпадает"

    db.remove_favorite("123")
    favorites_after = db.get_favorites()
    assert len(favorites_after) == 0, "Фильм не был удалён из избранного"
