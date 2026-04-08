from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.graph import traverse, node_count, edge_count

router = APIRouter()


class TraverseRequest(BaseModel):
    root: str
    relationship: Optional[str] = None


@router.post("/traverse")
async def traverse_graph(request: TraverseRequest):
    """
    Traverse the grammar knowledge graph.

    Given a verb root or concept node id and an optional relationship filter,
    returns all connected nodes and their relationship labels.

    relationship values: aspect_of | focus_type | related_form | derived_noun | all
    """
    result = traverse(request.root, request.relationship)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/traverse/{root}")
async def traverse_get(
    root: str,
    relationship: Optional[str] = Query(None),
):
    """GET variant for quick inspection."""
    result = traverse(root, relationship)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/status")
async def status():
    return {"nodes": node_count(), "edges": edge_count(), "status": "ok"}
