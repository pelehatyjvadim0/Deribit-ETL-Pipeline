import pytest 
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from dotenv import load_dotenv

load_dotenv()

from app.main import app
from app.dependencies import get_session
from app.core.models import BaseModel
from app.core.config import settings

DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
engine_test = create_async_engine(DATABASE_URL)
session_maker = async_sessionmaker(bind=engine_test)

@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
    
@pytest.fixture(scope='session', autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    
    yield
    
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    
@pytest.fixture(scope='function')
async def ac_online():
    async with AsyncClient(base_url='http://test') as client:
        yield client
   
@pytest.fixture(scope='function')     
async def ac_offline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client
    
async def override_get_db():
    async with session_maker() as session:
        yield session

