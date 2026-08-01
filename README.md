<div align="center">
  <img width="100%" alt="Deribit ETL Pipeline" src="https://capsule-render.vercel.app/api?type=rect&color=0:F8FAFC,100:E2E8F0&height=180&section=header&text=Deribit%20ETL%20Pipeline&fontSize=57&fontColor=0F172A&fontAlignY=40&desc=Small%20service.%20Clear%20contracts.%20Reproducible%20startup.&descAlignY=64&descSize=16" />

  <a href="#http-api"><img alt="Ticks BTC and ETH" src="https://img.shields.io/badge/TICKS-BTC__USD%20%2B%20ETH__USD-475569?style=for-the-badge&labelColor=1E293B" /></a>
  <a href="#архитектура-и-ограничения"><img alt="Scheduler Celery Beat" src="https://img.shields.io/badge/SCHEDULER-CELERY%20BEAT-64748B?style=for-the-badge&labelColor=334155" /></a>

  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=650&size=16&pause=1900&color=334155&center=true&vCenter=true&width=720&lines=Price+observations%2C+not+trading+advice." alt="Price observations not trading advice" />
</div>

Сервис периодически получает индексные цены `BTC_USD` и `ETH_USD` из
публичного API Deribit, сохраняет наблюдения в PostgreSQL и предоставляет
read-only HTTP API. Celery Beat ставит задачу сбора в Redis, Celery Worker
выполняет её, а FastAPI обслуживает запросы на чтение.

Сервис не является торговой системой, гарантией цены или финансовой
рекомендацией.

## Быстрый запуск

Нужны Docker и Docker Compose. Пример конфигурации содержит только локальные
значения для разработки:

```bash
docker compose --env-file .env.example up --build
```

Перед запуском API контейнер выполняет `alembic upgrade head`. API доступен на
`http://localhost:8000`, OpenAPI UI — на `http://localhost:8000/docs`, проверка
готовности — на `http://localhost:8000/health`.

Чтобы изменить значения, скопируйте пример в игнорируемый Git файл `.env`:

```bash
cp .env.example .env
docker compose up --build
```

Остановка сервисов сохраняет именованный том PostgreSQL:

```bash
docker compose down
```

## HTTP API

Все сохранённые и возвращаемые timestamps — Unix-время в миллисекундах.
Параметры запроса допускают целые Unix-секунды и нормализуют их один раз на
границе API.

```http
GET /prices/?ticker=btc_usd&limit=10&offset=0
GET /prices/btc_usd/latest
GET /prices/filter?ticker=btc_usd&start_timestamp=1700000000&end_timestamp=1700000010
```

Элемент ответа имеет форму:

```json
{"ticker":"btc_usd","price":"62000.50","timestamp":1700000005000}
```

`/prices/` и `/prices/{ticker}/latest` возвращают `404`, если данных нет.
`/prices/filter` возвращает список, отклоняет неверный диапазон и
его начало более чем на 60 секунд в будущем.
Допустимые тикеры: `btc_usd` и `eth_usd`.

## Разработка и проверки

Проект использует Python 3.12 и зафиксированные зависимости `uv`:

```bash
uv sync --locked
uv lock --check
uv run ruff check .
uv run pyright
uv run pytest
docker compose --env-file .env.example config
```

CI повторяет установку из lock-файла, lint, type-check, тесты и сохраняет XML
отчёт покрытия как artifact. Процент покрытия в документации намеренно не
фиксируется: он должен подтверждаться конкретным запуском.

## Архитектура и ограничения

Слои, направления зависимостей, транзакции и жизненный цикл ресурсов описаны в
[docs/architecture.md](docs/architecture.md).

Текущие ограничения:

- только индексные цены `BTC_USD` и `ETH_USD`;
- нет авторизации, rate limiting, метрик и исторического backfill;
- готовность API проверяет PostgreSQL, но не доступность Deribit;
- локальная Compose-конфигурация рассчитана на один API, один worker и один beat.

## Лицензия

[MIT](LICENSE)
