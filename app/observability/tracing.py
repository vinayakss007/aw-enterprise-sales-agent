"""Tracing helpers.

OpenTelemetry is treated as an optional dependency. When the OTel packages are
not installed (or ``TRACING_ENABLED`` is false in settings) the public
``tracer``, ``instrument_app``, ``trace_agent_execution`` and ``trace_step``
become no-ops, which lets the rest of the app import without hard requirements
on the OTel stack.
"""
from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

try:  # pragma: no cover — optional dependency
    from opentelemetry import trace as _otel_trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
    except Exception:  # pragma: no cover
        OTLPSpanExporter = None  # type: ignore[assignment]

    _OTEL_AVAILABLE = True
except Exception:  # pragma: no cover
    _otel_trace = None  # type: ignore[assignment]
    _OTEL_AVAILABLE = False


class _NoopSpan:
    def __enter__(self) -> _NoopSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def set_attribute(self, *args: Any, **kwargs: Any) -> None:
        return None


class _NoopTracer:
    @contextmanager
    def start_as_current_span(self, *args: Any, **kwargs: Any) -> Iterator[_NoopSpan]:
        yield _NoopSpan()


if _OTEL_AVAILABLE:
    _provider = TracerProvider()
    _otel_trace.set_tracer_provider(_provider)
    _otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if _otlp_endpoint and OTLPSpanExporter is not None:
        try:
            _provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=_otlp_endpoint))
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to configure OTLP exporter: %s", exc)
    tracer: Any = _otel_trace.get_tracer(__name__)
else:
    tracer = _NoopTracer()


def instrument_app(app: Any) -> None:
    """Auto-instrument the FastAPI app and common libraries when OTel exists."""
    if not _OTEL_AVAILABLE:
        return
    try:  # pragma: no cover — optional
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        RequestsInstrumentor().instrument()
    except Exception as exc:  # pragma: no cover
        logger.warning("OTel instrumentation skipped: %s", exc)


def trace_agent_execution(agent_type: str, tenant_id: str, lead_id: str):
    """Decorator that wraps an async callable in a span (no-op if OTel absent)."""

    def decorator(func):
        async def wrapper(*args: Any, **kwargs: Any):
            with tracer.start_as_current_span(f"agent_execution_{agent_type}") as span:
                span.set_attribute("agent.type", agent_type)
                span.set_attribute("tenant.id", tenant_id)
                span.set_attribute("lead.id", lead_id)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("execution.success", True)
                    return result
                except Exception as exc:
                    span.set_attribute("execution.success", False)
                    span.set_attribute("execution.error", str(exc))
                    raise

        return wrapper

    return decorator


def trace_step(step_name: str):
    def decorator(func):
        async def wrapper(*args: Any, **kwargs: Any):
            with tracer.start_as_current_span(f"agent_step_{step_name}") as span:
                span.set_attribute("step.name", step_name)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("step.success", True)
                    return result
                except Exception as exc:
                    span.set_attribute("step.success", False)
                    span.set_attribute("step.error", str(exc))
                    raise

        return wrapper

    return decorator


__all__ = [
    "tracer",
    "instrument_app",
    "trace_agent_execution",
    "trace_step",
]
