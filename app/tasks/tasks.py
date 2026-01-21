import asyncio
from app.tasks.celery import celery_app
from app.external_api.deribit import DeribitClient
from app.crud import TickDAO
from app.core.database import new_session

@celery_app.task(name='fetch_crypto_prices')
def fetch_crypto_prices():
    async def fetch_and_save():
        from app.core.database import engine
        
        tickers = ['btc_usd', 'eth_usd']
        
        async with new_session() as session:
        
            for ticker in tickers:
                data = await DeribitClient.get_index_price(ticker)
                
                if data:
                    await TickDAO.add(
                        ticker=data['ticker'],
                        price=data['price'],
                        timestamp=data['timestamp'],
                        session=session
                    )
                    print(f'Successfully saved {ticker} price')
                    
        await engine.dispose()
                
    asyncio.run(fetch_and_save())