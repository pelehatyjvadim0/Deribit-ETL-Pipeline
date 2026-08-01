"""HTTP request and response schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deribit_etl.domain.errors import InvalidTimestamp
from deribit_etl.domain.models import Ticker, normalize_timestamp


class TickResponse(BaseModel):
    ticker: Ticker
    price: Decimal
    timestamp: int

    model_config = ConfigDict(from_attributes=True)

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_milliseconds(cls, value: int) -> int:
        try:
            return normalize_timestamp(value)
        except InvalidTimestamp as error:
            raise ValueError(str(error)) from error


class PricePaginationParams(BaseModel):
    ticker: Ticker
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PriceFilterParams(PricePaginationParams):
    start_timestamp: int
    end_timestamp: int | None = None

    @field_validator("start_timestamp", "end_timestamp")
    @classmethod
    def timestamps_are_milliseconds(cls, value: int | None) -> int | None:
        if value is None:
            return None
        try:
            return normalize_timestamp(value)
        except InvalidTimestamp as error:
            raise ValueError(str(error)) from error

    @model_validator(mode="after")
    def end_is_not_before_start(self) -> "PriceFilterParams":
        if self.end_timestamp is not None and self.end_timestamp < self.start_timestamp:
            raise ValueError("Конец периода не может быть раньше начала")
        return self


class HealthResponse(BaseModel):
    status: str
