"""Read-only price HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from deribit_etl.api.dependencies import ApplicationServicesDep, CurrentTimeDep
from deribit_etl.api.schemas import PriceFilterParams, PricePaginationParams, TickResponse
from deribit_etl.domain.models import Ticker

router = APIRouter(prefix="/prices", tags=["Курсы валют"])


@router.get("/", response_model=list[TickResponse])
async def get_all_prices(
    services: ApplicationServicesDep,
    params: Annotated[PricePaginationParams, Query()],
) -> list[TickResponse]:
    ticks = await services.prices.list(
        params.ticker,
        limit=params.limit,
        offset=params.offset,
    )
    if not ticks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Данные по этому тикеру не найдены",
        )
    return [TickResponse.model_validate(tick) for tick in ticks]


@router.get("/filter", response_model=list[TickResponse])
async def get_prices_by_filter(
    services: ApplicationServicesDep,
    current_time: CurrentTimeDep,
    params: Annotated[PriceFilterParams, Query()],
) -> list[TickResponse]:
    if params.start_timestamp > current_time + 60_000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Вы пытаетесь запросить данные из будущего!",
        )
    end_timestamp = params.end_timestamp
    if end_timestamp is None:
        end_timestamp = current_time
    ticks = await services.prices.in_range(
        params.ticker,
        start_timestamp=params.start_timestamp,
        end_timestamp=end_timestamp,
        limit=params.limit,
        offset=params.offset,
    )
    return [TickResponse.model_validate(tick) for tick in ticks]


@router.get("/{ticker}/latest", response_model=TickResponse)
async def get_latest_price(
    services: ApplicationServicesDep,
    ticker: Ticker,
) -> TickResponse:
    tick = await services.prices.latest(ticker)
    if tick is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Актуальные данные по тикеру {ticker.value} не найдены",
        )
    return TickResponse.model_validate(tick)
