import aiohttp
import time
from app.core.config import settings
from app.core.http_client import HttpClient

class DeribitClient:
    @staticmethod
    async def get_index_price(index_name: str) -> dict | None:
        params = {'index_name': index_name}
        
        session = HttpClient.get_session()
        
        if session is None or session.closed:
            async with aiohttp.ClientSession() as temp_session:
                return await DeribitClient._execute_request(temp_session, params, index_name)
        
        return await DeribitClient._execute_request(session, params, index_name)
    
    @staticmethod
    async def _execute_request(session: aiohttp.ClientSession, params: dict, index_name: str):
        try:
            async with session.get(settings.DERIBIT_BASE_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
            
                remote_timestamp = data.get('usIn', int(time.time() * 1000))
                
                if len(str(remote_timestamp)) > 13: 
                    remote_timestamp //= 1000

                return {
                    'ticker': index_name,
                    'price': data['result']['index_price'],
                    'timestamp': remote_timestamp
                }
                
        except Exception as e:
            print(f'Error fetching data from Deribit: {e}')
            return None