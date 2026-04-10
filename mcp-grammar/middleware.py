"""
Request metrics middleware for the grammar MCP service.

Tracks request count and duration for every endpoint automatically.
Attaches the current trace ID as an exemplar so Grafana can link metric
data points to their traces in Tempo.
"""

import os
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry import trace

from metrics import REQUESTS_TOTAL, REQUEST_DURATION

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "kapampangan-mcp-grammar")


class MetricsMiddleware(BaseHTTPMiddleware):
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

        REQUESTS_TOTAL.labels(
            service=SERVICE_NAME,
            endpoint=path,
            status_code=str(response.status_code),
        ).inc(exemplar=exemplar)
        REQUEST_DURATION.labels(
            service=SERVICE_NAME,
            endpoint=path,
        ).observe(duration, exemplar=exemplar)

        return response
