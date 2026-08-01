"""Core quote types and timestamp normalization."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from deribit_etl.domain.errors import InvalidTimestamp

_MILLISECONDS_THRESHOLD = 10**11
_MAX_TIMESTAMP = 10**14


class Ticker(str, Enum):  # noqa: UP042 - the public contract requires both bases.
    BTC_USD = "btc_usd"
    ETH_USD = "eth_usd"


@dataclass(frozen=True)
class Tick:
    ticker: Ticker
    price: Decimal
    timestamp: int


def normalize_timestamp(timestamp: int) -> int:
    """Return a Unix timestamp in milliseconds.

    Whole-second request timestamps are converted at this boundary, while
    millisecond timestamps remain unchanged. Larger values are assumed to use
    a finer unit and are not accepted.
    """
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise InvalidTimestamp("timestamp must be an integer")
    if timestamp > _MAX_TIMESTAMP:
        raise InvalidTimestamp("timestamp must not exceed 10**14")
    if timestamp < _MILLISECONDS_THRESHOLD:
        return timestamp * 1_000
    return timestamp
