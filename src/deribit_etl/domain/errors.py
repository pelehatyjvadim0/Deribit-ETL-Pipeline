"""Domain errors raised while accepting or retrieving market data."""


class InvalidTimestamp(ValueError):
    """Raised when a timestamp is not a supported Unix timestamp."""


class UpstreamError(Exception):
    """Base class for failures returned by the price provider."""


class UpstreamTimeout(UpstreamError):
    """The price provider did not respond before its timeout."""


class UpstreamUnavailable(UpstreamError):
    """The price provider could not serve a request."""


class MalformedUpstreamResponse(UpstreamError):
    """The price provider returned data that cannot form a tick."""
