from celery import Celery
from app.core.config import settings
from celery.schedules import crontab

celery_app = Celery(
    'tasks',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}',
    include=['app.tasks.tasks']
)

celery_app.conf.beat_schedule = {
    'fetch-prices-every-minute': {
        'task': 'fetch_crypto_prices',
        'schedule': crontab(minute='*')
    },
}

celery_app.conf.update(
    timezone = 'UTC',
    enable_utc = True
)