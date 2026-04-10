"""
Vocabulary proxy routes.

The frontend calls these endpoints on the orchestration layer. The orchestration
layer forwards the requests to the mcp-vocabulary service. This keeps the
frontend unaware of the MCP server addresses (Decision 3.5 — service boundaries).
"""

import os
import httpx
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

log = logging.getLogger(__name__)

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])

VOCAB_URL = os.getenv("VOCABULARY_SERVICE_URL", "http://vocab:8001")


class AddVocabularyRequest(BaseModel):
    term: str
    meaning: str
    part_of_speech: Optional[str] = None
    aspect_forms: Optional[dict] = None
    examples: Optional[list[dict]] = None
    usage_notes: Optional[str] = None
    source: Optional[str] = None
    authority_level: int = Field(default=3, ge=1, le=4)


@router.get("/search", summary="Semantic vocabulary search")
async def search_vocabulary(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    max_authority_level: int = Query(4, ge=1, le=4),
):
    """Proxy to mcp-vocabulary GET /lookup?q=..."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{VOCAB_URL}/lookup",
                params={"q": q, "limit": limit, "max_authority_level": max_authority_level},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError as e:
        log.error("vocabulary service unreachable", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Vocabulary service unavailable")


@router.post("", status_code=201, summary="Add a vocabulary entry")
async def add_vocabulary(body: AddVocabularyRequest):
    """Proxy to mcp-vocabulary POST /vocabulary"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{VOCAB_URL}/vocabulary", json=body.model_dump())
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError as e:
        log.error("vocabulary service unreachable", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Vocabulary service unavailable")
