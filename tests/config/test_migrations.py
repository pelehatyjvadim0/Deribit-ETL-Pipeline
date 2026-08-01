"""Executable checks for the Alembic migration environment."""

import os
import subprocess
import sys
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from deribit_etl.infrastructure.db.models import Base
from deribit_etl.settings import Settings


PROJECT_ROOT = Path(__file__).parents[2]


def test_only_canonical_environment_example_is_present_and_loadable(monkeypatch) -> None:
    """A stale alternate sample can configure the removed legacy application."""
    canonical_example = PROJECT_ROOT / ".env.example"

    assert canonical_example.is_file()
    assert not (PROJECT_ROOT / ".env_example").exists()

    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
    settings = Settings(_env_file=canonical_example)
    assert settings.postgres_db == "deribit"
    assert settings.deribit_base_url == "https://www.deribit.com/api/v2"


def test_migrations_render_offline_with_example_configuration() -> None:
    """Catch stale package imports or runtime-only database configuration."""
    environment = os.environ.copy()
    for line in (PROJECT_ROOT / ".env.example").read_text().splitlines():
        if line and not line.startswith("#"):
            name, value = line.split("=", maxsplit=1)
            environment[name] = value

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "CREATE TABLE ticks" in result.stdout


def test_migration_head_matches_orm_metadata() -> None:
    """An applied migration head must not drift from the runtime ORM schema."""
    alembic_config = Config(PROJECT_ROOT / "alembic.ini")
    revisions = list(
        ScriptDirectory.from_config(alembic_config).walk_revisions(
            base="base", head="heads"
        )
    )
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            migration_context = MigrationContext.configure(
                connection,
                opts={"compare_type": True},
            )
            with Operations.context(migration_context):
                for revision in reversed(revisions):
                    revision.module.upgrade()

            assert compare_metadata(migration_context, Base.metadata) == []
            migrated_columns = {
                column["name"]: column
                for column in inspect(connection).get_columns("ticks")
            }
            mapped_ticker = Base.metadata.tables["ticks"].c.ticker
            assert migrated_columns["ticker"]["type"].length == mapped_ticker.type.length
    finally:
        engine.dispose()
