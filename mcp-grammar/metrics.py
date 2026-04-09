"""
Prometheus metrics for the grammar MCP service.

All metric definitions live here. Import individual metrics into service
files — never redefine them elsewhere (duplicate registration raises at startup).
"""

from prometheus_client import Counter, Histogram, REGISTRY
from prometheus_client.openmetrics.exposition import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from fastapi import Request, Response

REQUESTS_TOTAL = Counter(
    "kapampangan_requests_total",
    "Total HTTP requests by service, endpoint, and status code",
    ["service", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "kapampangan_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

GRAMMAR_TRAVERSALS_TOTAL = Counter(
    "kapampangan_grammar_traversals_total",
    "Total grammar graph traversals",
    ["relationship"],
)

GRAMMAR_TRAVERSAL_DURATION = Histogram(
    "kapampangan_grammar_traversal_duration_seconds",
    "Time spent traversing the grammar graph",
    ["relationship"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
)


def metrics_endpoint(request: Request) -> Response:
    """Expose metrics in OpenMetrics format. Must use openmetrics.exposition."""
    return Response(
        generate_latest(REGISTRY),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )
