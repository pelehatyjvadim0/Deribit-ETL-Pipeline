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
    
@pytest.fixture(scope='session', autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    
    yield
    
    async with engine_test.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)

async def get_test_db_session():
    async with session_maker() as session:
        yield session

@pytest.fixture(scope='function', autouse=True)
async def override_get_session():
    app.dependency_overrides[get_session] = get_test_db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope='function')     
async def ac_client():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url='http://test') as client:
        yield client

@pytest.fixture(scope='function')
async def mocker_Tick_DAO(mocker):
    mocker_Tick_DAO = mocker.patch('app.currency.router.TickDAO', autospec=True)
    return mocker_Tick_DAO