"""
Vocabulary management API implementation.

Subclasses BaseVocabularyApi for POST /vocabulary.
"""

from fastapi import HTTPException

from mcp_vocabulary_api.apis.vocabulary_api_base import BaseVocabularyApi
from mcp_vocabulary_api.models.add_vocabulary_request import AddVocabularyRequest
from mcp_vocabulary_api.models.vocabulary_entry import VocabularyEntry

from services.index import add_entry


class VocabularyApi(BaseVocabularyApi):

    async def vocabulary_post(
        self,
        add_vocabulary_request: AddVocabularyRequest,
    ) -> VocabularyEntry:
        try:
            entry = await add_entry(add_vocabulary_request.model_dump())
            return VocabularyEntry(**entry)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
