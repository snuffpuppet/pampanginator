"""
Admin endpoint for the grammar MCP server.

POST /admin/reseed — truncates and reseeds the grammar tables from canonical
data files. Called by the orchestration app's POST /api/admin/sync/reseed.
"""

from fastapi import APIRouter
from services import seed

router = APIRouter(tags=["admin"])


@router.post("/admin/reseed")
async def trigger_reseed():
    """Force a full reseed of the grammar_nodes and grammar_edges tables from canonical files."""
    count = await seed.seed_if_needed(force=True)
    return {"reseeded": count}
