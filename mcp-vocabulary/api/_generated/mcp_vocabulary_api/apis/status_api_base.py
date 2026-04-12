# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from mcp_vocabulary_api.models.status_response import StatusResponse


class BaseStatusApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseStatusApi.subclasses = BaseStatusApi.subclasses + (cls,)
    async def status_get(
        self,
    ) -> StatusResponse:
        ...
