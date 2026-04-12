"""
Shared test fixtures.

Creates a minimal FastAPI app with all routes but no lifespan, telemetry, or
static file mount. Services (llm, db, feedback, etc.) are mocked per-test.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def app():
    """Minimal test app: all routes, no lifespan, no telemetry."""
    from routes import chat, health, feedback, vocab, export
    from kapampangan_obs import MetricsMiddleware
    from metrics import REQUESTS_TOTAL, REQUEST_DURATION

    test_app = FastAPI()
    test_app.add_middleware(
        MetricsMiddleware,
        requests_total=REQUESTS_TOTAL,
        request_duration=REQUEST_DURATION,
    )
    test_app.include_router(health.router)
    test_app.include_router(chat.router, prefix="/api")
    test_app.include_router(feedback.router, prefix="/api")
    test_app.include_router(vocab.router, prefix="/api")
    test_app.include_router(export.router, prefix="/api")
    return test_app


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
