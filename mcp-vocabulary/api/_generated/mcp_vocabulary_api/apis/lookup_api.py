# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from mcp_vocabulary_api.apis.lookup_api_base import BaseLookupApi
import impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from mcp_vocabulary_api.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictStr
from typing import Any, Optional
from typing_extensions import Annotated
from mcp_vocabulary_api.models.lookup_request import LookupRequest
from mcp_vocabulary_api.models.lookup_response import LookupResponse
from mcp_vocabulary_api.models.vocabulary_search_response import VocabularySearchResponse


router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/lookup",
    responses={
        200: {"model": VocabularySearchResponse, "description": "Search results with similarity scores"},
    },
    tags=["lookup"],
    summary="Semantic vocabulary search (GET) — for the frontend",
    response_model_by_alias=True,
)
async def lookup_get(
    q: Annotated[StrictStr, Field(description="Search query — Kapampangan word or English concept")] = Query(None, description="Search query — Kapampangan word or English concept", alias="q"),
    limit: Optional[Annotated[int, Field(le=20, strict=True, ge=1)]] = Query(5, description="", alias="limit", ge=1, le=20),
    max_authority_level: Annotated[Optional[Annotated[int, Field(le=4, strict=True, ge=1)]], Field(description="Only return entries at or below this authority level")] = Query(4, description="Only return entries at or below this authority level", alias="max_authority_level", ge=1, le=4),
) -> VocabularySearchResponse:
    """Embed q and return the closest vocabulary entries by cosine similarity. Includes similarity_score on each result so the frontend can distinguish exact-ish matches from near-misses. """
    if not BaseLookupApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseLookupApi.subclasses[0]().lookup_get(q, limit, max_authority_level)


@router.post(
    "/lookup",
    responses={
        200: {"model": LookupResponse, "description": "Matching vocabulary entries"},
        404: {"description": "No entries found for the given term"},
    },
    tags=["lookup"],
    summary="Semantic vocabulary lookup (POST) — used by orchestration tool router",
    response_model_by_alias=True,
)
async def lookup_post(
    lookup_request: LookupRequest = Body(None, description=""),
) -> LookupResponse:
    """Semantic search via pgvector. Accepts {term, type, limit} JSON body. Same contract as the previous JSON-index implementation so tools.yaml does not need to change. """
    if not BaseLookupApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseLookupApi.subclasses[0]().lookup_post(lookup_request)


@router.get(
    "/lookup/{term}",
    responses={
        200: {"model": LookupResponse, "description": "Matching vocabulary entries"},
        404: {"description": "No entries found for the given term"},
    },
    tags=["lookup"],
    summary="Semantic vocabulary lookup by URL path (GET)",
    response_model_by_alias=True,
)
async def lookup_term_get(
    term: StrictStr = Path(..., description=""),
    limit: Optional[Annotated[int, Field(le=20, strict=True, ge=1)]] = Query(6, description="", alias="limit", ge=1, le=20),
) -> LookupResponse:
    if not BaseLookupApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseLookupApi.subclasses[0]().lookup_term_get(term, limit)
