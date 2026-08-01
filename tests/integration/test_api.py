from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from deribit_etl.application.prices import PriceQueries
from deribit_etl.domain.models import Tick, Ticker


class FakeReader:
    def __init__(self) -> None:
        self.list_result: list[Tick] = []
        self.latest_result: Tick | None = None
        self.range_result: list[Tick] = []
        self.range_request: tuple[Ticker, int, int, int, int] | None = None

    async def list(self, ticker: Ticker, *, limit: int, offset: int) -> list[Tick]:
        return self.list_result

    async def latest(self, ticker: Ticker) -> Tick | None:
        return self.latest_result

    async def in_range(
        self,
        ticker: Ticker,
        *,
        start_timestamp: int,
        end_timestamp: int,
        limit: int,
        offset: int,
    ) -> list[Tick]:
        self.range_request = (ticker, start_timestamp, end_timestamp, limit, offset)
        return self.range_result


class FakeUnitOfWork:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.fixture
def api_context():
    from deribit_etl.api.dependencies import (
        ApplicationServices,
        get_application_services,
        get_current_time_ms,
    )
    from deribit_etl.main import create_app

    reader = FakeReader()
    app = create_app()

    async def override_services() -> ApplicationServices:
        return ApplicationServices(
            prices=PriceQueries(reader),
            unit_of_work=FakeUnitOfWork(),
        )

    app.dependency_overrides[get_application_services] = override_services
    app.dependency_overrides[get_current_time_ms] = lambda: 1_700_000_000_000
    return app, reader


@pytest.mark.asyncio
async def test_filter_normalizes_whole_seconds_to_milliseconds_once(api_context) -> None:
    """Removing request-boundary normalization must forward seconds to storage."""
    app, reader = api_context
    reader.range_result = [
        Tick(Ticker.BTC_USD, Decimal("62000.50"), 1_700_000_005)
    ]

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/prices/filter",
            params={
                "ticker": "btc_usd",
                "start_timestamp": 1_700_000_000,
                "end_timestamp": 1_700_000_010,
            },
        )

    assert response.status_code == 200
    assert reader.range_request == (
        Ticker.BTC_USD,
        1_700_000_000_000,
        1_700_000_010_000,
        10,
        0,
    )
    assert response.json() == [
        {"ticker": "btc_usd", "price": "62000.50", "timestamp": 1_700_000_005_000}
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "expected_detail"),
    [
        ("/prices/?ticker=btc_usd", "Данные по этому тикеру не найдены"),
        (
            "/prices/btc_usd/latest",
            "Актуальные данные по тикеру btc_usd не найдены",
        ),
    ],
)
async def test_empty_price_queries_keep_not_found_semantics(
    api_context, path: str, expected_detail: str
) -> None:
    """Returning 200 for an absent list/latest result breaks the read API."""
    app, _ = api_context

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(path)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}


@pytest.mark.asyncio
async def test_health_returns_readiness_without_configuration(api_context) -> None:
    """Adding connection details to readiness would expose service secrets."""
    from deribit_etl.api.dependencies import get_session

    app, _ = api_context

    class ReadySession:
        async def execute(self, statement: object) -> None:
            return None

    async def ready_session():
        yield ReadySession()

    app.dependency_overrides[get_session] = ready_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_returns_safe_service_unavailable_when_database_fails(
    api_context,
) -> None:
    """Propagating a readiness error as 500 would hide the service state."""
    from sqlalchemy.exc import OperationalError

    from deribit_etl.api.dependencies import get_session

    app, _ = api_context

    class UnavailableSession:
        async def execute(self, statement: object) -> None:
            raise OperationalError("SELECT 1", {}, RuntimeError("secret host"))

    async def unavailable_session():
        yield UnavailableSession()

    app.dependency_overrides[get_session] = unavailable_session
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service is not ready"}
    assert "secret" not in response.text


@pytest.mark.asyncio
async def test_filter_rejects_a_range_starting_in_the_future(api_context) -> None:
    """Removing the future guard must incorrectly call the query use case."""
    app, reader = api_context

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/prices/filter",
            params={"ticker": "btc_usd", "start_timestamp": 1_800_000_000},
        )

    assert response.status_code == 422
    assert reader.range_request is None
