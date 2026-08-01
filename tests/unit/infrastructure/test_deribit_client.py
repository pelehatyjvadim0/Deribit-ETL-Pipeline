from decimal import Decimal

import httpx
import pytest

from deribit_etl.domain.errors import (
    MalformedUpstreamResponse,
    UpstreamTimeout,
    UpstreamUnavailable,
)
from deribit_etl.domain.models import Tick, Ticker
from deribit_etl.infrastructure.deribit.client import DeribitPriceProvider


@pytest.mark.asyncio
async def test_fetch_normalizes_deribit_microseconds_to_milliseconds() -> None:
    """Leaving Deribit's usIn value in microseconds must fail this contract."""

    async def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v2/public/get_index_price"
        assert dict(request.url.params) == {"index_name": "btc_usd"}
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "result": {"index_price": 62000.25},
                "usIn": 1_700_000_001_234_567,
                "usOut": 1_700_000_001_235_000,
                "usDiff": 433,
                "testnet": False,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=1.0,
            max_retries=0,
        )

        tick = await provider.fetch(Ticker.BTC_USD)

    assert tick == Tick(
        ticker=Ticker.BTC_USD,
        price=Decimal("62000.25"),
        timestamp=1_700_000_001_234,
    )


@pytest.mark.asyncio
async def test_fetch_treats_us_in_as_microseconds_at_every_magnitude() -> None:
    """A magnitude heuristic must not reinterpret the documented usIn unit."""

    async def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={
                "jsonrpc": "2.0",
                "result": {"index_price": 62000.25},
                "usIn": 1_700_000_001_234,
                "usOut": 1_700_000_002_000,
                "usDiff": 766,
                "testnet": False,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=1.0,
            max_retries=0,
        )

        tick = await provider.fetch(Ticker.BTC_USD)

    assert tick.timestamp == 1_700_000_001


@pytest.mark.asyncio
async def test_fetch_maps_http_timeout_to_typed_upstream_error() -> None:
    """Leaking httpx timeout exceptions would bypass the application error contract."""

    async def time_out(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Deribit timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(time_out)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=0.1,
            max_retries=0,
        )

        with pytest.raises(UpstreamTimeout):
            await provider.fetch(Ticker.ETH_USD)


@pytest.mark.asyncio
async def test_fetch_retries_5xx_only_up_to_configured_limit() -> None:
    """An unbounded loop or wrong retry count changes the finite retry contract."""
    attempts = 0

    async def unavailable(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(unavailable)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=1.0,
            max_retries=2,
        )

        with pytest.raises(UpstreamUnavailable):
            await provider.fetch(Ticker.BTC_USD)

    assert attempts == 3


@pytest.mark.asyncio
async def test_fetch_retries_transport_error_then_returns_tick() -> None:
    """Not retrying transient transport failures would lose a recoverable quote."""
    attempts = 0

    async def recover(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("connection reset", request=request)
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "result": {"index_price": 3000.5},
                "usIn": 1_700_000_001_234_000,
                "usOut": 1_700_000_001_235_000,
                "usDiff": 1000,
                "testnet": False,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(recover)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=1.0,
            max_retries=2,
        )

        tick = await provider.fetch(Ticker.ETH_USD)

    assert tick.price == Decimal("3000.5")
    assert attempts == 2


@pytest.mark.asyncio
async def test_fetch_maps_malformed_json_without_retrying() -> None:
    """Retrying a deterministic JSON error or leaking JSONDecodeError must fail."""
    attempts = 0

    async def malformed(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200,
            request=request,
            content=b"{not-json",
            headers={"content-type": "application/json"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(malformed)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=1.0,
            max_retries=3,
        )

        with pytest.raises(MalformedUpstreamResponse):
            await provider.fetch(Ticker.BTC_USD)

    assert attempts == 1


@pytest.mark.asyncio
async def test_fetch_maps_4xx_without_retrying() -> None:
    """Retrying a non-transient client response violates the retry policy."""
    attempts = 0

    async def rejected(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(400, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(rejected)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=1.0,
            max_retries=3,
        )

        with pytest.raises(UpstreamUnavailable):
            await provider.fetch(Ticker.BTC_USD)

    assert attempts == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"jsonrpc": "2.0", "usIn": 1_700_000_001_234_000},
        {
            "jsonrpc": "2.0",
            "result": {"index_price": "not-a-price"},
            "usIn": 1_700_000_001_234_000,
        },
        {
            "jsonrpc": "2.0",
            "result": {"index_price": 62000.25},
            "usIn": "not-a-timestamp",
        },
    ],
)
@pytest.mark.asyncio
async def test_fetch_maps_invalid_payload_shape(payload: object) -> None:
    """Missing or invalid quote fields must not leak parsing implementation errors."""

    async def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        provider = DeribitPriceProvider(
            client,
            base_url="https://www.deribit.com/api/v2",
            timeout=1.0,
            max_retries=0,
        )

        with pytest.raises(MalformedUpstreamResponse):
            await provider.fetch(Ticker.BTC_USD)
