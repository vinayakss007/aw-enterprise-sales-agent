"""
Observability middleware for API requests.
Collects metrics and adds structured logging to every request.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse
from app.observability.metrics import api_requests_total, api_request_duration
from app.observability.tracing import tracer
import time
import logging


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect Prometheus metrics for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        tenant_id = request.headers.get("X-Tenant-Id", "unknown")
        method = request.method
        path = request.url.path

        try:
            response: StarletteResponse = await call_next(request)
            duration = time.time() - start_time

            api_requests_total.labels(
                method=method, endpoint=path,
                status_code=response.status_code, tenant_id=tenant_id
            ).inc()
            api_request_duration.labels(
                method=method, endpoint=path, tenant_id=tenant_id
            ).observe(duration)

            return response
        except Exception:
            duration = time.time() - start_time
            api_requests_total.labels(
                method=method, endpoint=path, status_code=500, tenant_id=tenant_id
            ).inc()
            api_request_duration.labels(
                method=method, endpoint=path, tenant_id=tenant_id
            ).observe(duration)
            raise


class TracingMiddleware(BaseHTTPMiddleware):
    """Add distributed tracing spans (no-op if OTEL unavailable)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            tenant_id = request.headers.get("X-Tenant-Id", "unknown")
            span.set_attribute("tenant.id", tenant_id)

            try:
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                return response
            except Exception as e:
                span.set_attribute("http.status_code", 500)
                span.set_attribute("exception.message", str(e))
                raise


class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured JSON logging for every request."""

    def __init__(self, app, logger_instance: logging.Logger = None):
        super().__init__(app)
        self.logger = logger_instance or logging.getLogger("api.access")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "-")

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            self.logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "tenant_id": request.headers.get("X-Tenant-Id", "unknown"),
                },
            )
            return response
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                    "tenant_id": request.headers.get("X-Tenant-Id", "unknown"),
                },
            )
            raise
