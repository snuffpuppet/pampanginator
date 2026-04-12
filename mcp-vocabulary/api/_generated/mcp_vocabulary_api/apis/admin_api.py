# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from mcp_vocabulary_api.apis.admin_api_base import BaseAdminApi
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
from datetime import date
from pydantic import Field
from typing import Optional
from typing_extensions import Annotated
from mcp_vocabulary_api.models.admin_export_response import AdminExportResponse
from mcp_vocabulary_api.models.admin_stats_response import AdminStatsResponse
from mcp_vocabulary_api.models.reseed_response import ReseedResponse


router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/admin/export",
    responses={
        200: {"model": AdminExportResponse, "description": "Exported vocabulary entries"},
    },
    tags=["admin"],
    summary="Export locally added vocabulary entries",
    response_model_by_alias=True,
)
async def admin_export_get(
    min_authority_level: Optional[Annotated[int, Field(le=4, strict=True, ge=1)]] = Query(1, description="", alias="min_authority_level", ge=1, le=4),
    since: Annotated[Optional[date], Field(description="ISO date — only entries added after this date")] = Query(None, description="ISO date — only entries added after this date", alias="since"),
) -> AdminExportResponse:
    """Exports vocabulary entries that were added locally (seeded_from_canonical &#x3D; FALSE)."""
    if not BaseAdminApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAdminApi.subclasses[0]().admin_export_get(min_authority_level, since)


@router.post(
    "/admin/reseed",
    responses={
        200: {"model": ReseedResponse, "description": "Reseed complete"},
    },
    tags=["admin"],
    summary="Force a full reseed from canonical data",
    response_model_by_alias=True,
)
async def admin_reseed_post(
) -> ReseedResponse:
    """Truncates and reseeds the vocabulary table from data/vocabulary.json."""
    if not BaseAdminApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAdminApi.subclasses[0]().admin_reseed_post()


@router.get(
    "/admin/stats",
    responses={
        200: {"model": AdminStatsResponse, "description": "Stats"},
    },
    tags=["admin"],
    summary="Seeded and local-addition counts",
    response_model_by_alias=True,
)
async def admin_stats_get(
) -> AdminStatsResponse:
    """Returns seeded and local-addition counts for the orchestration app&#39;s sync status view."""
    if not BaseAdminApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAdminApi.subclasses[0]().admin_stats_get()
