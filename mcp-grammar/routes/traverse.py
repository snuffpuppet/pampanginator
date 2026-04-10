from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from services.graph import traverse, node_count, edge_count

router = APIRouter()


class TraverseRequest(BaseModel):
    root: str = Field(
        ...,
        description=(
            "A Kapampangan verb root (e.g. 'mangan') or a concept ID "
            "(e.g. 'actor_focus', 'progressive_aspect', 'absolutive_pronouns')"
        ),
    )
    relationship: Optional[str] = Field(
        None,
        description="aspect_of | focus_type | related_form | derived_noun | all",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"root": "mangan"},
                {"root": "mangan", "relationship": "aspect_of"},
                {"root": "sulat", "relationship": "all"},
                {"root": "actor_focus"},
                {"root": "progressive_aspect"},
                {"root": "absolutive_pronouns"},
                {"root": "case_system"},
            ]
        }
    }


@router.post(
    "/traverse",
    tags=["traverse"],
    summary="Traverse the grammar graph (POST)",
    response_description="Connected nodes and relationship labels for the given root",
)
async def traverse_graph(request: TraverseRequest):
    """
    Given a verb root or concept node ID and an optional relationship filter,
    returns all connected nodes from the Kapampangan grammar knowledge graph.

    **Verb root examples:** `mangan` (eat), `sulat` (write), `basa` (read)

    **Concept ID examples:** `actor_focus`, `object_focus`, `progressive_aspect`,
    `completed_aspect`, `contemplated_aspect`, `absolutive_pronouns`,
    `ergative_pronouns`, `case_system`, `vso_word_order`

    **Relationship filters:** `aspect_of` | `focus_type` | `related_form` | `derived_noun` | `all`
    """
    result = traverse(request.root, request.relationship)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get(
    "/traverse/{root}",
    tags=["traverse"],
    summary="Traverse the grammar graph (GET)",
    response_description="Connected nodes and relationship labels for the given root",
)
async def traverse_get(
    root: str,
    relationship: Optional[str] = Query(
        None,
        description="aspect_of | focus_type | related_form | derived_noun | all",
    ),
):
    """GET variant for quick browser or curl inspection."""
    result = traverse(root, relationship)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/status", tags=["status"], summary="Graph stats and liveness")
async def status():
    return {"nodes": node_count(), "edges": edge_count(), "status": "ok"}
