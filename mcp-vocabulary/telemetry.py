"""
OpenTelemetry initialisation for the vocabulary MCP service.

Call init_telemetry(app) immediately after app = FastAPI() and before any
route registration.
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "kapampangan-vocab")


def init_telemetry(app) -> None:
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": os.getenv("SERVICE_VERSION", "0.1.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,healthz,metrics,status",
    )
