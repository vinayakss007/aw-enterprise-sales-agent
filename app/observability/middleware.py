import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse

from app.observability.metrics import api_request_duration, api_requests_total
from app.observability.tracing import tracer


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect API metrics
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Get tenant ID from headers
        tenant_id = request.headers.get("X-Tenant-Id", "unknown")
        
        # Get request details
        method = request.method
        path = request.url.path
        
        try:
            response: StarletteResponse = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            api_requests_total.labels(
                method=method,
                endpoint=path,
                status_code=response.status_code,
                tenant_id=tenant_id
            ).inc()
            
            api_request_duration.labels(
                method=method,
                endpoint=path,
                tenant_id=tenant_id
            ).observe(duration)
            
            return response
        except Exception:
            # Calculate duration for error case
            duration = time.time() - start_time
            
            # Record metrics for error
            api_requests_total.labels(
                method=method,
                endpoint=path,
                status_code=500,
                tenant_id=tenant_id
            ).inc()
            
            api_request_duration.labels(
                method=method,
                endpoint=path,
                tenant_id=tenant_id
            ).observe(duration)
            
            raise

class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add tracing to requests
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        with tracer.start_as_current_span(f"request_{request.method}_{request.url.path}") as span:
            # Add request attributes to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
            span.set_attribute("http.client_ip", request.client.host if request.client else "")
            
            # Get tenant ID
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
    """
    Middleware to add structured logging to requests
    """
    def __init__(self, app, logger: logging.Logger = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # Log request start
        self.logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url),
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": request.client.host if request.client else "",
                "tenant_id": request.headers.get("X-Tenant-Id", "unknown")
            }
        )
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            
            # Log response
            self.logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url),
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "tenant_id": request.headers.get("X-Tenant-Id", "unknown")
                }
            )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            self.logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url),
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                    "tenant_id": request.headers.get("X-Tenant-Id", "unknown")
                }
            )
            
            raise