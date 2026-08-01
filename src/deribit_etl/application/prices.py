"""Read-only price query use cases."""

from collections.abc import Sequence

from deribit_etl.domain.models import Tick, Ticker
from deribit_etl.domain.ports import TickReader


class PriceQueries:
    """Retrieve stored quotes through the repository read port."""

    def __init__(self, reader: TickReader) -> None:
        self._reader = reader

    async def list(self, ticker: Ticker, *, limit: int, offset: int) -> Sequence[Tick]:
        """Return a page of stored quotes for a ticker."""
        return await self._reader.list(ticker, limit=limit, offset=offset)

    async def latest(self, ticker: Ticker) -> Tick | None:
        """Return the latest stored quote for a ticker, if any."""
        return await self._reader.latest(ticker)

    async def in_range(
        self,
        ticker: Ticker,
        *,
        start_timestamp: int,
        end_timestamp: int,
        limit: int,
        offset: int,
    ) -> Sequence[Tick]:
        """Return a page of quotes in an inclusive timestamp range."""
        return await self._reader.in_range(
            ticker,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            limit=limit,
            offset=offset,
        )
