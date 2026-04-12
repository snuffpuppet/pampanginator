"""
Status API implementation.

Subclasses BaseStatusApi for GET /status.
"""

from mcp_vocabulary_api.apis.status_api_base import BaseStatusApi
from mcp_vocabulary_api.models.status_response import StatusResponse

from services.index import entry_count


class StatusApi(BaseStatusApi):

    async def status_get(self) -> StatusResponse:
        count = await entry_count()
        return StatusResponse(entries=count, status="ok")
