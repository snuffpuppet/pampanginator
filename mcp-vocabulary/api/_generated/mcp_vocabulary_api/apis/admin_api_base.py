# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from datetime import date
from pydantic import Field
from typing import Optional
from typing_extensions import Annotated
from mcp_vocabulary_api.models.admin_export_response import AdminExportResponse
from mcp_vocabulary_api.models.admin_stats_response import AdminStatsResponse
from mcp_vocabulary_api.models.reseed_response import ReseedResponse


class BaseAdminApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAdminApi.subclasses = BaseAdminApi.subclasses + (cls,)
    async def admin_export_get(
        self,
        min_authority_level: Optional[Annotated[int, Field(le=4, strict=True, ge=1)]],
        since: Annotated[Optional[date], Field(description="ISO date — only entries added after this date")],
    ) -> AdminExportResponse:
        """Exports vocabulary entries that were added locally (seeded_from_canonical &#x3D; FALSE)."""
        ...


    async def admin_reseed_post(
        self,
    ) -> ReseedResponse:
        """Truncates and reseeds the vocabulary table from data/vocabulary.json."""
        ...


    async def admin_stats_get(
        self,
    ) -> AdminStatsResponse:
        """Returns seeded and local-addition counts for the orchestration app&#39;s sync status view."""
        ...
