import pytest
from tests.conftest import override_get_db
from app.main import app
from app.dependencies import get_session

@pytest.mark.parametrize('ticker_in, ticker_out, exp_status', [
    ('eth_usd', 'eth_usd', 200),
    ('test_usd', 'btc_usd', 422),
    ('btc_usd', 'eth_usd', 200),
], ids=["eth_success", "invalid_ticker", "btc_success"])
async def test_get_all_prices(ac_offline, mocker, ticker_in, ticker_out, exp_status):
    
    client = ac_offline
    m_all_tickers = [
        {'id': 1,
         'ticker': ticker_out,
         'price': 9999.99,
         'timestamp': 9832312231}
    ]
    
    m_DAO = mocker.patch('app.currency.router.TickDAO', new_callable=mocker.MagicMock)
    m_DAO.find_all_by_ticker = mocker.AsyncMock(return_value = m_all_tickers)
    
    response = await client.get('/prices/', params={'ticker': ticker_in})
    
    print(response.status_code)
    
    status_code = response.status_code
    assert status_code == exp_status
    
    if status_code == 200:
        assert response.json()[0]['ticker'] == ticker_out