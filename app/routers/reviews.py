from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_current_us
from app.db_depends import get_async_db
from app.models.anime import Anime as AnimeModel
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel
from app.schemas import ReviewCreate, ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/{anime_name}", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    anime_name: str,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_us),
):
    """Создаёт отзыв на аниме (или восстанавливает ранее удалённый)."""
    anime = await db.scalar(
        select(AnimeModel).where(AnimeModel.name == anime_name, AnimeModel.is_active == True)
    )
    if anime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not found!")

    existing_review = await db.scalar(
        select(ReviewModel).where(
            ReviewModel.user_id == current_user.id,
            ReviewModel.anime_id == anime.id,
        )
    )
    if existing_review is not None:
        if existing_review.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this anime!",
            )
        existing_review.text = review_data.text
        existing_review.rating = review_data.rating
        existing_review.is_active = True
        await db.commit()
        await db.refresh(existing_review)
        return existing_review

    db_review = ReviewModel(
        text=review_data.text,
        rating=review_data.rating,
        user_id=current_user.id,
        anime_id=anime.id,
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review


@router.get("/{anime_name}", response_model=list[ReviewOut], status_code=status.HTTP_200_OK)
async def get_anime_reviews(
    anime_name: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Возвращает все активные отзывы на конкретное аниме."""
    anime = await db.scalar(
        select(AnimeModel).where(AnimeModel.name == anime_name, AnimeModel.is_active == True)
    )
    if anime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not found!")

    stmt = (
        select(ReviewModel)
        .where(ReviewModel.anime_id == anime.id, ReviewModel.is_active == True)
        .order_by(ReviewModel.id.desc())
    )
    result = await db.scalars(stmt)
    return result.all()


@router.put("/{anime_name}", response_model=ReviewOut, status_code=status.HTTP_200_OK)
async def update_my_review(
    anime_name: str,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_us),
):
    """Редактирует отзыв текущего пользователя на указанное аниме."""
    anime = await db.scalar(
        select(AnimeModel).where(AnimeModel.name == anime_name, AnimeModel.is_active == True)
    )
    if anime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not found!")

    db_review = await db.scalar(
        select(ReviewModel).where(
            ReviewModel.user_id == current_user.id,
            ReviewModel.anime_id == anime.id,
            ReviewModel.is_active == True,
        )
    )
    if db_review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found!")

    db_review.text = review_data.text
    db_review.rating = review_data.rating
    await db.commit()
    await db.refresh(db_review)
    return db_review


@router.delete("/{anime_name}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_my_review(
    anime_name: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_us),
):
    """Мягко удаляет отзыв текущего пользователя."""
    anime = await db.scalar(
        select(AnimeModel).where(AnimeModel.name == anime_name, AnimeModel.is_active == True)
    )
    if anime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anime not found!")

    db_review = await db.scalar(
        select(ReviewModel).where(
            ReviewModel.user_id == current_user.id,
            ReviewModel.anime_id == anime.id,
            ReviewModel.is_active == True,
        )
    )
    if db_review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found!")

    db_review.is_active = False
    await db.commit()
