from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_current_us
from app.db_depends import get_async_db
from app.models.anime import Anime as AnimeModel
from app.models.genre import Genre as GenreModel
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel
from app.schemas import AnimeCreate, AnimeDetail, Anime as AnimeSchema
import json
from app.redis_client import redis_client, clear_anime_cache

router = APIRouter(prefix="/animes", tags=["animes"])

import json
from app.redis_client import redis_client, clear_anime_cache

@router.get("", response_model=list[AnimeSchema], status_code=status.HTTP_200_OK)
async def get_all_anime(db: AsyncSession = Depends(get_async_db)):
    # 1. Пробуем достать из Redis
    cached_data = await redis_client.get("animes:all")
    if cached_data is not None:
        return json.loads(cached_data)

    # 2. Если в кэше нет — берём из БД
    stmt = select(AnimeModel).where(AnimeModel.is_active == True).order_by(AnimeModel.id)
    result = await db.scalars(stmt)
    animes = result.all()

    # 3. Сериализуем через Pydantic и кладём в Redis на 300 секунд
    serialized = [AnimeSchema.model_validate(a).model_dump() for a in animes]
    await redis_client.set("animes:all", json.dumps(serialized), ex=300)
    return serialized


@router.get("/{id}", response_model=AnimeDetail, status_code=status.HTTP_200_OK)
async def get_anime_on_id(id: int, db: AsyncSession = Depends(get_async_db)):
    cache_key = f"animes:{id}"
    cached_anime = await redis_client.get(cache_key)
    if cached_anime is not None:
        return json.loads(cached_anime)

    stmt = select(AnimeModel).where(AnimeModel.id == id, AnimeModel.is_active == True)
    anime = await db.scalar(stmt)
    if anime is None:
        raise HTTPException(status_code=404, detail="Anime not found!")

    rating_stmt = select(func.avg(ReviewModel.rating)).where(
        ReviewModel.anime_id == anime.id,
        ReviewModel.is_active == True,
    )
    avg_rating = await db.scalar(rating_stmt)
    anime.average_rating = round(float(avg_rating), 2) if avg_rating is not None else 0.0

    serialized = AnimeDetail.model_validate(anime).model_dump()
    await redis_client.set(cache_key, json.dumps(serialized), ex=300)
    return serialized


@router.post("", response_model=AnimeSchema, status_code=status.HTTP_201_CREATED)
async def create_anime(anime: AnimeCreate, db: AsyncSession = Depends(get_async_db),  current_user: UserModel = Depends(get_current_admin)):
    # 1. Проверяем дубликат названия аниме
    anime_stmt = select(AnimeModel).where(AnimeModel.name == anime.name)
    if await db.scalar(anime_stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Уже создано!")

    # 2. Проверяем существование всех переданных жанров
    genres = []
    if anime.genre_ids:
        unique_ids = set(anime.genre_ids)
        genres_stmt = select(GenreModel).where(GenreModel.id.in_(unique_ids), GenreModel.is_active == True)
        genres_result = await db.scalars(genres_stmt)
        genres = list(genres_result.all())
        if len(genres) != len(unique_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Один или несколько жанров не существуют!")

    # 3. Создаём аниме и привязываем жанры
    anime_data = anime.model_dump(exclude={"genre_ids"})
    db_anime = AnimeModel(**anime_data, genres=genres)
    db.add(db_anime)
    await db.commit()
    await db.refresh(db_anime)
    return db_anime



@router.get("", response_model=list[AnimeSchema], status_code=status.HTTP_200_OK)
async def get_all_anime(db: AsyncSession = Depends(get_async_db)):
    cached_data = await redis_client.get("animes:all")
    if cached_data is not None:
        return json.loads(cached_data)

    stmt = select(AnimeModel).where(AnimeModel.is_active == True).order_by(AnimeModel.id)
    result = await db.scalars(stmt)
    animes = result.all()

    serialized = [AnimeSchema.model_validate(a).model_dump() for a in animes]
    await redis_client.set("animes:all", json.dumps(serialized), ex=300)
    return serialized


@router.put("/{anime_id}", response_model=AnimeSchema, status_code=status.HTTP_200_OK)
async def change_anime_on_id(anime_id: int, anime: AnimeCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_admin)):
    stmt = select(AnimeModel).where(AnimeModel.id == anime_id, AnimeModel.is_active == True)
    db_anime = await db.scalar(stmt)
    if db_anime is None:
        raise HTTPException(status_code=404, detail="Anime not found!")

    # Проверяем и обновляем жанры, если переданы
    if anime.genre_ids is not None:
        unique_ids = set(anime.genre_ids)
        genres_stmt = select(GenreModel).where(GenreModel.id.in_(unique_ids), GenreModel.is_active == True)
        genres = list((await db.scalars(genres_stmt)).all())
        if len(genres) != len(unique_ids):
            raise HTTPException(status_code=404, detail="Один или несколько жанров не существуют!")
        db_anime.genres = genres

    # Обновляем остальные поля (без genre_ids)
    update_anime = anime.model_dump(exclude={"genre_ids"}, exclude_unset=True)
    for key, value in update_anime.items():
        setattr(db_anime, key, value)

    await db.commit()
    await db.refresh(db_anime)
    return db_anime


@router.delete("/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_anime(anime_id: int, db: AsyncSession = Depends(get_async_db),  current_user: UserModel = Depends(get_current_admin)):
    stmt = select(AnimeModel).where(AnimeModel.id == anime_id, AnimeModel.is_active == True)
    db_anime = await db.scalar(stmt)
    if db_anime is None:
        raise HTTPException(status_code=404, detail="Anime not found!")

    await db.execute(
        update(AnimeModel)
        .where(AnimeModel.id == anime_id)
        .values(is_active=False)
    )
    await db.commit()
