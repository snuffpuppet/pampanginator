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


@asynccontextmanager
async def lifespan(app: FastAPI):
    load()
    yield


app = FastAPI(title="Kapampangan Grammar MCP", lifespan=lifespan)

init_telemetry(app)

app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics_endpoint)

app.include_router(traverse_router)
