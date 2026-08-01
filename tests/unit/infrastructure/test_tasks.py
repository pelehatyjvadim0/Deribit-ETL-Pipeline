from __future__ import annotations

from collections.abc import Coroutine
from typing import Any

import pytest

from deribit_etl.domain.errors import UpstreamUnavailable
from deribit_etl.domain.models import Ticker


def test_celery_boundary_runs_the_async_runner_exactly_once(monkeypatch) -> None:
    """Calling the runner directly or twice would break the event-loop boundary."""
    from deribit_etl.infrastructure.tasks import tasks

    calls = {"runner": 0, "asyncio_run": 0}

    async def runner() -> None:
        return None

    def make_coroutine() -> Coroutine[Any, Any, None]:
        calls["runner"] += 1
        return runner()

    def run_once(coroutine: Coroutine[Any, Any, None]) -> None:
        calls["asyncio_run"] += 1
        coroutine.close()

    monkeypatch.setattr(tasks, "_run_ingestion", make_coroutine)
    monkeypatch.setattr(tasks.asyncio, "run", run_once)

    tasks.fetch_crypto_prices.run()

    assert calls == {"runner": 1, "asyncio_run": 1}


@pytest.mark.asyncio
async def test_async_runner_disposes_the_engine_once_when_ingestion_fails(monkeypatch) -> None:
    """Removing the finally block must leak the task-owned database engine."""
    from deribit_etl.infrastructure.tasks import tasks

    class FakeEngine:
        def __init__(self) -> None:
            self.dispose_count = 0

        async def dispose(self) -> None:
            self.dispose_count += 1

    class FailingSessionFactory:
        def __init__(self) -> None:
            raise RuntimeError("database is unavailable")

    fake_engine = FakeEngine()
    monkeypatch.setattr(tasks, "create_engine", lambda database_url: fake_engine)
    monkeypatch.setattr(
        tasks,
        "create_session_factory",
        lambda engine: FailingSessionFactory(),
    )

    with pytest.raises(RuntimeError, match="database is unavailable"):
        await tasks._run_ingestion()

    assert fake_engine.dispose_count == 1


@pytest.mark.asyncio
async def test_async_runner_logs_partial_failures_with_structured_fields(
    monkeypatch, caplog
) -> None:
    """Dropping a failure field would make worker events impossible to aggregate."""
    from deribit_etl.infrastructure.tasks import tasks

    class FakeEngine:
        async def dispose(self) -> None:
            return None

    class FakeSessionFactory:
        def __call__(self):
            return self

        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *args: object) -> None:
            return None

    class FakeClient:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *args: object) -> None:
            return None

    class PartialIngest:
        def __init__(self, *args: object) -> None:
            return None

        async def run(self, tickers: list[Ticker]):
            return {Ticker.ETH_USD: UpstreamUnavailable("Deribit unavailable")}

    monkeypatch.setattr(tasks, "create_engine", lambda database_url: FakeEngine())
    monkeypatch.setattr(
        tasks, "create_session_factory", lambda engine: FakeSessionFactory()
    )
    monkeypatch.setattr(tasks.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(tasks, "SqlAlchemyTickRepository", lambda session: object())
    monkeypatch.setattr(tasks, "SqlAlchemyUnitOfWork", lambda session: object())
    monkeypatch.setattr(tasks, "DeribitPriceProvider", lambda *args, **kwargs: object())
    monkeypatch.setattr(tasks, "IngestPrices", PartialIngest)

    with caplog.at_level("WARNING", logger=tasks.__name__):
        await tasks._run_ingestion()

    [record] = caplog.records
    assert record.event == "ingestion_upstream_failure"
    assert record.ticker == "eth_usd"
    assert record.timestamp is None
    assert record.error_class == "UpstreamUnavailable"


def test_settings_database_url_preserves_spaces_in_passwords() -> None:
    """Using form-style plus encoding would change a PostgreSQL password."""
    from sqlalchemy.engine import make_url

    from deribit_etl.settings import Settings

    settings = Settings(postgres_password="has space")

    assert make_url(settings.database_url).password == "has space"
