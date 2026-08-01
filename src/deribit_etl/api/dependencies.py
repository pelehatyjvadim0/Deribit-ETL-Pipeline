"""FastAPI dependency wiring for application and infrastructure adapters."""

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from deribit_etl.application.ingest import UnitOfWork
from deribit_etl.application.prices import PriceQueries
from deribit_etl.infrastructure.db.repository import (
    SqlAlchemyTickRepository,
    SqlAlchemyUnitOfWork,
)


@dataclass(frozen=True)
class ApplicationServices:
    """Request-scoped application use cases sharing one transaction boundary."""

    prices: PriceQueries
    unit_of_work: UnitOfWork


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide one caller-owned database session per HTTP request."""
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_application_services(session: SessionDep) -> ApplicationServices:
    repository = SqlAlchemyTickRepository(session)
    return ApplicationServices(
        prices=PriceQueries(repository),
        unit_of_work=SqlAlchemyUnitOfWork(session),
    )


ApplicationServicesDep = Annotated[ApplicationServices, Depends(get_application_services)]


def get_current_time_ms() -> int:
    return int(time.time() * 1_000)


CurrentTimeDep = Annotated[int, Depends(get_current_time_ms)]


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Inject the HTTP client owned by the application lifespan."""
    return request.app.state.http_client


HttpClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]


async def health_readiness_probe(session: SessionDep) -> None:
    """Verify database readiness without returning connection details."""
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready",
        ) from error
