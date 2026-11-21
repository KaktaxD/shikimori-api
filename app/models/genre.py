from sqlalchemy import Column, String, Integer, ForeignKey, Table, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

genre_animes = Table(
    "genre_animes",
    Base.metadata,
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    Column("anime_id", Integer, ForeignKey("animes.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    animes: Mapped[list["Anime"]] = relationship("Anime", secondary=genre_animes, back_populates="genres")

