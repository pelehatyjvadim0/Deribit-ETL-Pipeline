from decimal import Decimal

import pytest

from deribit_etl.domain.errors import UpstreamUnavailable
from deribit_etl.domain.models import Tick, Ticker


class FakeProvider:
    def __init__(self, responses: dict[Ticker, Tick | Exception]) -> None:
        self.responses = responses

    async def fetch(self, ticker: Ticker) -> Tick:
        response = self.responses[ticker]
        if isinstance(response, Exception):
            raise response
        return response


class FakeWriter:
    def __init__(self, error: Exception | None = None) -> None:
        self.ticks: list[Tick] = []
        self.error = error

    async def add(self, tick: Tick) -> None:
        if self.error is not None:
            raise self.error
        self.ticks.append(tick)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


@pytest.mark.asyncio
async def test_ingest_stores_every_successful_tick_and_commits_once() -> None:
    from deribit_etl.application.ingest import IngestPrices

    btc_tick = Tick(Ticker.BTC_USD, Decimal("62000.50"), 1_700_000_000_000)
    eth_tick = Tick(Ticker.ETH_USD, Decimal("3200.25"), 1_700_000_000_000)
    provider = FakeProvider({Ticker.BTC_USD: btc_tick, Ticker.ETH_USD: eth_tick})
    writer = FakeWriter()
    unit_of_work = FakeUnitOfWork()

    failures = await IngestPrices(provider, writer, unit_of_work).run(
        [Ticker.BTC_USD, Ticker.ETH_USD]
    )

    assert failures == {}
    assert writer.ticks == [btc_tick, eth_tick]
    assert unit_of_work.commit_count == 1
    assert unit_of_work.rollback_count == 0


@pytest.mark.asyncio
async def test_ingest_collects_upstream_failures_by_ticker_and_continues() -> None:
    from deribit_etl.application.ingest import IngestPrices

    btc_tick = Tick(Ticker.BTC_USD, Decimal("62000.50"), 1_700_000_000_000)
    upstream_error = UpstreamUnavailable("Deribit unavailable")
    provider = FakeProvider({Ticker.BTC_USD: btc_tick, Ticker.ETH_USD: upstream_error})
    writer = FakeWriter()
    unit_of_work = FakeUnitOfWork()

    failures = await IngestPrices(provider, writer, unit_of_work).run(
        [Ticker.BTC_USD, Ticker.ETH_USD]
    )

    assert failures == {Ticker.ETH_USD: upstream_error}
    assert writer.ticks == [btc_tick]
    assert unit_of_work.commit_count == 1
    assert unit_of_work.rollback_count == 0


@pytest.mark.asyncio
async def test_ingest_rolls_back_and_reraises_database_errors() -> None:
    from deribit_etl.application.ingest import IngestPrices

    database_error = RuntimeError("database is unavailable")
    provider = FakeProvider(
        {Ticker.BTC_USD: Tick(Ticker.BTC_USD, Decimal("62000.50"), 1_700_000_000_000)}
    )
    writer = FakeWriter(error=database_error)
    unit_of_work = FakeUnitOfWork()

    with pytest.raises(RuntimeError, match="database is unavailable"):
        await IngestPrices(provider, writer, unit_of_work).run([Ticker.BTC_USD])

    assert unit_of_work.commit_count == 0
    assert unit_of_work.rollback_count == 1
