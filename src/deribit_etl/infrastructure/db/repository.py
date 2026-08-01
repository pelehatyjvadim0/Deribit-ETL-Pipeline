"""SQLAlchemy implementation of quote storage ports."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from deribit_etl.domain.models import Tick, Ticker
from deribit_etl.infrastructure.db.errors import DatabaseOperationError
from deribit_etl.infrastructure.db.models import TickRecord


class SqlAlchemyTickRepository:
    """Store and retrieve quotes through a caller-owned session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, tick: Tick) -> None:
        self._session.add(
            TickRecord(
                ticker=tick.ticker.value,
                price=tick.price,
                timestamp=tick.timestamp,
            )
        )

    async def list(self, ticker: Ticker, *, limit: int, offset: int) -> Sequence[Tick]:
        statement = (
            select(TickRecord)
            .where(TickRecord.ticker == ticker.value)
            .order_by(TickRecord.timestamp.desc(), TickRecord.id.desc())
            .limit(limit)
            .offset(offset)
        )
        records = (await self._session.scalars(statement)).all()
        return [self._to_domain(record) for record in records]

    async def latest(self, ticker: Ticker) -> Tick | None:
        statement = (
            select(TickRecord)
            .where(TickRecord.ticker == ticker.value)
            .order_by(TickRecord.timestamp.desc(), TickRecord.id.desc())
            .limit(1)
        )
        record = (await self._session.scalars(statement)).first()
        return None if record is None else self._to_domain(record)

    async def in_range(
        self,
        ticker: Ticker,
        *,
        start_timestamp: int,
        end_timestamp: int,
        limit: int,
        offset: int,
    ) -> Sequence[Tick]:
        statement = (
            select(TickRecord)
            .where(
                TickRecord.ticker == ticker.value,
                TickRecord.timestamp >= start_timestamp,
                TickRecord.timestamp <= end_timestamp,
            )
            .order_by(TickRecord.timestamp.asc(), TickRecord.id.asc())
            .limit(limit)
            .offset(offset)
        )
        records = (await self._session.scalars(statement)).all()
        return [self._to_domain(record) for record in records]

    @staticmethod
    def _to_domain(record: TickRecord) -> Tick:
        return Tick(
            ticker=Ticker(record.ticker),
            price=record.price,
            timestamp=record.timestamp,
        )


class SqlAlchemyUnitOfWork:
    """Transaction operations for a caller-owned SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except (SQLAlchemyError, OSError) as error:
            raise DatabaseOperationError("Database commit failed") from error

    async def rollback(self) -> None:
        await self._session.rollback()
