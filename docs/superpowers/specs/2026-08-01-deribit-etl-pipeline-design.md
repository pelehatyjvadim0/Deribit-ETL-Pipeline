# Deribit ETL Pipeline — design

## Purpose and scope

This portfolio service periodically reads BTC/USD and ETH/USD index prices from
Deribit, persists ticks, and exposes read-only HTTP endpoints. It is not a
trading system, a price guarantee, or financial advice. The refactor preserves
the three existing `/prices` API contracts while making the ingestion path,
transactions, configuration, and local startup reproducible.

## Baseline

On 2026-08-01 the existing suite passed: 32 tests. Its displayed 100% coverage
is not a repository-wide measure: `app.external_api` and `app.tasks` are not
imported by the test run. README must not claim this metric until CI measures
the new package as a whole. `docker compose` was not started because the
worktree deliberately contains no local `.env`; the new configuration will
provide safe defaults and a committed `.env.example`.

## Options considered

1. **Big-bang move to a new `src` package.** It produces the target tree
   quickly, but breaks Alembic, Celery import paths, and tests at once. The
   resulting failures are difficult to attribute and rollback.
2. **Compatibility wrappers around the existing `app` package.** This is safe
   initially, but leaves two public module trees and delays the architectural
   goal.
3. **Staged strangler migration (selected).** Build the new `src/deribit_etl`
   domain and application boundary behind tested interfaces; then make FastAPI,
   Celery, database, and Deribit adapters depend on those interfaces. Remove
   the legacy package only after every entry point and migration references the
   new package. Each commit is independently testable and reversible.

## Architecture

`domain` contains immutable `Tick` and `Ticker` types, `TickRepository` and
`PriceProvider` protocols, and typed upstream errors. `application` owns
`IngestPrices` and query use cases. It is framework-independent.

`infrastructure` implements those ports: an `httpx.AsyncClient`-based Deribit
adapter, SQLAlchemy async repository, and Celery integration. The API creates
repositories via dependencies and invokes use cases; it does not issue ORM
queries. A Celery task owns one `asyncio.run()` call and disposes its engine in
`finally`; the use case owns no event loop and no database session.

```text
FastAPI routes ──────┐
Celery task ─────────┼─> application use cases ─> domain ports
                     │                               │
                     └──────── infrastructure adapters ┘
                              (SQLAlchemy, httpx, Redis)
```

## Data and failure rules

- All stored timestamps are Unix milliseconds. Request timestamps supplied in
  seconds are multiplied by 1,000; already-millisecond values are returned
  unchanged; values above `10**14` are rejected.
- A repository accepts an `AsyncSession` supplied by its caller and never
  commits it. The application transaction wrapper commits once after a complete
  ingestion batch and rolls back on failure.
- The Deribit adapter uses a bounded timeout and a finite retry policy only for
  transient transport errors and 5xx responses. It raises `UpstreamTimeout`,
  `UpstreamUnavailable`, or `InvalidUpstreamResponse`; it never returns a
  silently ambiguous `None`.
- Scheduled ingestion logs structured event fields (ticker, timestamp, error
  class) and continues with other tickers after an upstream failure. Database
  failures fail the task so Celery can report/retry them.
- `/health` reports readiness without leaking configuration, credentials, or
  upstream response bodies.

## Delivery and safety

The repository moves to `pyproject.toml` with `uv.lock`, Ruff, Pyright,
pytest, pre-commit, CI, Docker Compose health checks, no host bind mount, no
fixed container names, and only the application port exposed. `.env.example`
contains placeholders and local development values only. No `.env`, database,
coverage artifact, personal contacts, or screenshot is committed.

## Acceptance criteria

- `uv run ruff check .`, `uv run pyright`, and `uv run pytest` pass locally.
- CI performs the same checks and stores coverage as an artifact without
  publishing an unsupported percentage.
- `docker compose up --build` applies migrations before serving the API and
  waits for PostgreSQL and Redis health checks.
- Documentation describes verified commands, endpoint examples, architecture,
  limitations, and MIT license terms in concise, factual language.
