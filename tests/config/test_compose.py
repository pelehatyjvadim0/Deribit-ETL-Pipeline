"""Behavior checks for the rendered Docker Compose application."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


PROJECT_ROOT = Path(__file__).parents[2]


def _render_compose() -> dict[str, Any]:
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is unavailable")

    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            ".env.example",
            "config",
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"docker compose config failed:\n{result.stderr}")
    return json.loads(result.stdout)


def test_compose_renders_a_private_health_gated_stack() -> None:
    """Catch accidental host exposure, bind mounts, and premature starts."""
    config = _render_compose()
    services = config["services"]

    assert set(config["volumes"]) == {"postgres_data"}
    assert services["postgres"]["volumes"][0]["source"] == "postgres_data"
    assert {"api", "beat", "postgres", "redis", "worker"} <= set(services)
    assert all("container_name" not in service for service in services.values())
    assert all(
        mount["type"] != "bind"
        for service in services.values()
        for mount in service.get("volumes", [])
    )

    published_services = {
        name for name, service in services.items() if service.get("ports")
    }
    assert published_services == {"api"}
    api_ports = services["api"]["ports"]
    assert len(api_ports) == 1
    assert api_ports[0]["target"] == 8000
    assert str(api_ports[0]["published"]) == "8000"

    assert "healthcheck" in services["postgres"]
    assert "healthcheck" in services["redis"]
    for name in ("api", "beat", "worker"):
        dependencies = services[name]["depends_on"]
        assert dependencies["postgres"]["condition"] == "service_healthy"
        assert dependencies["redis"]["condition"] == "service_healthy"

    configured_command = services["api"]["command"]
    api_command = (
        " ".join(configured_command)
        if isinstance(configured_command, list)
        else configured_command
    )
    assert api_command.index("alembic upgrade head") < api_command.index(
        "uvicorn deribit_etl.main:app"
    )
