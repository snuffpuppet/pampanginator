"""
Lookup API implementation.

Subclasses BaseLookupApi so the generated router in
mcp_vocabulary_api/apis/lookup_api.py can dispatch to these methods.
Registered automatically via __init_subclass__ when this module is imported.
"""

from typing import Optional
from typing_extensions import Annotated
from pydantic import Field, StrictStr
from fastapi import HTTPException

from mcp_vocabulary_api.apis.lookup_api_base import BaseLookupApi
from mcp_vocabulary_api.models.lookup_request import LookupRequest
from mcp_vocabulary_api.models.lookup_response import LookupResponse
from mcp_vocabulary_api.models.vocabulary_search_response import VocabularySearchResponse
from mcp_vocabulary_api.models.vocabulary_search_result import VocabularySearchResult

from services.index import search, add_entry


class LookupApi(BaseLookupApi):

    async def lookup_post(
        self,
        lookup_request: LookupRequest,
    ) -> LookupResponse:
        results = await search(lookup_request.term, limit=lookup_request.limit)
        if not results:
            raise HTTPException(status_code=404, detail=f"No entries found for '{lookup_request.term}'")
        return LookupResponse(
            term=lookup_request.term,
            count=len(results),
            entries=[VocabularySearchResult(**r) for r in results],
        )

    async def lookup_get(
        self,
        q: Annotated[StrictStr, Field(description="Search query — Kapampangan word or English concept")],
        limit: Optional[Annotated[int, Field(le=20, strict=True, ge=1)]],
        max_authority_level: Annotated[Optional[Annotated[int, Field(le=4, strict=True, ge=1)]], Field(description="Only return entries at or below this authority level")],
    ) -> VocabularySearchResponse:
        resolved_limit = limit if limit is not None else 5
        resolved_max_auth = max_authority_level if max_authority_level is not None else 4
        results = await search(q, limit=resolved_limit, max_authority_level=resolved_max_auth)
        return VocabularySearchResponse(
            query=q,
            count=len(results),
            results=[VocabularySearchResult(**r) for r in results],
        )

    async def lookup_term_get(
        self,
        term: StrictStr,
        limit: Optional[Annotated[int, Field(le=20, strict=True, ge=1)]],
    ) -> LookupResponse:
        resolved_limit = limit if limit is not None else 6
        results = await search(term, limit=resolved_limit)
        if not results:
            raise HTTPException(status_code=404, detail=f"No entries found for '{term}'")
        return LookupResponse(
            term=term,
            count=len(results),
            entries=[VocabularySearchResult(**r) for r in results],
        )
