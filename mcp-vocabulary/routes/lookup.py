from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from services.index import lookup, entry_count

router = APIRouter()


@router.get("/lookup/{term}")
async def lookup_term(
    term: str,
    type: Optional[str] = Query(None, description="word | phrase | verb | noun | adjective"),
    limit: int = Query(6, ge=1, le=20),
):
    """
    Look up a Kapampangan word or English concept.

    Searches by exact word, inflected form, stem prefix, and English gloss.
    Returns up to `limit` matching entries from the kaikki.org vocabulary index.
    """
    results = lookup(term, limit=limit)
    if not results:
        raise HTTPException(status_code=404, detail=f"No entries found for '{term}'")
    return {"term": term, "count": len(results), "entries": results}


@router.post("/lookup")
async def lookup_post(body: dict):
    """POST variant — accepts {term, type, limit} body (used by tool_router)."""
    term = body.get("term", "")
    limit = int(body.get("limit", 6))
    if not term:
        raise HTTPException(status_code=400, detail="'term' is required")
    results = lookup(term, limit=limit)
    if not results:
        raise HTTPException(status_code=404, detail=f"No entries found for '{term}'")
    return {"term": term, "count": len(results), "entries": results}


@router.get("/status")
async def status():
    return {"entries": entry_count(), "status": "ok"}
