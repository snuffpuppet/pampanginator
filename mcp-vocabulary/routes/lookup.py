from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from models.schemas import AddVocabularyRequest, VocabularySearchResponse
from services.index import search, add_entry, entry_count

router = APIRouter()


# ---------------------------------------------------------------------------
# Tool-router-compatible POST /lookup  (used by orchestration layer)
# ---------------------------------------------------------------------------

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


@router.post(
    "/lookup",
    tags=["lookup"],
    summary="Semantic vocabulary lookup (POST) — used by orchestration tool router",
)
async def lookup_post(body: LookupRequest):
    """
    Semantic search via pgvector. Accepts `{term, type, limit}` JSON body.
    Same contract as the previous JSON-index implementation so tools.yaml
    does not need to change.
    """
    results = await search(body.term, limit=body.limit)
    if not results:
        raise HTTPException(status_code=404, detail=f"No entries found for '{body.term}'")
    return {"term": body.term, "count": len(results), "entries": results}


# ---------------------------------------------------------------------------
# GET /lookup  — semantic search for the frontend vocabulary page
# ---------------------------------------------------------------------------

@router.get(
    "/lookup",
    tags=["lookup"],
    summary="Semantic vocabulary search (GET) — for the frontend",
    response_model=VocabularySearchResponse,
)
async def lookup_get(
    q: str = Query(..., description="Search query — Kapampangan word or English concept"),
    limit: int = Query(5, ge=1, le=20),
    max_authority_level: int = Query(4, ge=1, le=4,
                                     description="Only return entries at or below this authority level"),
):
    """
    Embed `q` and return the closest vocabulary entries by cosine similarity.
    Includes similarity_score on each result so the frontend can distinguish
    exact-ish matches from near-misses.
    """
    results = await search(q, limit=limit, max_authority_level=max_authority_level)
    return VocabularySearchResponse(query=q, count=len(results), results=results)


# ---------------------------------------------------------------------------
# GET /lookup/{term}  — kept for direct browser / curl inspection
# ---------------------------------------------------------------------------

@router.get(
    "/lookup/{term}",
    tags=["lookup"],
    summary="Semantic vocabulary lookup by URL path (GET)",
)
async def lookup_term(
    term: str,
    limit: int = Query(6, ge=1, le=20),
):
    results = await search(term, limit=limit)
    if not results:
        raise HTTPException(status_code=404, detail=f"No entries found for '{term}'")
    return {"term": term, "count": len(results), "entries": results}


# ---------------------------------------------------------------------------
# POST /vocabulary  — add a new entry
# ---------------------------------------------------------------------------

@router.post(
    "/vocabulary",
    tags=["vocabulary"],
    summary="Add a vocabulary entry",
    status_code=201,
)
async def add_vocabulary(body: AddVocabularyRequest):
    """
    Insert a new vocabulary entry. Generates the embedding immediately so the
    entry is searchable without a restart. If source is native_speaker and
    authority_level is not explicitly set, authority_level defaults to 1.
    """
    try:
        entry = await add_entry(body.model_dump())
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /status
# ---------------------------------------------------------------------------

@router.get("/status", tags=["status"], summary="Index stats and liveness")
async def status():
    count = await entry_count()
    return {"entries": count, "status": "ok"}
