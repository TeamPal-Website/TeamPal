from celery import Celery
from celery.schedules import crontab

from src.config import settings

_broker = settings.celery_broker or 'redis://127.0.0.1:6379/0'
celery_app = Celery('teampal', broker=_broker, backend=_broker)

celery_app.conf.task_routes = {
    'src.tasks.embeddings.*': {'queue': 'embeddings'},
}

celery_app.conf.beat_schedule = {
    'recompute-stale-embeddings-nightly': {
        'task': 'src.tasks.embeddings.recompute_stale_embeddings',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'embeddings'},
    },
}

import src.tasks.catalog  # noqa: F401
import src.tasks.embeddings  # noqa: F401
