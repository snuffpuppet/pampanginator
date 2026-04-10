"""
Structured JSON logging with OpenTelemetry trace correlation.

Call setup_logging() in main.py before FastAPI initialisation. Every log
record will carry trace_id and span_id from the active OTel span, enabling
direct links from Grafana log panels to Tempo traces.
"""

import logging
import os
from pythonjsonlogger import jsonlogger
from opentelemetry import trace


class _OtelTraceFilter(logging.Filter):
    """Inject service name, trace_id, and span_id into every log record."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service_name
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            record.trace_id = trace.format_trace_id(ctx.trace_id)
            record.span_id = trace.format_span_id(ctx.span_id)
        else:
            record.trace_id = ""
            record.span_id = ""
        return True


def setup_logging() -> None:
    service_name = os.getenv("OTEL_SERVICE_NAME", "kapampangan-mcp-grammar")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(_OtelTraceFilter(service_name))

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    # Reduce noise from third-party loggers that log at INFO by default
    for noisy in ("uvicorn.access", "httpx", "httpcore", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
