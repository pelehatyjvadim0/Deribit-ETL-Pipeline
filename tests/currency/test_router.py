import pytest
from app.currency.dao import TickDAO

@pytest.mark.parametrize('ticker_in, ticker_out, exp_status', [
    ('eth_usd', 'eth_usd', 200),
    ('test_usd', 'btc_usd', 422),
    ('btc_usd', 'eth_usd', 200),
], ids=["eth_success", "invalid_ticker", "btc_success"])
async def test_get_all_prices(ac_client, mocker, mocker_Tick_DAO, ticker_in, ticker_out, exp_status):
    
    client = ac_client
    m_all_tickers = [
        {'id': 1,
         'ticker': ticker_out,
         'price': 9999.99,
         'timestamp': 9832312231}
    ]

    mocker_Tick_DAO.find_all_by_ticker = mocker.AsyncMock(return_value = m_all_tickers)
    
    response = await client.get('/prices/', params={'ticker': ticker_in})
    
    print(response.status_code)
    
    status_code = response.status_code
    assert status_code == exp_status
    
    if status_code == 200:
        assert response.json()[0]['ticker'] == ticker_out

@pytest.mark.parametrize('ticker_to, dict_resp, status_code', [
    ('eth_usd',  {'id': 1, 'ticker': 'test_usd', 'price': 9999.9, 'timestamp': 7639864219}, 500),
    ('test_usd', {'id': 1, 'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}, 422),
    ('btc_usd', {'id': 1, 'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}, 200),
    ('btc_usd', {'id': 1, 'ticker': 'eth_usd', 'price': 9999.9, 'timestamp': 7639864219}, 200),
    ('btc_usd', {'id': 1, 'ticker': 'btc_usd', 'timestamp': 7639864219}, 500),
    ('btc_usd', {'id': 1, 'ticker': 'btc_usd', 'price': 9999.9}, 500),
    ('btc_usd', {'ticker': 'btc_usd', 'price': 9999.9, 'timestamp': 7639864219}, 200),
], ids=['invalid_ticker_resp', 'invalid_ticker_in', 'success_operation', 'success_diff_ticker', 'none_price_in_resp', 'none_timestamp_in_resp', 'none_id_in_resp'])
async def test_get_latest_price(ac_client, mocker, mocker_Tick_DAO, ticker_to, dict_resp, status_code):
    mocker_Tick_DAO.find_latest = mocker.AsyncMock(return_value = dict_resp)

    response = await ac_client.get(f'/prices/{ticker_to}/latest')

    assert response.status_code == status_code
    if response.status_code == 200 and 'id' in dict_resp:
        json_data = response.json()
        assert len(json_data) != len(dict_resp)