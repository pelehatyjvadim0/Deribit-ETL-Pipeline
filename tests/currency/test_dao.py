import pytest 
from app.currency.dao import TickDAO
from sqlalchemy import delete
from app.currency.models import CurrencyTick
from unittest.mock import patch

@pytest.mark.parametrize('test_query, use_my_session', [('ok', True), ('empty_list', False)])
async def test_find_by_filter(session, test_query, use_my_session):
    if test_query == 'ok':
        tick_data = {'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737000}
        await TickDAO.add(session=session, **tick_data)
        await session.commit()
        
    current_session = session if use_my_session else None

    result = await TickDAO.find_by_filter(
    session=current_session,
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

@pytest.mark.parametrize('find_ticker, excepted_timestamp, use_my_session', [
    ('btc_usd', 1673737001, True),
    ('eth_usd', 1673737005, False),
    ('test_usd', None, True)
]) 
async def test_find_latest(session, find_ticker, excepted_timestamp, use_my_session):
    tick_data = [{'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737000},
                {'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737001},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737002},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737003},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737004},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737005}]
    
    with patch.object(TickDAO, 'add', wraps=TickDAO.add) as spy:
        current_session = session if use_my_session is True else None

        for ticker in tick_data:
            await TickDAO.add(session=current_session, **ticker)
        args, kwargs = spy.call_args
        assert kwargs['session'] == current_session

    result = await TickDAO.find_latest(session=session, ticker=find_ticker)
    
    if excepted_timestamp is None:
        assert result is None
    else: 
        assert result.timestamp == excepted_timestamp
        assert not isinstance(result, (list, dict))