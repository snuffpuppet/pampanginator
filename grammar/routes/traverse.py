from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from models.schemas import GraphFragment, TraverseRequest
from services.graph import semantic_traverse, node_count, edge_count

router = APIRouter()


@router.post(
    "/traverse",
    tags=["traverse"],
    summary="Two-stage grammar retrieval (POST) — used by orchestration tool router",
    response_model=GraphFragment,
)
async def traverse_graph(request: TraverseRequest):
    """
    Two-stage retrieval as per Decision 13:

    **Stage 1 — Semantic search:** embeds `root` (the query) and finds the
    closest grammar_nodes by cosine similarity against grammar_nodes.embedding.

    **Stage 2 — Graph traversal:** from each matched entry node, fetches all
    connected grammar_edges and their neighbour nodes.

    Returns `entry_nodes` (semantically matched), `related_nodes` (graph
    neighbours), and `edges` (all connecting edges).

    The `root` field accepts natural language ("how do I form the past tense")
    or exact concept IDs (`mangan`, `actor_focus`, `completed_aspect`).
    """
    try:
        result = await semantic_traverse(
            request.root,
            relationship=request.relationship,
            limit=request.limit,
        )
        if not result["entry_nodes"]:
            raise HTTPException(
                status_code=404,
                detail=f"No grammar nodes found matching '{request.root}'"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/traverse/{root}",
    tags=["traverse"],
    summary="Two-stage grammar retrieval (GET) — for direct browser / curl inspection",
    response_model=GraphFragment,
)
async def traverse_get(
    root: str,
    relationship: Optional[str] = Query(
        None,
        description="aspect_of | focus_type | related_form | derived_noun | all",
    ),
    limit: int = Query(3, ge=1, le=10),
):
    """GET variant for quick browser or curl inspection. Same two-stage logic."""
    try:
        result = await semantic_traverse(root, relationship=relationship, limit=limit)
        if not result["entry_nodes"]:
            raise HTTPException(
                status_code=404,
                detail=f"No grammar nodes found matching '{root}'"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", tags=["status"], summary="Graph stats and liveness")
async def status():
    nodes = await node_count()
    edges = await edge_count()
    return {"nodes": nodes, "edges": edges, "status": "ok"}
