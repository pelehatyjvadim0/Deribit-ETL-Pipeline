"""Price provider backed by Deribit's public HTTP API."""

from decimal import Decimal, DecimalException

import httpx

from deribit_etl.domain.errors import (
    MalformedUpstreamResponse,
    UpstreamTimeout,
    UpstreamUnavailable,
)
from deribit_etl.domain.models import Tick, Ticker

_MAX_TIMESTAMP = 10**14
_INDEX_PRICE_PATH = "/public/get_index_price"


class DeribitPriceProvider:
    """Fetch the latest Deribit index price with a caller-owned HTTP client."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        timeout: float,
        max_retries: int,
    ) -> None:
        self._client = client
        self._endpoint_url = f"{base_url.rstrip('/')}{_INDEX_PRICE_PATH}"
        self._timeout = timeout
        self._max_retries = max_retries

    async def fetch(self, ticker: Ticker) -> Tick:
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.get(
                    self._endpoint_url,
                    params={"index_name": ticker.value},
                    timeout=self._timeout,
                )
            except httpx.TimeoutException as error:
                if attempt < self._max_retries:
                    continue
                raise UpstreamTimeout("Deribit request timed out") from error
            except httpx.TransportError as error:
                if attempt < self._max_retries:
                    continue
                raise UpstreamUnavailable("Deribit transport failed") from error
            if response.status_code < 500:
                break
            if attempt == self._max_retries:
                raise UpstreamUnavailable("Deribit returned a server error")
        else:
            raise UpstreamUnavailable("Deribit request could not be attempted")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise UpstreamUnavailable("Deribit rejected the request") from error
        try:
            data = response.json()
        except ValueError as error:
            raise MalformedUpstreamResponse("Deribit returned malformed JSON") from error
        try:
            if not isinstance(data, dict):
                raise TypeError
            result = data["result"]
            if not isinstance(result, dict):
                raise TypeError
            timestamp = data["usIn"]
            if isinstance(timestamp, bool) or not isinstance(timestamp, int):
                raise TypeError
            timestamp //= 1_000
            if timestamp > _MAX_TIMESTAMP:
                raise ValueError
            price = Decimal(str(result["index_price"]))
            if not price.is_finite():
                raise ValueError
        except (KeyError, TypeError, ValueError, DecimalException) as error:
            raise MalformedUpstreamResponse("Deribit returned an invalid quote") from error
        return Tick(ticker=ticker, price=price, timestamp=timestamp)
