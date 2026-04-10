"""
Database connection pool for the grammar MCP server.

Same pattern as mcp-vocabulary/services/db.py. Call connect() at startup
and disconnect() at shutdown. All other modules call pool() to get the pool.
"""

import asyncpg
import logging
import os

log = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    global _pool
    url = os.environ["DATABASE_URL"]
    try:
        _pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    except asyncpg.exceptions.InvalidPasswordError as e:
        raise RuntimeError(
            f"Database authentication failed — check POSTGRES_PASSWORD in .env "
            f"matches the DATABASE_URL password: {e}"
        ) from e
    log.info("grammar db pool connected")


async def disconnect() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        log.info("grammar db pool closed")


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised — connect() must be called at startup")
    return _pool
