# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from typing import Any
from mcp_vocabulary_api.models.add_vocabulary_request import AddVocabularyRequest
from mcp_vocabulary_api.models.vocabulary_entry import VocabularyEntry


class BaseVocabularyApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseVocabularyApi.subclasses = BaseVocabularyApi.subclasses + (cls,)
    async def vocabulary_post(
        self,
        add_vocabulary_request: AddVocabularyRequest,
    ) -> VocabularyEntry:
        """Insert a new vocabulary entry. Generates the embedding immediately so the entry is searchable without a restart. If source is native_speaker and authority_level is not explicitly set, authority_level defaults to 1. """
        ...
