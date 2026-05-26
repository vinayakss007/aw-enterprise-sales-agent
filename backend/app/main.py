"""Application entry point."""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.observability.health import router as health_router
from app.observability.middleware import MetricsMiddleware, TracingMiddleware, LoggingMiddleware
from app.observability.logging import setup_logging
from app.observability.tracing import instrument_app
from app.observability.alerting import ALERT_MANAGER
from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Logging
    setup_logging()

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # CORS
    if settings.backend_cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.backend_cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Observability middleware (order matters: last added = first executed)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(TracingMiddleware)

    # Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(health_router, prefix=settings.API_V1_STR)

    # OpenTelemetry instrumentation (no-op if disabled)
    instrument_app(app)

    @app.on_event("startup")
    async def startup_event():
        # Create tables (dev convenience — production uses Alembic)
        if settings.DEBUG:
            from app.db.session import engine
            from app.db.base import Base
            from app.db.models import *  # noqa: ensure all models registered
            Base.metadata.create_all(bind=engine)

        # Start alert monitoring
        asyncio.create_task(ALERT_MANAGER.start_monitoring())

    @app.on_event("shutdown")
    async def shutdown_event():
        ALERT_MANAGER.stop_monitoring()

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
