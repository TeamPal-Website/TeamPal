import redis

from src.catalog_cache import NAMES_TO_KEY
from src.celery_app import celery_app
from src.config import settings


@celery_app.task
def invalidate_catalog_cache(names: list[str]):
    url = settings.celery_broker
    if not url:
        return
    r = redis.from_url(url, decode_responses=True)
    try:
        keys = [NAMES_TO_KEY[n] for n in names if n in NAMES_TO_KEY]
        if keys:
            r.delete(*keys)
    finally:
        r.close()
