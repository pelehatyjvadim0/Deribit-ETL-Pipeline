"""Alembic environment for the asynchronous PostgreSQL database."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

from deribit_etl.infrastructure.db.models import Base
from deribit_etl.settings import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
# Alembic's ConfigParser treats percent signs in escaped passwords as interpolation.
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Render migrations without creating a database connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(engine: AsyncEngine) -> None:
    try:
        async with engine.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await engine.dispose()


def run_migrations_online() -> None:
    """Apply migrations through SQLAlchemy's async engine."""
    section = config.get_section(config.config_ini_section) or {}
    engine = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    asyncio.run(run_async_migrations(engine))


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
