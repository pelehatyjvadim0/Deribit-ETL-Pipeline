# Deribit ETL Pipeline

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
`/prices/filter` возвращает список и отклоняет неверный или будущий диапазон.
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
