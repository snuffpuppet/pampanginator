# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from mcp_vocabulary_api.apis.vocabulary_api_base import BaseVocabularyApi
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
from typing import Any
from mcp_vocabulary_api.models.add_vocabulary_request import AddVocabularyRequest
from mcp_vocabulary_api.models.vocabulary_entry import VocabularyEntry


router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/vocabulary",
    responses={
        201: {"model": VocabularyEntry, "description": "Entry created"},
        500: {"description": "Internal error inserting entry"},
    },
    tags=["vocabulary"],
    summary="Add a vocabulary entry",
    response_model_by_alias=True,
)
async def vocabulary_post(
    add_vocabulary_request: AddVocabularyRequest = Body(None, description=""),
) -> VocabularyEntry:
    """Insert a new vocabulary entry. Generates the embedding immediately so the entry is searchable without a restart. If source is native_speaker and authority_level is not explicitly set, authority_level defaults to 1. """
    if not BaseVocabularyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseVocabularyApi.subclasses[0]().vocabulary_post(add_vocabulary_request)
