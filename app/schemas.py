from datetime import datetime
from decimal import Decimal
from typing import Optional, Annotated, Literal
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class GenreCreate(BaseModel):
    """
    Модель для создания и обновления жанров аниме.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., description="Название жанра")

class Genre(BaseModel):
    """
    Модель для ответа с данными аниме.
    Используется в GET-запросах.
    """
    id: int = Field(..., description="Уникальный идентификатор жанра")
    name: str = Field(..., description="Название жанра")

    model_config = ConfigDict(from_attributes=True)

class AnimeCreate(BaseModel):
    """
    Модель для создания и обновления аниме.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., min_length=3, max_length=50,description="Название аниме (3-50 символов)")
    year_release: int = Field(..., gt=1900, lt=datetime.today().year+2,description="Год выхода аниме")
    author: str = Field(..., min_length=3, max_length=50,description="Автор аниме")
    genre_ids: list[int] = Field(default=[], description="Список ID жанров")

class Anime(BaseModel):
    """
    Модель для ответа с данными аниме.
    Используется в GET-запросах.
    """
    id: int = Field(..., description="Уникальный идентификатор аниме")
    name: str = Field(..., description="Название аниме")
    year_release: int = Field(..., description="Год выхода аниме")
    author: str = Field(..., description="Автор аниме")
    is_active: bool = Field(default=True, description="Активно ли аниме")
    genres: list[Genre] = []

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    """
    Модель для ответа с user.
    Используется в GET-запросах.
    """
    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(min_length=8, max_length=64, description="Минимум 8 символов")

class User(BaseModel):
    """
    Модель для ответа с user.
    Используется в POST и PUT-запросах.
    """
    id: int
    email: EmailStr
    is_active: bool
    role: str = Field(default="user", description="Роль пользователя")

    model_config = ConfigDict(from_attributes=True)

WatchStatus = Literal["watching", "watched"]

class WatchlistUpdate(BaseModel):
    """
    Модель для ответа с watchlist.
    Используется в GET-запросах.
    """
    status: WatchStatus = Field(default="watched", pattern=r"^(watching|watched)$", description="Статус просмотра: watching или watched")


class WatchlistItem(BaseModel):
    """
    Модель для ответа с watchlist.
    Используется в POST и PUT-запросах.
    """
    status: WatchStatus
    anime: Anime

    model_config = ConfigDict(from_attributes=True)

class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Название аниме для добавления в список")


class ReviewCreate(BaseModel):
    """Используется в POST и PUT-запросах."""
    text: str = Field(..., min_length=5, max_length=1000, description="Текст отзыва")
    rating: int = Field(..., ge=1, le=10, description="Оценка от 1 до 10")

class ReviewOut(BaseModel):
    """Используется в GET-запросах."""
    id: int
    text: str
    rating: int
    user: User

    model_config = ConfigDict(from_attributes=True)

class AnimeDetail(Anime):
    """Модель для детального ответа об аниме со средним рейтингом."""
    average_rating: float = Field(default=0.0, description="Средний рейтинг на основе отзывов")

