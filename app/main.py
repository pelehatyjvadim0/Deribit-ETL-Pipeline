from contextlib import asynccontextmanager
import aiohttp
from fastapi import FastAPI

from app.currency.router import router as router_currency
from app.core.http_client import HttpClient

@asynccontextmanager
async def lifespan(app: FastAPI):

    HttpClient.session = aiohttp.ClientSession()
    print('🚀 API Session initialized')
        
    yield
        
    await HttpClient.session.close()
        
    print('🛑 API Session closed')
        
app = FastAPI(
    title='Deribit-ETL-Pipeline',
    description='Сервис для мониторинга курсов криптовалют с использованием Celery и Redis',
    version='1.0.0',
    lifespan=lifespan
)

app.include_router(router_currency)

@app.get('/', tags=['Root'])
async def root():
    return {
        'status': 'working',
        'docs': '/docs',
        'message': 'Welcome to Deribit-ETL-Pipeline'
    }