from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from services.index import lookup, entry_count

router = APIRouter()


class LookupRequest(BaseModel):
    term: str = Field(..., description="Kapampangan word or English concept to look up")
    type: Optional[str] = Field(None, description="word | phrase | verb | noun | adjective")
    limit: int = Field(6, ge=1, le=20, description="Maximum entries to return")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"term": "mangan"},
                {"term": "eat"},
                {"term": "sulat", "limit": 3},
            ]
        }
    }


@router.get(
    "/lookup/{term}",
    tags=["lookup"],
    summary="Look up a word (GET)",
    response_description="Matching vocabulary entries from the kaikki.org index",
)
async def lookup_term(
    term: str,
    type: Optional[str] = Query(None, description="word | phrase | verb | noun | adjective"),
    limit: int = Query(6, ge=1, le=20, description="Maximum entries to return"),
):
    """
    Look up a Kapampangan word or English concept by URL path parameter.

    Search order: exact word → inflected form → stem prefix → English gloss.
    Pass a Kapampangan word (`mangan`, `sulat`) or an English concept (`eat`, `write`).
    """
    results = lookup(term, limit=limit)
    if not results:
        raise HTTPException(status_code=404, detail=f"No entries found for '{term}'")
    return {"term": term, "count": len(results), "entries": results}


@router.post(
    "/lookup",
    tags=["lookup"],
    summary="Look up a word (POST)",
    response_description="Matching vocabulary entries from the kaikki.org index",
)
async def lookup_post(body: LookupRequest):
    """
    POST variant used by the orchestration layer's tool router.
    Accepts `{term, type, limit}` JSON body. Identical search logic to the GET endpoint.
    """
    results = lookup(body.term, limit=body.limit)
    if not results:
        raise HTTPException(status_code=404, detail=f"No entries found for '{body.term}'")
    return {"term": body.term, "count": len(results), "entries": results}


@router.get("/status", tags=["status"], summary="Index stats and liveness")
async def status():
    return {"entries": entry_count(), "status": "ok"}
