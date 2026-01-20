import pytest
from app.currency.dao import TickDAO

@pytest.mark.parametrize('ticker_to, dao_return, exp_status', [
    ('eth_usd', [{'id': 1, 'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}], 200),
    ('test_usd', [{'id': 1, 'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}], 422),
    ('btc_usd', [{'id': 1, 'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}], 200),
    ('btc_usd', [{'id': 1, 'ticker': 'test_usd', 'price': 9999.9, 'timestamp': 7639864219}], 500),
    ('btc_usd', [], 404),
], ids=["eth_success", "invalid_ticker", "btc_success", "invalid_ticker_response", "not_found_ticker"])
async def test_get_all_prices(ac_client, mocker, mocker_Tick_DAO, ticker_to, dao_return, exp_status):
    
    mocker_Tick_DAO.find_all_by_ticker = mocker.AsyncMock(return_value = dao_return)
    
    response = await ac_client.get('/prices/', params={'ticker': ticker_to})
    
    print(response.status_code)
    
    status_code = response.status_code
    assert status_code == exp_status
    
    if status_code == 200:
        assert response.json()[0]['ticker'] == dao_return[0]['ticker']

@pytest.mark.parametrize('ticker_to, dao_return, status_code', [
    ('eth_usd',  {'id': 1, 'ticker': 'test_usd', 'price': 9999.9, 'timestamp': 7639864219}, 500),
    ('test_usd', {'id': 1, 'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}, 422),
    ('btc_usd', {'id': 1, 'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}, 200),
    ('btc_usd', {'id': 1, 'ticker': 'eth_usd', 'price': 9999.9, 'timestamp': 7639864219}, 200),
    ('btc_usd', {'id': 1, 'ticker': 'btc_usd', 'timestamp': 7639864219}, 500),
    ('btc_usd', {'id': 1, 'ticker': 'btc_usd', 'price': 9999.9}, 500),
    ('btc_usd', {'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}, 200),
    ('btc_usd', None, 404),
], ids=['invalid_ticker_resp', 'invalid_ticker_in', 'success_operation', 'success_diff_ticker', 'none_price_in_resp', 'none_timestamp_in_resp', 'none_id_in_resp', 'none_latest_price'])
async def test_get_latest_price(ac_client, mocker, mocker_Tick_DAO, ticker_to, dao_return, status_code):
    mocker_Tick_DAO.find_latest = mocker.AsyncMock(return_value = dao_return)

    response = await ac_client.get(f'/prices/{ticker_to}/latest')

    assert response.status_code == status_code
    if response.status_code == 200 and 'id' in dao_return:
        json_data = response.json()
        assert len(json_data) != len(dao_return)

@pytest.mark.parametrize('params, dao_return, status_code', [
    ({'ticker': 'btc_usd', 'start_timestamp': 1673737000}, [{'ticker': 'btc_usd', 'price': 100, 'timestamp': 1737370001}], 200),
    ({'ticker': 'btc_usd', 'start_timestamp': 1673737000}, [], 200),
    ({'ticker': 'btc_usd', 'start_timestamp': 'вчера'}, [], 422),
    ({'ticker': 'btc_usd', 'start_timestamp': 1673737000, 'limit': 50, 'offset': 10}, [], 200),
    ({'ticker': 'btc_usd', 'start_timestamp': 1673737000, 'limit': 101}, [], 422),
    ({'ticker': 'btc_usd', 'start_timestamp': 1673737000, 'limit': 0}, [], 422),
    ({'ticker': 'btc_usd', 'start_timestamp': 1673737000, 'limit': 5, 'offset': -1}, [], 422),
], ids=['success_filter', 'not_int_from_start_timestamp', 'success_empty_list_return', 'success_size_filter', 'limit_invalid_le_100', 'offset_invalid_ge_0', 'limit_invalid_ge_1'])
async def test_get_prices_by_filter(mocker, mocker_Tick_DAO, ac_client, params, dao_return, status_code):
    mocker_Tick_DAO.find_by_filter = mocker.AsyncMock(return_value=dao_return)

    response = await ac_client.get('/prices/filter', params=params)
       
    if status_code == 200:
        assert isinstance(response.json(), list)
        if len(response.json()) != 0:
            assert len(response.json()[0]) != len(dao_return)