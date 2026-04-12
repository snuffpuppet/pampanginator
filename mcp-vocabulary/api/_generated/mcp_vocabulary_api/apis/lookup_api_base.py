# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import Any, Optional
from typing_extensions import Annotated
from mcp_vocabulary_api.models.lookup_request import LookupRequest
from mcp_vocabulary_api.models.lookup_response import LookupResponse
from mcp_vocabulary_api.models.vocabulary_search_response import VocabularySearchResponse


class BaseLookupApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseLookupApi.subclasses = BaseLookupApi.subclasses + (cls,)
    async def lookup_get(
        self,
        q: Annotated[StrictStr, Field(description="Search query — Kapampangan word or English concept")],
        limit: Optional[Annotated[int, Field(le=20, strict=True, ge=1)]],
        max_authority_level: Annotated[Optional[Annotated[int, Field(le=4, strict=True, ge=1)]], Field(description="Only return entries at or below this authority level")],
    ) -> VocabularySearchResponse:
        """Embed q and return the closest vocabulary entries by cosine similarity. Includes similarity_score on each result so the frontend can distinguish exact-ish matches from near-misses. """
        ...


    async def lookup_post(
        self,
        lookup_request: LookupRequest,
    ) -> LookupResponse:
        """Semantic search via pgvector. Accepts {term, type, limit} JSON body. Same contract as the previous JSON-index implementation so tools.yaml does not need to change. """
        ...


    async def lookup_term_get(
        self,
        term: StrictStr,
        limit: Optional[Annotated[int, Field(le=20, strict=True, ge=1)]],
    ) -> LookupResponse:
        ...
