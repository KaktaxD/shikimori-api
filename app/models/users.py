from sqlalchemy import Boolean, Integer, String, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

users_animes = Table(
    "users_animes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("anime_id", Integer, ForeignKey("animes.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String, default="user")

    animes: Mapped[list["Anime"]] = relationship("Anime", secondary=users_animes, back_populates="users")
    watchlist: Mapped[list["Watchlist"]] = relationship("Watchlist", back_populates="user", lazy="selectin")

