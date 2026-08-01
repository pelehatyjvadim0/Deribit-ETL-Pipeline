from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from deribit_etl.domain.models import Tick, Ticker
from deribit_etl.infrastructure.db.database import create_engine, create_session_factory
from deribit_etl.infrastructure.db.models import Base
from deribit_etl.infrastructure.db.repository import (
    SqlAlchemyTickRepository,
    SqlAlchemyUnitOfWork,
)


@pytest.mark.asyncio
async def test_list_returns_requested_ticker_newest_first() -> None:
    """Removing ticker filtering or descending timestamp ordering must fail."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            repository = SqlAlchemyTickRepository(session)
            for tick in (
                Tick(Ticker.BTC_USD, Decimal("62000.10"), 1_700_000_001_000),
                Tick(Ticker.ETH_USD, Decimal("3000.20"), 1_700_000_003_000),
                Tick(Ticker.BTC_USD, Decimal("62001.30"), 1_700_000_002_000),
            ):
                await repository.add(tick)
            await session.flush()

            ticks = await repository.list(Ticker.BTC_USD, limit=10, offset=0)

        assert [tick.timestamp for tick in ticks] == [
            1_700_000_002_000,
            1_700_000_001_000,
        ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_latest_returns_tick_with_greatest_timestamp() -> None:
    """Removing descending timestamp selection must return the wrong tick."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            repository = SqlAlchemyTickRepository(session)
            await repository.add(
                Tick(Ticker.ETH_USD, Decimal("3000.10"), 1_700_000_001_000)
            )
            await repository.add(
                Tick(Ticker.ETH_USD, Decimal("3001.20"), 1_700_000_002_000)
            )
            await session.flush()

            tick = await repository.latest(Ticker.ETH_USD)

        assert tick == Tick(
            Ticker.ETH_USD,
            Decimal("3001.20000000"),
            1_700_000_002_000,
        )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_in_range_is_inclusive_oldest_first_and_paginated() -> None:
    """Wrong range bounds, ordering, filtering, limit, or offset must fail."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            repository = SqlAlchemyTickRepository(session)
            for ticker, timestamp in (
                (Ticker.BTC_USD, 1_700_000_001_000),
                (Ticker.BTC_USD, 1_700_000_002_000),
                (Ticker.ETH_USD, 1_700_000_002_500),
                (Ticker.BTC_USD, 1_700_000_003_000),
                (Ticker.BTC_USD, 1_700_000_004_000),
                (Ticker.BTC_USD, 1_700_000_005_000),
            ):
                await repository.add(Tick(ticker, Decimal("100.00"), timestamp))
            await session.flush()

            ticks = await repository.in_range(
                Ticker.BTC_USD,
                start_timestamp=1_700_000_002_000,
                end_timestamp=1_700_000_004_000,
                limit=2,
                offset=1,
            )

        assert [tick.timestamp for tick in ticks] == [
            1_700_000_003_000,
            1_700_000_004_000,
        ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_queries_use_id_as_stable_timestamp_tie_breaker() -> None:
    """Timestamp-only ordering can duplicate or skip rows across offset pages."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    timestamp = 1_700_000_001_000
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            repository = SqlAlchemyTickRepository(session)
            await repository.add(Tick(Ticker.BTC_USD, Decimal("62000.00"), timestamp))
            await repository.add(Tick(Ticker.BTC_USD, Decimal("62001.00"), timestamp))
            await session.flush()

            newest_first = await repository.list(Ticker.BTC_USD, limit=10, offset=0)
            latest = await repository.latest(Ticker.BTC_USD)
            oldest_first = await repository.in_range(
                Ticker.BTC_USD,
                start_timestamp=timestamp,
                end_timestamp=timestamp,
                limit=10,
                offset=0,
            )

        assert [tick.price for tick in newest_first] == [
            Decimal("62001.00000000"),
            Decimal("62000.00000000"),
        ]
        assert latest is not None
        assert latest.price == Decimal("62001.00000000")
        assert [tick.price for tick in oldest_first] == [
            Decimal("62000.00000000"),
            Decimal("62001.00000000"),
        ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_only_unit_of_work_commits_the_session() -> None:
    """A repository commit would make the observed commit count greater than one."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            commit = AsyncMock(wraps=session.commit)
            session.commit = commit
            repository = SqlAlchemyTickRepository(session)
            unit_of_work = SqlAlchemyUnitOfWork(session)

            await repository.add(
                Tick(Ticker.BTC_USD, Decimal("62000.00"), 1_700_000_001_000)
            )
            await session.flush()
            await repository.list(Ticker.BTC_USD, limit=10, offset=0)
            await repository.latest(Ticker.BTC_USD)
            await repository.in_range(
                Ticker.BTC_USD,
                start_timestamp=1_700_000_001_000,
                end_timestamp=1_700_000_001_000,
                limit=10,
                offset=0,
            )
            await unit_of_work.commit()

            assert commit.await_count == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unit_of_work_rolls_back_pending_tick() -> None:
    """A missing rollback would leave the pending tick visible in the session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            repository = SqlAlchemyTickRepository(session)
            unit_of_work = SqlAlchemyUnitOfWork(session)
            await repository.add(
                Tick(Ticker.BTC_USD, Decimal("62000.00"), 1_700_000_001_000)
            )
            await session.flush()

            await unit_of_work.rollback()

            ticks = await repository.list(Ticker.BTC_USD, limit=10, offset=0)

        assert ticks == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_factories_create_usable_sessions() -> None:
    """A misbound engine or session factory would break the persistence round-trip."""
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = create_session_factory(engine)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            repository = SqlAlchemyTickRepository(session)
            await repository.add(
                Tick(Ticker.BTC_USD, Decimal("62000.00"), 1_700_000_001_000)
            )
            await SqlAlchemyUnitOfWork(session).commit()

        async with session_factory() as session:
            tick = await SqlAlchemyTickRepository(session).latest(Ticker.BTC_USD)

        assert tick == Tick(
            Ticker.BTC_USD,
            Decimal("62000.00000000"),
            1_700_000_001_000,
        )
    finally:
        await engine.dispose()
