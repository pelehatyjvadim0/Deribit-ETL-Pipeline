<div align="center">
  <img width="100%" alt="Deribit ETL Pipeline" src="https://capsule-render.vercel.app/api?type=rect&color=0:F8FAFC,100:E2E8F0&height=180&section=header&text=Deribit%20ETL%20Pipeline&fontSize=57&fontColor=0F172A&fontAlignY=40&desc=Small%20service.%20Clear%20contracts.%20Reproducible%20startup.&descAlignY=64&descSize=16" />

  <a href="#http-api"><img alt="Ticks BTC and ETH" src="https://img.shields.io/badge/TICKS-BTC__USD%20%2B%20ETH__USD-475569?style=for-the-badge&labelColor=1E293B" /></a>
  <a href="#architecture-and-limitations"><img alt="Scheduler Celery Beat" src="https://img.shields.io/badge/SCHEDULER-CELERY%20BEAT-64748B?style=for-the-badge&labelColor=334155" /></a>

  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=650&size=16&pause=1900&color=334155&center=true&vCenter=true&width=720&lines=Price+observations%2C+not+trading+advice." alt="Price observations not trading advice" />
</div>

The service periodically fetches `BTC_USD` and `ETH_USD` index prices from the
public Deribit API, stores observations in PostgreSQL, and exposes a read-only
HTTP API. Celery Beat schedules ingestion through Redis, Celery Worker runs it,
and FastAPI serves read queries.

This is not a trading system, a price guarantee, or financial advice.

## Quick start

Docker and Docker Compose are required. The example configuration contains
local development values only:

```bash
docker compose --env-file .env.example up --build
```

Before starting the API, its container runs `alembic upgrade head`. The API is
available at `http://localhost:8000`, the OpenAPI UI at
`http://localhost:8000/docs`, and readiness at `http://localhost:8000/health`.

To override values, copy the example into the Git-ignored `.env` file:

```bash
cp .env.example .env
docker compose up --build
```

Stopping the services preserves the named PostgreSQL volume:

```bash
docker compose down
```

## HTTP API

All stored and returned timestamps are Unix milliseconds. Request parameters
also accept whole Unix seconds and normalize them once at the API boundary.

```http
GET /prices/?ticker=btc_usd&limit=10&offset=0
GET /prices/btc_usd/latest
GET /prices/filter?ticker=btc_usd&start_timestamp=1700000000&end_timestamp=1700000010
```

Response items have this shape:

```json
{"ticker":"btc_usd","price":"62000.50","timestamp":1700000005000}
```

`/prices/` and `/prices/{ticker}/latest` return `404` when no data is found.
`/prices/filter` returns a list, rejects invalid ranges, and rejects a range
whose start is more than 60 seconds in the future. Supported tickers are
`btc_usd` and `eth_usd`.

## Development and verification

The project uses Python 3.12 and locked `uv` dependencies:

```bash
uv sync --locked
uv lock --check
uv run ruff check .
uv run pyright
uv run pytest
docker compose --env-file .env.example config
```

CI repeats the locked installation, lint, type check, and tests, then stores an
XML coverage report as an artifact. The documentation intentionally does not
state a permanent coverage percentage: it must be backed by a specific run.

## Architecture and limitations

Layers, dependency direction, transactions, and resource lifecycles are
described in [docs/architecture.md](docs/architecture.md).

Current limitations:

- only `BTC_USD` and `ETH_USD` index prices are collected;
- there is no authentication, rate limiting, metrics, or historical backfill;
- API readiness checks PostgreSQL, not Deribit availability;
- the local Compose setup is sized for one API, one worker, and one beat.

## License

[MIT](LICENSE)
