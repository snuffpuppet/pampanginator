"""
Shared test fixtures for mcp-vocabulary.

Creates a minimal FastAPI app with all routes but no lifespan, embeddings,
or DB connection. Services are mocked per-test.
"""

import sys
import os

# Add api/_generated to path so generated packages are importable in tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "_generated"))

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from kapampangan_obs import MetricsMiddleware
from metrics import REQUESTS_TOTAL, REQUEST_DURATION


@pytest.fixture(scope="session")
def app():
    """Minimal test app: all routes, no lifespan, no embeddings."""
    from mcp_vocabulary_api.apis.lookup_api import router as lookup_router
    from mcp_vocabulary_api.apis.vocabulary_api import router as vocabulary_router
    from mcp_vocabulary_api.apis.status_api import router as status_router
    from mcp_vocabulary_api.apis.admin_api import router as admin_router

    test_app = FastAPI()
    test_app.add_middleware(
        MetricsMiddleware,
        requests_total=REQUESTS_TOTAL,
        request_duration=REQUEST_DURATION,
    )
    test_app.include_router(lookup_router)
    test_app.include_router(vocabulary_router)
    test_app.include_router(status_router)
    test_app.include_router(admin_router)
    return test_app


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
