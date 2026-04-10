"""
MCP Vocabulary Server

Connects to PostgreSQL at startup, loads the sentence-transformer embedding
model, and exposes HTTP endpoints for semantic vocabulary lookup and entry
addition via pgvector cosine similarity search.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes.lookup import router as lookup_router
from routes.admin import router as admin_router
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
    ],
    lifespan=lifespan,
)

init_telemetry(app)

app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics_endpoint)

app.include_router(lookup_router)
app.include_router(admin_router)
