import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def clear_anime_cache(anime_id: int | None = None):
    """Удаляет кэш списка всех аниме и (если передан id) конкретной карточки."""
    await redis_client.delete("animes:all")
    if anime_id is not None:
        await redis_client.delete(f"animes:{anime_id}")
