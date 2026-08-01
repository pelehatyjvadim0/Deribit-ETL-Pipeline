"""Framework-free ports for quote providers and storage."""

from collections.abc import Sequence
from typing import Protocol

from deribit_etl.domain.models import Tick, Ticker


class PriceProvider(Protocol):
    async def fetch(self, ticker: Ticker) -> Tick:
        """Fetch the most recent quote for a ticker."""
        ...


class TickWriter(Protocol):
    async def add(self, tick: Tick) -> None:
        """Store one quote without committing a transaction."""
        ...


class TickReader(Protocol):
    async def list(self, ticker: Ticker, *, limit: int, offset: int) -> Sequence[Tick]:
        """Return a page of quotes for a ticker."""
        ...

    async def latest(self, ticker: Ticker) -> Tick | None:
        """Return the newest stored quote for a ticker, if any."""
        ...

    async def in_range(
        self,
        ticker: Ticker,
        *,
        start_timestamp: int,
        end_timestamp: int,
        limit: int,
        offset: int,
    ) -> Sequence[Tick]:
        """Return a page of quotes within an inclusive timestamp range."""
        ...


class TickRepository(TickReader, TickWriter, Protocol):
    """Combined read/write repository port for adapters that provide both."""
