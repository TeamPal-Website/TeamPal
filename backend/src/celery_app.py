from celery import Celery

from src.config import settings

_broker = settings.celery_broker or "redis://127.0.0.1:6379/0"
celery_app = Celery("teampal", broker=_broker, backend=_broker)

import src.tasks.catalog
