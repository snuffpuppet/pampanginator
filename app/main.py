"""
Kapampangan Tutor — Orchestration App

Starts the FastAPI application, loads tool definitions from config/tools.yaml,
and mounts the chat and health routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routes import chat, health
from services.tool_router import load_tools
from services import llm
from telemetry import init_telemetry
from metrics import metrics_endpoint
from middleware import MetricsMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_tools("/app/config/tools.yaml")
    llm.init()
    yield


app = FastAPI(title="Kapampangan Tutor", lifespan=lifespan)

# Must come before route registration so auto-instrumentation covers all routes
init_telemetry(app)

app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics_endpoint)

app.include_router(chat.router, prefix="/api")
app.include_router(health.router)

# Serve the React build as static files if present
frontend_path = Path("/app/frontend")
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
