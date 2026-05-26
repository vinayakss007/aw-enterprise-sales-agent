"""FastAPI application factory.

Uses the modern ``lifespan`` context manager (``@app.on_event`` was deprecated
in FastAPI 0.93). Optional observability (OpenTelemetry tracing, alert manager)
is wired up only when explicitly enabled, so the minimal install path works
without a stack of optional dependencies.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.observability.alerting import ALERT_MANAGER
from app.observability.health import router as health_router
from app.observability.logging import setup_logging
from app.observability.middleware import (
    LoggingMiddleware,
    MetricsMiddleware,
    TracingMiddleware,
)
from app.observability.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start-up and shut-down hooks for the application."""
    # Optional: provision schema on first boot. In production this is owned by
    # Alembic; we keep ``create_all`` only as a developer convenience and only
    # when DEBUG is on.
    if settings.DEBUG:
        try:
            from app.db import models  # noqa: F401  (import side effect)
            from app.db.base import Base
            from app.db.session import engine

            await asyncio.to_thread(Base.metadata.create_all, engine)
        except Exception as exc:  # pragma: no cover — best effort
            logger.warning("Skipping create_all: %s", exc)

    monitor_task = asyncio.create_task(ALERT_MANAGER.start_monitoring())
    try:
        yield
    finally:
        ALERT_MANAGER.stop_monitoring()
        monitor_task.cancel()
        try:
            await monitor_task
        except (asyncio.CancelledError, Exception):
            pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    if settings.backend_cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.backend_cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(TracingMiddleware)
    from app.observability.rate_limit import build_default_limiter

    app.add_middleware(
        RateLimitMiddleware,
        limit=settings.RATE_LIMIT_REQUESTS,
        window=settings.RATE_LIMIT_WINDOW,
        limiter=build_default_limiter(settings.REDIS_URL),
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(health_router, prefix=settings.API_V1_STR)

    if settings.TRACING_ENABLED:
        try:
            from app.observability.tracing import instrument_app

            instrument_app(app)
        except Exception as exc:  # pragma: no cover
            logger.warning("Tracing disabled — failed to instrument app: %s", exc)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
