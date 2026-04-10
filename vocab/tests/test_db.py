"""
Tests for mcp-vocabulary/services/db.py startup behaviour.

Verifies that connect() surfaces a clear RuntimeError when PostgreSQL
authentication fails, so operators can immediately identify the cause
without decoding a raw asyncpg exception.
"""

import os
import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock, patch

import services.db as db


@pytest.fixture(autouse=True)
def reset_pool():
    """Ensure module-level _pool is None before and after each test."""
    db._pool = None
    yield
    db._pool = None


@pytest.mark.asyncio
async def test_connect_raises_runtime_error_on_invalid_password(monkeypatch):
    """connect() wraps InvalidPasswordError with a diagnostic RuntimeError."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://kapampangan:wrongpass@localhost/kapampangan")

    with patch(
        "services.db.asyncpg.create_pool",
        side_effect=asyncpg.exceptions.InvalidPasswordError("password authentication failed"),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            await db.connect()

    assert "POSTGRES_PASSWORD" in str(exc_info.value)
    assert "DATABASE_URL" in str(exc_info.value)


@pytest.mark.asyncio
async def test_connect_raises_key_error_when_env_var_missing():
    """connect() raises KeyError when DATABASE_URL is not set."""
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(KeyError):
            await db.connect()


@pytest.mark.asyncio
async def test_connect_succeeds_and_sets_pool(monkeypatch):
    """connect() sets the module-level pool on success."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://kapampangan:correct@localhost/kapampangan")

    mock_pool = MagicMock()
    with patch("services.db.asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        await db.connect()

    assert db._pool is mock_pool
