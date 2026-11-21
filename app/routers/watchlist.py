from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm

from app.models.watchlist import Watchlist as WatchlistModel
from app.models.users import User as UserModel
from app.models.anime import Anime as AnimeModel
from app.schemas import UserCreate, User as UserSchema, AnimeCreate, Anime as AnimeSchema,  WatchlistCreate, WatchlistItem
from app.db_depends import get_async_db
from app.auth import hash_password, verify_password, create_access_token, get_current_admin, get_current_us

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

@router.post("", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
async def add_watchlist(
    data: WatchlistCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_us),
):
    """Добавляет аниме в список со статусом"""
    stmt = select(AnimeModel).where(AnimeModel.name == data.name, AnimeModel.is_active == True)
    anime = await db.scalar(stmt)
    if anime is None:
        raise HTTPException(status_code=404, detail="Anime not found!")

    existing = select(WatchlistModel).where(
        WatchlistModel.user_id == current_user.id,
        WatchlistModel.anime_id == anime.id,
    )
    existing_item = await db.scalar(existing)
    if existing_item is not None:
        raise HTTPException(status_code=409, detail="Anime already in your list!")

    db_item = WatchlistModel(user_id=current_user.id, anime_id=anime.id)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@router.get("", response_model=list[WatchlistItem], status_code=status.HTTP_200_OK)
async def get_all_watchlist(db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_us)):
    """Весь список аниме пользователя"""
    stmt = select(WatchlistModel).where(WatchlistModel.is_active == True)
    res = await db.scalars(stmt)
    return res

from app.schemas import WatchlistItem, WatchlistUpdate

@router.put("/{anime_name}", response_model=WatchlistItem, status_code=status.HTTP_200_OK)
async def update_watchlist_status(
    anime_name: str,
    data: WatchlistUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_us),
):
    """Меняет статус просмотра аниме в списке (watching <-> watched)."""
    anime = await db.scalar(
        select(AnimeModel).where(AnimeModel.name == anime_name, AnimeModel.is_active == True)
    )
    if anime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not found!")

    db_item = await db.scalar(
        select(WatchlistModel).where(
            WatchlistModel.user_id == current_user.id,
            WatchlistModel.anime_id == anime.id,
            WatchlistModel.is_active == True,
        )
    )
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not in your list!")

    db_item.status = data.status
    await db.commit()
    await db.refresh(db_item)
    return db_item

@router.delete("/{anime_name}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_watchlist(anime_name: str, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_us),):
    """Мягко удаляет аниме из личного списка пользователя (is_active = False)."""
    anime = await db.scalar(select(AnimeModel).where(AnimeModel.name == anime_name, AnimeModel.is_active == True))
    if anime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not found!")

    db_item = await db.scalar(select(WatchlistModel).where(WatchlistModel.user_id == current_user.id, WatchlistModel.anime_id == anime.id,WatchlistModel.is_active == True))
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not in your list!")

    db_item.is_active = False
    await db.commit()

