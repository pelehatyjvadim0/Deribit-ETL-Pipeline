from dataclasses import FrozenInstanceError

import pytest

from deribit_etl.domain.models import Tick, Ticker, normalize_timestamp


@pytest.mark.parametrize(
    ("timestamp", "expected_timestamp"),
    [
        (1_700_000_000, 1_700_000_000_000),
        (1_700_000_000_123, 1_700_000_000_123),
    ],
)
def test_normalize_timestamp_converts_seconds_and_preserves_milliseconds(
    timestamp: int, expected_timestamp: int
) -> None:
    assert normalize_timestamp(timestamp) == expected_timestamp


def test_normalize_timestamp_rejects_values_above_maximum() -> None:
    with pytest.raises(ValueError):
        normalize_timestamp(10**14 + 1)


def test_tick_is_an_immutable_quote() -> None:
    tick = Tick(ticker=Ticker.BTC_USD, price=62_000.0, timestamp=1_700_000_000_000)

    with pytest.raises(FrozenInstanceError):
        tick.price = 62_100.0
