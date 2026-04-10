"""
Admin endpoints for the grammar MCP server.

POST /admin/reseed  — truncates and reseeds grammar tables from canonical data files.
GET  /admin/stats   — returns local-addition counts for the app's sync status display.
GET  /admin/export  — exports locally added grammar nodes and edges as JSON.
"""

from fastapi import APIRouter, Query

from services import db

router = APIRouter(tags=["admin"])


@router.post("/admin/reseed")
async def trigger_reseed():
    """Force a full reseed of the grammar_nodes and grammar_edges tables from canonical files."""
    from services import seed
    count = await seed.seed_if_needed(force=True)
    return {"reseeded": count}


@router.get("/admin/stats")
async def get_stats():
    """Return local-addition counts for the orchestration app's sync status view."""
    pool = db.pool()

    local_row = await pool.fetchrow(
        "SELECT COUNT(*) FROM grammar_nodes WHERE seeded_from_canonical = FALSE"
    )

    return {
        "local_additions": local_row[0],
    }


@router.get("/admin/export")
async def export_local(
    min_authority_level: int = Query(1, ge=1, le=4),
    since: str | None = Query(None, description="ISO date — only entries added after this date"),
):
    """Export locally added grammar nodes and their edges (seeded_from_canonical = FALSE)."""
    pool = db.pool()

    conditions = ["seeded_from_canonical = FALSE", "authority_level <= $1"]
    params: list = [min_authority_level]
    if since:
        params.append(since)
        conditions.append(f"added_date >= ${len(params)}::date")

    node_rows = await pool.fetch(
        f"""
        SELECT id, type, label, meaning, embedding_text,
               authority_level, source, verified_by, notes, contributor, added_date
        FROM grammar_nodes
        WHERE {' AND '.join(conditions)}
        ORDER BY added_date, id
        """,
        *params,
    )
    grammar_nodes = [
        {k: (str(v) if hasattr(v, "isoformat") else v) for k, v in dict(row).items() if v is not None}
        for row in node_rows
    ]

    node_ids = [n["id"] for n in grammar_nodes]
    grammar_edges: list[dict] = []
    if node_ids:
        edge_rows = await pool.fetch(
            "SELECT from_node, relationship, to_node FROM grammar_edges "
            "WHERE from_node = ANY($1) OR to_node = ANY($1) ORDER BY from_node",
            node_ids,
        )
        grammar_edges = [dict(r) for r in edge_rows]

    return {"grammar_nodes": grammar_nodes, "grammar_edges": grammar_edges}
