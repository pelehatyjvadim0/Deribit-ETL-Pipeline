import pytest 
from app.currency.dao import TickDAO
from sqlalchemy import delete
from app.currency.models import CurrencyTick

@pytest.mark.parametrize('test_query', ['ok', 'empty_list'])
async def test_find_by_filter(session, test_query):
    if test_query == 'ok':
        tick_data = {'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737000}
        await TickDAO.add(session=session, **tick_data)
        await session.commit()
    
    result = await TickDAO.find_by_filter(
        session=session,
        ticker='btc_usd',
        start_ts=1673737000,
        end_ts=1673737000
    )
    
    if test_query == 'ok':
        assert len(result) == 1
        assert result[0].ticker == 'btc_usd'
        assert float(result[0].price) == 100
        
        await session.execute(delete(CurrencyTick))
        await session.commit()
        
    else:
        assert len(result) == 0
        assert isinstance(result, list)
        
        await session.execute(delete(CurrencyTick))
        await session.commit()

@pytest.mark.parametrize('find_ticker, excepted_timestamp', [
    ('btc_usd', 1673737001),
    ('eth_usd', 1673737005),
    ('test_usd', None)
]) 
async def test_find_latest(session, find_ticker, excepted_timestamp):
    tick_data = [{'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737000},
                {'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737001},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737002},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737003},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737004},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737005}]
    
    for ticker in tick_data:
        await TickDAO.add(session=session, **ticker)
    
    result = await TickDAO.find_latest(session=session, ticker=find_ticker)
    
    if excepted_timestamp is None:
        assert result is None
    else: 
        assert result.timestamp == excepted_timestamp
        assert not isinstance(result, (list, dict))
        
