"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI

from deribit_etl.api.dependencies import health_readiness_probe
from deribit_etl.api.router import router as price_router
from deribit_etl.api.schemas import HealthResponse
from deribit_etl.infrastructure.db.database import create_engine, create_session_factory
from deribit_etl.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct the API while deferring resources to its lifespan."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        config = settings or get_settings()
        engine = create_engine(config.database_url)
        http_client = httpx.AsyncClient()
        application.state.settings = config
        application.state.engine = engine
        application.state.session_factory = create_session_factory(engine)
        application.state.http_client = http_client
        try:
            yield
        finally:
            await http_client.aclose()
            await engine.dispose()

    application = FastAPI(
        title="Deribit-ETL-Pipeline",
        description="Сервис для мониторинга курсов криптовалют",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.include_router(price_router)

    @application.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health(_: None = Depends(health_readiness_probe)) -> HealthResponse:
        return HealthResponse(status="ok")

    @application.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        return {
            "status": "working",
            "docs": "/docs",
            "message": "Welcome to Deribit-ETL-Pipeline",
        }

    return application


app = create_app()
