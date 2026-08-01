"""Executable checks for the Alembic migration environment."""

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]


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
