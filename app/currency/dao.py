from sqlalchemy import desc, select, insert
from app.currency.models import CurrencyTick
from app.core.database import new_session
import decimal

class TickDAO:
    model = CurrencyTick
    
    @classmethod
    async def add(cls, ticker: str, price: float, timestamp: int, session=None):
        if session is None:
            async with new_session() as session:
                return await cls._execute_add(session, ticker, price, timestamp)
        return await cls._execute_add(session, ticker, price, timestamp)

    @classmethod
    async def _execute_add(cls, session, ticker, price, timestamp):
        query = insert(cls.model).values(ticker=ticker, price=price, timestamp=timestamp)
        await session.execute(query)
        await session.commit()
        
    @classmethod
    async def find_all_by_ticker(cls, ticker: str, session=None):
        if session is None:
            async with new_session() as session:
                return await cls._execute_find_all(session, ticker)
        return await cls._execute_find_all(session, ticker)

    @classmethod
    async def _execute_find_all(cls, session, ticker):
        query = select(cls.model).filter_by(ticker=ticker)
        result = await session.execute(query)
        return result.scalars().all()
    
    @classmethod    
    async def find_latest(cls, ticker: str, session=None):
        if session is None:
            async with new_session() as session:
                return await cls._execute_find_latest(session, ticker)
        return await cls._execute_find_latest(session, ticker)

    @classmethod
    async def _execute_find_latest(cls, session, ticker):
        query = (
            select(cls.model)
            .filter_by(ticker=ticker)
            .order_by(cls.model.timestamp.desc())
            .limit(1)
        )
        result = await session.execute(query)
        return result.scalars().first()
        
    @classmethod
    async def find_by_date(cls, ticker: str, start_ts: int, end_ts: int, session=None):
        if session is None:
            async with new_session() as session:
                return await cls._execute_find_by_date(session, ticker, start_ts, end_ts)
        return await cls._execute_find_by_date(session, ticker, start_ts, end_ts)

    @classmethod
    async def _execute_find_by_date(cls, session, ticker, start_ts, end_ts):
        query = (
            select(cls.model)
            .filter(
                cls.model.ticker == ticker,
                cls.model.timestamp >= start_ts,
                cls.model.timestamp <= end_ts
            )
            .order_by(cls.model.timestamp.asc())
        )
        result = await session.execute(query)
        return result.scalars().all()