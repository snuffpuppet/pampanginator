"""
MCP Vocabulary Server

Loads the Kapampangan vocabulary index (kaikki.org / Wiktionary data) at startup
and exposes HTTP endpoints for vocabulary lookup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes.lookup import router as lookup_router
from services.index import load
from telemetry import init_telemetry
from metrics import metrics_endpoint
from middleware import MetricsMiddleware
from logging_setup import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load()
    yield


app = FastAPI(
    title="Kapampangan Vocabulary MCP",
    description=(
        "Vocabulary lookup service for the Kapampangan language tutor. "
        "Indexes the kaikki.org / Wiktionary Kapampangan extract (~1,600 entries) "
        "and serves it via exact-match, inflected-form, prefix, and English-gloss search.\n\n"
        "Called by the orchestration layer's agentic tool loop. "
        "Can also be queried directly here for manual testing."
    ),
    version="0.1.0",
    openapi_tags=[
        {"name": "lookup", "description": "Vocabulary search endpoints"},
        {"name": "status", "description": "Service health and index stats"},
    ],
    lifespan=lifespan,
)

init_telemetry(app)

app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics_endpoint)

app.include_router(lookup_router)
