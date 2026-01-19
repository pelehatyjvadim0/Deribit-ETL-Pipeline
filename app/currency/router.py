from fastapi import APIRouter, HTTPException, Query, status, Depends, Path
from app.currency.dao import TickDAO
from app.currency.schemas import STickResponse, SPriceRequest, STickPaginationParams, CurrencyTicker
from typing import List, Annotated
from app.dependencies import CurrentTimeDep, SessionDep

router = APIRouter(
    prefix='/prices',
    tags=['Курсы валют']
)

@router.get('/', response_model=List[STickResponse])
async def get_all_prices(session: SessionDep, params: Annotated[STickPaginationParams, Depends()]):
    data = await TickDAO.find_all_by_ticker(ticker=params.ticker, session=session, limit=params.limit, offset=params.offset)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Данные по этому тикеру не найдены'
        )
    return data

@router.get('/{ticker}/latest', response_model=STickResponse)
async def get_latest_price(session: SessionDep, ticker: Annotated[CurrencyTicker, Path(description='Выберите валютную пару')]):
    price = await TickDAO.find_latest(ticker=ticker, session=session)
    
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Актуальные данные по тикеру {ticker} не найдены'
        )
        
    return price

@router.get('/filter', response_model=List[STickResponse])
async def get_prices_by_filter(
    current_time: CurrentTimeDep,
    session: SessionDep,
    params: SPriceRequest = Depends()
):
    end_ts = params.end_timestamp if params.end_timestamp is not None else current_time
        
    data = await TickDAO.find_by_date(params.ticker, start_ts=params.start_timestamp, end_ts=end_ts, session=session)
    return data