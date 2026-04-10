"""
MCP Grammar Graph Server

Loads the Kapampangan grammar knowledge graph at startup and exposes
HTTP endpoints for graph traversal queries.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes.traverse import router as traverse_router
from services.graph import load
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
    title="Kapampangan Grammar MCP",
    description=(
        "Grammar knowledge graph server for the Kapampangan language tutor. "
        "Loads a JSON graph of verb roots, aspect forms, focus types, pronouns, "
        "case markers, and other grammatical structures, and exposes it for traversal.\n\n"
        "Valid `root` values: a Kapampangan verb root (`mangan`, `sulat`, `basa`) "
        "or a concept ID (`actor_focus`, `progressive_aspect`, `case_system`, "
        "`absolutive_pronouns`, `ergative_pronouns`, `vso_word_order`, …).\n\n"
        "Called by the orchestration layer's agentic tool loop. "
        "Can also be queried directly here for manual testing."
    ),
    version="0.1.0",
    openapi_tags=[
        {"name": "traverse", "description": "Graph traversal endpoints"},
        {"name": "status", "description": "Service health and graph stats"},
    ],
    lifespan=lifespan,
)

init_telemetry(app)

app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics_endpoint)

app.include_router(traverse_router)
