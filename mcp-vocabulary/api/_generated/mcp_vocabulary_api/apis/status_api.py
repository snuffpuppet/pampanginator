# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from mcp_vocabulary_api.apis.status_api_base import BaseStatusApi
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
from mcp_vocabulary_api.models.status_response import StatusResponse


router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/status",
    responses={
        200: {"model": StatusResponse, "description": "Service status and entry count"},
    },
    tags=["status"],
    summary="Index stats and liveness",
    response_model_by_alias=True,
)
async def status_get(
) -> StatusResponse:
    if not BaseStatusApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatusApi.subclasses[0]().status_get()
