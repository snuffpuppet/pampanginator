"""
Shared test fixtures for mcp-grammar.

Creates a minimal FastAPI app with all routes but no lifespan, embeddings,
or DB connection. Services are mocked per-test.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from kapampangan_obs import MetricsMiddleware
from metrics import REQUESTS_TOTAL, REQUEST_DURATION


@pytest.fixture(scope="session")
def app():
    """Minimal test app: all routes, no lifespan, no embeddings."""
    from routes.traverse import router as traverse_router
    from routes.admin import router as admin_router

    test_app = FastAPI()
    test_app.add_middleware(
        MetricsMiddleware,
        requests_total=REQUESTS_TOTAL,
        request_duration=REQUEST_DURATION,
    )
    test_app.include_router(traverse_router)
    test_app.include_router(admin_router)
    return test_app


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
