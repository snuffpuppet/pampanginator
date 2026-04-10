"""
Database connection pool for the vocabulary MCP server.

Provides a module-level asyncpg pool created at app startup and
closed at shutdown. Call connect() in the FastAPI lifespan and
disconnect() on teardown. All other modules call pool() to get
the active pool.
"""

import asyncpg
import logging
import os

log = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    global _pool
    url = os.environ["DATABASE_URL"]
    _pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    log.info("vocabulary db pool connected")


async def disconnect() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        log.info("vocabulary db pool closed")


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised — connect() must be called at startup")
    return _pool
