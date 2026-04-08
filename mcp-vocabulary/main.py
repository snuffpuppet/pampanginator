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


@asynccontextmanager
async def lifespan(app: FastAPI):
    load()
    yield


app = FastAPI(title="Kapampangan Vocabulary MCP", lifespan=lifespan)

init_telemetry(app)

app.include_router(lookup_router)
