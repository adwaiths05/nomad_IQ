import json
from functools import lru_cache
from typing import Any

from redis.asyncio import Redis

from app.config.settings import get_settings


@lru_cache
def _redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def cache_get_json(key: str) -> dict[str, Any] | list[Any] | None:
    try:
        raw = await _redis_client().get(key)
    except Exception:
        return None

    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_set_json(key: str, payload: Any, ttl_seconds: int | None = None) -> None:
    raw = json.dumps(payload)
    try:
        if ttl_seconds is None:
            await _redis_client().set(key, raw)
        else:
            await _redis_client().setex(key, ttl_seconds, raw)
    except Exception:
        return
