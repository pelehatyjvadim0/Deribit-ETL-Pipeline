from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.currency.dao import TickDAO
from app.currency.schemas import STickResponse, SPriceRequest
from typing import List
from app.dependencies import CurrentTimeDep, SessionDep

router = APIRouter(
    prefix='/prices',
    tags=['Курсы валют']
)

@router.get('/{ticker}', response_model=List[STickResponse])
async def get_all_prices(ticker: str, session: SessionDep):
    data = await TickDAO.find_all_by_ticker(ticker=ticker, session=session)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Данные по этому тикеру не найдены'
        )
    return data

@router.get('/{ticker}/latest', response_model=STickResponse)
async def get_latest_price(ticker: str):
    price = await TickDAO.find_latest(ticker=ticker)
    
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Нет доступа'
        )
        
    return price

@router.get('/{ticker}/filter', response_model=List[STickResponse])
async def get_prices_by_filter(
    current_time: CurrentTimeDep,
    session: SessionDep,
    params: SPriceRequest = Depends()
):
    if params.end_timestamp is None:
        end_ts = current_time
        
    data = await TickDAO.find_by_date(params.ticker, start_ts=params.start_timestamp, end_ts=params.end_timestamp, session=session)
    return data