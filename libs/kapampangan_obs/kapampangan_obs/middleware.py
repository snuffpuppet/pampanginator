"""
Request metrics middleware — shared across all Kapampangan tutor services.

Tracks request count and duration for every endpoint automatically.
Attaches the current trace ID as an exemplar so Grafana can link metric
data points to their traces in Tempo.

Usage:
    from kapampangan_obs import MetricsMiddleware
    from metrics import REQUESTS_TOTAL, REQUEST_DURATION

    app.add_middleware(
        MetricsMiddleware,
        requests_total=REQUESTS_TOTAL,
        request_duration=REQUEST_DURATION,
    )

The service name is read from the OTEL_SERVICE_NAME environment variable
at request time. The metric objects are injected by each service so that
the service retains ownership of its own Prometheus registry.
"""

import os
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry import trace


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_total, request_duration, **kwargs):
        super().__init__(app, **kwargs)
        self.requests_total = requests_total
        self.request_duration = request_duration

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        path = request.url.path
        if path in ("/metrics", "/health"):
            return response

        span = trace.get_current_span()
        ctx = span.get_span_context()
        exemplar = None
        if ctx.is_valid:
            exemplar = {"TraceID": trace.format_trace_id(ctx.trace_id)}

        service = os.getenv("OTEL_SERVICE_NAME", "unknown-service")
        self.requests_total.labels(
            service=service,
            endpoint=path,
            status_code=str(response.status_code),
        ).inc(exemplar=exemplar)
        self.request_duration.labels(
            service=service,
            endpoint=path,
        ).observe(duration, exemplar=exemplar)

        return response
