from __future__ import annotations

from decimal import Decimal

import pytest

from deribit_etl.domain.models import Tick, Ticker


class FakeReader:
    def __init__(self, ticks: list[Tick]) -> None:
        self.ticks = ticks
        self.list_request: tuple[Ticker, int, int] | None = None
        self.latest_ticker: Ticker | None = None
        self.range_request: tuple[Ticker, int, int, int, int] | None = None

    async def list(self, ticker: Ticker, *, limit: int, offset: int) -> list[Tick]:
        self.list_request = (ticker, limit, offset)
        return self.ticks

    async def latest(self, ticker: Ticker) -> Tick | None:
        self.latest_ticker = ticker
        return self.ticks[-1] if self.ticks else None

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
        return self.ticks


@pytest.fixture
def ticks() -> list[Tick]:
    return [
        Tick(Ticker.BTC_USD, Decimal("62000.50"), 1_700_000_000_000),
        Tick(Ticker.BTC_USD, Decimal("62001.00"), 1_700_000_001_000),
    ]


@pytest.mark.asyncio
async def test_list_returns_requested_page_from_repository(ticks: list[Tick]) -> None:
    from deribit_etl.application.prices import PriceQueries

    reader = FakeReader(ticks)

    result = await PriceQueries(reader).list(Ticker.BTC_USD, limit=20, offset=5)

    assert result == ticks
    assert reader.list_request == (Ticker.BTC_USD, 20, 5)


@pytest.mark.asyncio
async def test_latest_returns_newest_tick_or_none(ticks: list[Tick]) -> None:
    from deribit_etl.application.prices import PriceQueries

    reader = FakeReader(ticks)

    result = await PriceQueries(reader).latest(Ticker.BTC_USD)

    assert result == ticks[-1]
    assert reader.latest_ticker is Ticker.BTC_USD


@pytest.mark.asyncio
async def test_in_range_forwards_the_inclusive_timestamp_window(ticks: list[Tick]) -> None:
    from deribit_etl.application.prices import PriceQueries

    reader = FakeReader(ticks)

    result = await PriceQueries(reader).in_range(
        Ticker.BTC_USD,
        start_timestamp=1_700_000_000_000,
        end_timestamp=1_700_000_010_000,
        limit=10,
        offset=2,
    )

    assert result == ticks
    assert reader.range_request == (Ticker.BTC_USD, 1_700_000_000_000, 1_700_000_010_000, 10, 2)
