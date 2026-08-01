"""Use case for persisting a batch of current market prices."""

from typing import Protocol

from deribit_etl.domain.errors import UpstreamError
from deribit_etl.domain.models import Ticker
from deribit_etl.domain.ports import PriceProvider, TickWriter


class UnitOfWork(Protocol):
    """Transaction boundary controlled by an application use case."""

    async def commit(self) -> None:
        """Persist all changes made in the current transaction."""
        ...

    async def rollback(self) -> None:
        """Discard all changes made in the current transaction."""
        ...


class IngestPrices:
    """Fetch current quotes and persist successful results in one transaction."""

    def __init__(
        self,
        provider: PriceProvider,
        writer: TickWriter,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._provider = provider
        self._writer = writer
        self._unit_of_work = unit_of_work

    async def run(self, tickers: list[Ticker]) -> dict[Ticker, UpstreamError]:
        """Ingest quotes, returning provider failures keyed by ticker.

        Provider failures are isolated to an individual ticker. Storage and
        transaction failures roll back the complete batch and are re-raised.
        """
        failures: dict[Ticker, UpstreamError] = {}
        try:
            for ticker in tickers:
                try:
                    tick = await self._provider.fetch(ticker)
                except UpstreamError as error:
                    failures[ticker] = error
                    continue
                await self._writer.add(tick)
            await self._unit_of_work.commit()
        except Exception:
            await self._unit_of_work.rollback()
            raise
        return failures
