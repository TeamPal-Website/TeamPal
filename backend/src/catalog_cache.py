import json
import redis.asyncio as redis
from src.config import settings
TTL_SEC = 300
# cities:v2 — сброс устаревшего кэша после сидов в БД (пустой список мог «залипнуть» на 300 с)
NAMES_TO_KEY = {'cities': 'tp:cat:cities:v2', 'skills': 'tp:cat:skills', 'roles': 'tp:cat:roles'}
_redis: redis.Redis | None = None

async def get_redis():
    global _redis
    if not settings.REDIS_URL:
        return None
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def close_redis():
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None

async def cached_json_list(name: str, fetch):
    key = NAMES_TO_KEY.get(name)
    if not key:
        return await fetch()
    r = await get_redis()
    if r:
        raw = await r.get(key)
        if raw:
            parsed = json.loads(raw)
            # Пустой список городов в Redis часто «залипал» до сидов — не доверяем, перечитываем БД
            if name == 'cities' and isinstance(parsed, list) and len(parsed) == 0:
                try:
                    await r.delete(key)
                except Exception:
                    pass
            else:
                return parsed
    items = await fetch()
    out = [x.model_dump(mode='json') for x in items]
    if r:
        # Не кэшировать пустой cities — иначе после наполнения БД снова залипнет до истечения TTL
        if name == 'cities' and len(out) == 0:
            try:
                await r.delete(key)
            except Exception:
                pass
        else:
            await r.setex(key, TTL_SEC, json.dumps(out))
    return out

def schedule_catalog_invalidate(names: list[str]):
    if not settings.celery_broker:
        return
    from src.tasks.catalog import invalidate_catalog_cache
    invalidate_catalog_cache.delay(names)
