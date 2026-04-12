"""
MCP Vocabulary Server

Connects to PostgreSQL at startup, loads the sentence-transformer embedding
model, and exposes HTTP endpoints for semantic vocabulary lookup and entry
addition via pgvector cosine similarity search.

API contract is defined in api/openapi.yaml (source of truth).
Server stubs are generated from it via `make generate` and live in
api/_generated/mcp_vocabulary_api/. Implementations are in api/_generated/impl/.
"""

import sys
import os

# Add api/_generated to the path so generated packages are importable.
# This must happen before importing any mcp_vocabulary_api or impl modules.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api", "_generated"))

from contextlib import asynccontextmanager
import yaml
from pathlib import Path
from fastapi import FastAPI

from mcp_vocabulary_api.apis.lookup_api import router as lookup_router
from mcp_vocabulary_api.apis.vocabulary_api import router as vocabulary_router
from mcp_vocabulary_api.apis.status_api import router as status_router
from mcp_vocabulary_api.apis.admin_api import router as admin_router

from services import embeddings, db, seed
from telemetry import init_telemetry
from metrics import metrics_endpoint
from middleware import MetricsMiddleware
from logging_setup import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    embeddings.load()
    await db.connect()
    await seed.seed_if_needed()
    yield
    await db.disconnect()


app = FastAPI(
    title="Kapampangan Vocabulary MCP",
    description=(
        "Vocabulary lookup service for the Kapampangan language tutor. "
        "Uses pgvector cosine similarity search against a PostgreSQL vocabulary "
        "table populated from canonical data files.\n\n"
        "Called by the orchestration layer's agentic tool loop. "
        "Can also be queried directly here for manual testing."
    ),
    version="0.2.0",
    openapi_tags=[
        {"name": "lookup", "description": "Vocabulary search endpoints"},
        {"name": "vocabulary", "description": "Vocabulary management endpoints"},
        {"name": "status", "description": "Service health and index stats"},
        {"name": "admin", "description": "Administrative operations"},
    ],
    lifespan=lifespan,
)


def _load_openapi() -> dict:
    """Serve the hand-authored contract instead of FastAPI's auto-generated spec."""
    return yaml.safe_load(Path("api/openapi.yaml").read_text())


app.openapi = _load_openapi

init_telemetry(app)

app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics_endpoint)

app.include_router(lookup_router)
app.include_router(vocabulary_router)
app.include_router(status_router)
app.include_router(admin_router)
