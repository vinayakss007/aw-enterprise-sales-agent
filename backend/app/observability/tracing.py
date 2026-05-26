"""
Tracing module with graceful degradation.
If OpenTelemetry is not installed, provides no-op implementations.
"""
import logging
import os

logger = logging.getLogger(__name__)

_OTEL_AVAILABLE = False

try:
    if os.getenv("ENABLE_OTEL", "false").lower() == "true":
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        provider = TracerProvider()
        trace.set_tracer_provider(provider)

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(span_exporter)
        provider.add_span_processor(span_processor)

        tracer = trace.get_tracer(__name__)
        _OTEL_AVAILABLE = True
        logger.info("OpenTelemetry tracing initialized")
    else:
        raise ImportError("OTEL disabled by config")
except (ImportError, Exception) as e:
    logger.info(f"OpenTelemetry not available, using no-op tracing: {e}")

    class _NoOpSpan:
        def set_attribute(self, key, value):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class _NoOpTracer:
        def start_as_current_span(self, name, **kwargs):
            return _NoOpSpan()

    tracer = _NoOpTracer()


def instrument_app(app):
    """Instrument the FastAPI application for tracing (no-op if OTEL unavailable)"""
    if _OTEL_AVAILABLE:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except Exception as e:
            logger.warning(f"Failed to instrument app: {e}")
