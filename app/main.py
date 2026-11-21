from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers.animes import router as animes_router
from app.routers.genres import router as genres_router
from app.routers.users import router as users_router
from app.routers.reviews import router as reviews_router
from app.routers.watchlist import router as watchlist_router

# Создаём приложение FastAPI
app = FastAPI(
    title="Shikimori",
    version="0.1.0",
)

app.include_router(genres_router)
app.include_router(animes_router)
app.include_router(users_router)
app.include_router(watchlist_router)
app.include_router(reviews_router)

@app.get("/")
async def root():
    """Главная ветка"""
    return {"message": "Hello World"}