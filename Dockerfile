# syntax=docker/dockerfile:1.7
FROM python:3.12.11-slim-bookworm

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --root-user-action=ignore uv==0.11.8
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn deribit_etl.main:app --host 0.0.0.0 --port 8000 --log-level ${LOG_LEVEL:-info}"]
