"""
Prometheus metrics for the orchestration service.

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

LLM_TOKENS_TOTAL = Counter(
    "kapampangan_llm_tokens_total",
    "Total LLM tokens consumed",
    ["direction", "model"],
)

LLM_CALL_DURATION = Histogram(
    "kapampangan_llm_call_duration_seconds",
    "Time spent waiting for Anthropic API response",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 30.0],
)

TOOL_CALLS_TOTAL = Counter(
    "kapampangan_tool_calls_total",
    "Total MCP tool invocations",
    ["tool_name"],
)

LLM_ERRORS_TOTAL = Counter(
    "kapampangan_llm_errors_total",
    "Total LLM backend errors (exceptions from Anthropic or Ollama)",
    ["backend", "model"],
)


def metrics_endpoint(request: Request) -> Response:
    """Expose metrics in OpenMetrics format. Must use openmetrics.exposition."""
    return Response(
        generate_latest(REGISTRY),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )
