import pytest 
from app.core.config import settings
from httpx import AsyncClient
from app.main import app
from app.api.dependencies import get_session
from app.core.http_client import HttpClient

async def test_get_prices_e2e_full_cycle(client: AsyncClient):
    _ = HttpClient.get_session()
    
    if get_session in app.dependency_overrides:
        old_overide = app.dependency_overrides.pop(get_session)
    
    try:
        settings.MODE = 'DEV'
        _ = settings.DATABASE_URL
        response = await client.get(
            '/prices/filter',
            params={'ticker': 'btc_usd', 'start_timestamp': 1673737000}
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        future_ts = 2020723200
        response_future = await client.get(
            '/prices/filter',
            params={'ticker': 'btc_usd', 'start_timestamp': future_ts}
        )
        assert response_future.status_code == 422
        
        response_404 = await client.get(
            '/prices/filter',
            params={'ticker': 'non_existent_coin', 'start_timestamp': 1673737000}
        )
        
        assert response_404.status_code == 422
        
        settings.MODE = 'TEST'
        
        response_root = await client.get('/')
        
        assert response_root.json()['status'] == 'working'
    finally:
        app.dependency_overrides[get_session] = old_overide