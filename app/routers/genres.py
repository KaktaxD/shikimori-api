from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import GenreCreate, Genre as GenreSchema
from app.models.genre import Genre as GenreModel
from app.db_depends import get_async_db
from app.models.users import User as UserModel
from app.auth import get_current_admin, get_current_us

router = APIRouter(prefix="/genres", tags=["genres"])

@router.post("", response_model=GenreSchema, status_code=status.HTTP_201_CREATED)
async def create_genre(genre: GenreCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_admin)):
    stmt = select(GenreModel).where(GenreModel.name == genre.name)
    result = await db.scalars(stmt)
    if result.first():
        raise HTTPException(status_code=400, detail="Already created!")

    # Создание новой категории
    db_genre = GenreModel(**genre.model_dump())
    db.add(db_genre)
    await db.commit()
    await db.refresh(db_genre)
    return db_genre

@router.get("", response_model=list[GenreSchema])
async def get_all_genres(db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_us)):
    stmt = select(GenreModel).where(GenreModel.is_active == True).order_by(GenreModel.id)
    result = await db.scalars(stmt)
    return result.all()

@router.put("/{genre_name}", response_model=GenreSchema, status_code=status.HTTP_200_OK)
async def update_genre(genre_name: str, genre: GenreCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_admin)):
    """Обновляет название жанра (только для admin)."""
    stmt = select(GenreModel).where(GenreModel.name == genre_name, GenreModel.is_active == True)
    db_genre = await db.scalar(stmt)
    if db_genre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found.")

    if genre.name != genre_name:
        duplicate = await db.scalar(select(GenreModel).where(GenreModel.name == genre.name))
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Genre with this name already exists!")

    db_genre.name = genre.name
    await db.commit()
    await db.refresh(db_genre)
    return db_genre

