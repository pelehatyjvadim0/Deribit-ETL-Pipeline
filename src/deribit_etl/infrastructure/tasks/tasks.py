"""Synchronous Celery boundary for asynchronous ingestion."""

import asyncio
import logging

import httpx

from deribit_etl.application.ingest import IngestPrices
from deribit_etl.domain.models import Ticker
from deribit_etl.infrastructure.db.database import create_engine, create_session_factory
from deribit_etl.infrastructure.db.repository import (
    SqlAlchemyTickRepository,
    SqlAlchemyUnitOfWork,
)
from deribit_etl.infrastructure.deribit.client import DeribitPriceProvider
from deribit_etl.infrastructure.tasks.celery import celery_app
from deribit_etl.settings import get_settings

logger = logging.getLogger(__name__)


async def _run_ingestion() -> None:
    """Own all async worker resources and release the engine on every exit."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        session_factory = create_session_factory(engine)
        async with httpx.AsyncClient() as client, session_factory() as session:
            repository = SqlAlchemyTickRepository(session)
            provider = DeribitPriceProvider(
                client,
                base_url=settings.deribit_base_url,
                timeout=settings.deribit_timeout_seconds,
                max_retries=settings.deribit_retry_attempts,
            )
            failures = await IngestPrices(
                provider,
                repository,
                SqlAlchemyUnitOfWork(session),
            ).run(list(Ticker))
            for ticker, error in failures.items():
                logger.warning(
                    "ingestion_upstream_failure",
                    extra={
                        "event": "ingestion_upstream_failure",
                        "ticker": ticker.value,
                        "timestamp": None,
                        "error_class": type(error).__name__,
                    },
                )
    finally:
        await engine.dispose()


@celery_app.task(name="fetch_crypto_prices")
def fetch_crypto_prices() -> None:
    """Run one ingestion coroutine in one task-owned event loop."""
    asyncio.run(_run_ingestion())
