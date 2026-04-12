"""
MCP Grammar Graph Server

Connects to PostgreSQL at startup, loads the sentence-transformer embedding
model, and exposes HTTP endpoints for two-stage grammar retrieval:
  Stage 1 — semantic search via pgvector cosine similarity
  Stage 2 — graph traversal from the matched entry nodes via grammar_edges
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes.traverse import router as traverse_router
from routes.admin import router as admin_router
from services import embeddings, db, seed
from telemetry import init_telemetry
from metrics import metrics_endpoint, REQUESTS_TOTAL, REQUEST_DURATION
from kapampangan_obs import MetricsMiddleware
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
    title="Kapampangan Grammar MCP",
    description=(
        "Grammar knowledge graph server for the Kapampangan language tutor. "
        "Uses two-stage retrieval: pgvector semantic search finds the closest "
        "grammar nodes, then graph traversal via grammar_edges returns the full "
        "relational context (aspect siblings, focus type, derived forms).\n\n"
        "Called by the orchestration layer's agentic tool loop. "
        "Can also be queried directly here for manual testing."
    ),
    version="0.2.0",
    openapi_tags=[
        {"name": "traverse", "description": "Grammar graph traversal endpoints"},
        {"name": "status", "description": "Service health and graph stats"},
    ],
    lifespan=lifespan,
)

init_telemetry(app)

app.add_middleware(
    MetricsMiddleware,
    requests_total=REQUESTS_TOTAL,
    request_duration=REQUEST_DURATION,
)
app.add_route("/metrics", metrics_endpoint)

app.include_router(traverse_router)
app.include_router(admin_router)
