# Deribit ETL Pipeline Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Deribit ETL service reproducible, explicitly layered, and ready for public GitHub review without changing its documented read API.

**Architecture:** A staged migration introduces framework-free domain and application code first, then uses SQLAlchemy, httpx, FastAPI, and Celery as adapters. One caller controls every transaction and one Celery boundary controls every async lifecycle.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy async, PostgreSQL, httpx, Celery, Redis, Alembic, uv, Ruff, Pyright, pytest, Docker Compose.

## Global Constraints

- Store and expose timestamps as Unix milliseconds; accept whole-second request timestamps by converting them once.
- Keep GET `/prices/`, `/prices/{ticker}/latest`, and `/prices/filter` response shapes and 404 semantics.
- Never commit `.env`, credentials, databases, coverage output, or host bind mounts.
- Do not claim an unverified coverage percentage.
- Keep each commit focused and use a Russian imperative commit message.

---

## File map

- `src/deribit_etl/domain/*`: types, port protocols, upstream errors.
- `src/deribit_etl/application/*`: ingestion and price-query use cases.
- `src/deribit_etl/infrastructure/db/*`: engine, ORM model, repository and transaction scope.
- `src/deribit_etl/infrastructure/deribit/*`: HTTP mapping and retry policy.
- `src/deribit_etl/infrastructure/tasks/*`: Celery construction and synchronous task boundary.
- `src/deribit_etl/api/*`, `src/deribit_etl/main.py`: FastAPI dependencies, routes, lifespan and health check.
- `tests/unit/*`, `tests/integration/*`: domain/application and adapter/API contracts.

### Task 1: Tooling and reproducible configuration

**Files:** Create `pyproject.toml`, `.env.example`, `.pre-commit-config.yaml`; modify `.gitignore`, `pytest.ini`; delete `requirements.txt` only after `uv.lock` is generated.

- [ ] Write a failing command test: `uv run ruff check .` must initially fail because no project configuration exists.
- [ ] Add `pyproject.toml` with runtime dependencies (`fastapi`, `uvicorn`, `httpx`, `sqlalchemy[asyncio]`, `asyncpg`, `aiosqlite`, `alembic`, `celery`, `redis`, `pydantic-settings`) and dev dependencies (`pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `pyright`, `pre-commit`).
- [ ] Generate `uv.lock`; configure Ruff and Pyright with `src` layout; make pytest collect `tests` and measure `deribit_etl`.
- [ ] Add `.env.example` using only `POSTGRES_*`, `REDIS_*`, `DERIBIT_BASE_URL`, timeout, retry, and log-level development values.
- [ ] Run `uv run ruff check .`, `uv run pyright`, and `uv run pytest`; commit `chore: настрой инструменты разработки`.

### Task 2: Domain types and request timestamp contract

**Files:** Create `src/deribit_etl/domain/models.py`, `ports.py`, `errors.py`; test `tests/unit/domain/test_models.py`.

- [ ] Write parameterized failing tests asserting `normalize_timestamp(1_700_000_000) == 1_700_000_000_000`, preserving milliseconds, and rejecting `> 10**14`.
- [ ] Implement `Ticker(str, Enum)`, frozen `Tick(ticker, price, timestamp)`, `normalize_timestamp`, `PriceProvider.fetch(Ticker) -> Tick`, and repository protocols.
- [ ] Run the focused test, then the full suite; commit `feat: выдели доменные типы котировок`.

### Task 3: Application use cases and transaction boundary

**Files:** Create `src/deribit_etl/application/ingest.py`, `prices.py`; test `tests/unit/application/test_ingest.py`, `test_prices.py`.

- [ ] Write failing fake-port tests: a successful two-ticker ingest calls `add` for both and commits once; an upstream error is collected per ticker; a database error rolls back and is raised.
- [ ] Implement `IngestPrices.run(tickers)` and `PriceQueries.list/latest/in_range`; application receives ports and a unit-of-work protocol rather than SQLAlchemy objects.
- [ ] Run focused and complete tests; commit `feat: добавь use cases для котировок`.

### Task 4: SQLAlchemy and Deribit adapters

**Files:** Create `src/deribit_etl/infrastructure/db/{database,models,repository}.py`, `src/deribit_etl/infrastructure/deribit/client.py`; test `tests/integration/test_repository.py`, `tests/unit/infrastructure/test_deribit_client.py`.

- [ ] Write failing adapter tests for ordered repository queries, no repository commit, timeout mapping, HTTP 5xx retry limit, malformed JSON mapping, and microsecond timestamp normalization.
- [ ] Implement async engine/session factory, `SqlAlchemyTickRepository`, `SqlAlchemyUnitOfWork`, and `DeribitPriceProvider` using a dependency-injected `httpx.AsyncClient`.
- [ ] Run adapter tests and full suite; commit `feat: подключи адаптеры базы и Deribit`.

### Task 5: FastAPI and Celery entry points

**Files:** Create `src/deribit_etl/api/{dependencies,router,schemas}.py`, `src/deribit_etl/infrastructure/tasks/{celery,tasks}.py`, `src/deribit_etl/{settings,main}.py`; test `tests/integration/test_api.py`, `tests/unit/infrastructure/test_tasks.py`.

- [ ] Write failing route tests for millisecond normalization, 404 responses, `/health`, and invalid future ranges; write a task test proving the async runner and engine disposal run exactly once.
- [ ] Implement lifespan-owned HTTP client, per-request unit of work, route-to-use-case mapping, health readiness probe, and Celery task with `asyncio.run()` plus `finally: dispose()`.
- [ ] Run focused and full tests; commit `feat: подключи API и планировщик ingestion`.

### Task 6: Migration, containers, CI, and documentation

**Files:** Modify `alembic.ini`, `migrations/env.py`; create `.github/workflows/ci.yml`, `docs/architecture.md`, `LICENSE`; replace `Dockerfile`, `docker-compose.yaml`, `README.md`; remove legacy `app/` and old tests only after replacement tests pass.

- [ ] Write a compose configuration check that succeeds with `.env.example` and `docker compose config`.
- [ ] Point Alembic metadata and all commands to `deribit_etl`; add an API startup command that runs `alembic upgrade head` before Uvicorn.
- [ ] Build Compose services without fixed names or bind mounts; expose only API port and add health checks/dependencies for PostgreSQL and Redis.
- [ ] Add CI jobs for `uv sync --locked`, Ruff, Pyright, pytest, and coverage artifact; add concise factual README, architecture diagram, limitations, and MIT license.
- [ ] Run `uv run ruff check .`, `uv run pyright`, `uv run pytest`, `docker compose --env-file .env.example config`, and `docker compose up --build`; commit `chore: подготовь проект к публикации`.

### Task 7: Final review and GitHub handoff

**Files:** Review every changed file; no feature files expected.

- [ ] Run `git diff main...HEAD --check` and inspect `git status --short` for secrets and generated artifacts.
- [ ] Re-run the complete lint, type, test, and Compose verification commands from Task 6.
- [ ] Review README claims against command output and CI configuration.
- [ ] Commit only any review corrections; prepare the branch for a pull request without pushing it.
