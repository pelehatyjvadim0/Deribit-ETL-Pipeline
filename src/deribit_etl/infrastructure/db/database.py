"""Construction helpers for async SQLAlchemy resources."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async engine without opening a connection eagerly."""
    return create_async_engine(database_url, echo=echo)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Bind sessions to an engine while retaining loaded state after commit."""
    return async_sessionmaker(engine, expire_on_commit=False)
