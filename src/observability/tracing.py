"""OpenTelemetry tracing configuration for distributed request tracing."""

from __future__ import annotations

import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing with Jaeger exporter."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel_service_name})
        tracer_provider = TracerProvider(resource=resource)

        jaeger_exporter = JaegerExporter(
            collector_endpoint=settings.otel_exporter_jaeger_endpoint,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        trace.set_tracer_provider(tracer_provider)

        logger.info("tracing_initialized", service=settings.otel_service_name)
    except ImportError:
        logger.warning("opentelemetry_not_available_tracing_disabled")
    except Exception as exc:
        logger.warning("tracing_setup_failed", error=str(exc))


def get_tracer(name: str = "agentic-orchestrator"):
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return None
