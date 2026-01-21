import pytest 
from app.crud import TickDAO
from sqlalchemy import delete
from app.core.models import CurrencyTick
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

    result = await TickDAO.find_latest(session=current_session, ticker=find_ticker)
    
    if excepted_timestamp is None:
        assert result is None
    else: 
        assert result.timestamp == excepted_timestamp
        assert not isinstance(result, (list, dict))

@pytest.mark.parametrize('ticker_req, limit_req, offset_req, id_first_ticker, resp_length, use_my_session', [
    ('btc_usd', 1, 0, 2, 1, False),
    ('eth_usd', 2, 2, 4, 2, True),
    ('test_usd', 1, 0, None, 0, False),
])      
async def test_find_all_by_ticker(session, ticker_req, limit_req, id_first_ticker, offset_req, resp_length, use_my_session):
    current_session = session if use_my_session else None
    
    tick_data = [{'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737000},
                {'ticker': 'btc_usd', 'price': 100, 'timestamp': 1673737001},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737002},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737003},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737004},
                {'ticker': 'eth_usd', 'price': 100, 'timestamp': 1673737005}]
    
    for ticker in tick_data:
        await TickDAO.add(session=current_session, **ticker)
    
    result = await TickDAO.find_all_by_ticker(session=current_session, ticker=ticker_req, limit=limit_req, offset=offset_req)
    
    assert isinstance(result, list)
    assert len(result) == resp_length
    
    if ticker_req != 'test_usd':
        assert result[0].id == id_first_ticker
        assert len(result) == limit_req 