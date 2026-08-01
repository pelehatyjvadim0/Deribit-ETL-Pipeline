"""Celery application construction."""

from celery import Celery
from celery.schedules import crontab

from deribit_etl.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "deribit_etl",
    broker=settings.redis_url,
    include=["deribit_etl.infrastructure.tasks.tasks"],
)
celery_app.conf.beat_schedule = {
    "fetch-prices-every-minute": {
        "task": "fetch_crypto_prices",
        "schedule": crontab(minute="*"),
    }
}
celery_app.conf.update(timezone="UTC", enable_utc=True)
