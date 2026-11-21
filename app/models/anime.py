from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Anime(Base):
    __tablename__ = "animes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    year_release: Mapped[int] = mapped_column(Integer, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    genres: Mapped[list["Genre"]] = relationship("Genre", secondary="genre_animes", back_populates="animes", lazy="selectin")
    users: Mapped[list["User"]] = relationship("User", secondary="users_animes", back_populates="animes")
