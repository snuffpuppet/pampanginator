# coding: utf-8

from fastapi.testclient import TestClient


from datetime import date  # noqa: F401
from pydantic import Field  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from mcp_vocabulary_api.models.admin_export_response import AdminExportResponse  # noqa: F401
from mcp_vocabulary_api.models.admin_stats_response import AdminStatsResponse  # noqa: F401
from mcp_vocabulary_api.models.reseed_response import ReseedResponse  # noqa: F401


def test_admin_export_get(client: TestClient):
    """Test case for admin_export_get

    Export locally added vocabulary entries
    """
    params = [("min_authority_level", 1),     ("since", '2013-10-20')]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/admin/export",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_admin_reseed_post(client: TestClient):
    """Test case for admin_reseed_post

    Force a full reseed from canonical data
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/admin/reseed",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_admin_stats_get(client: TestClient):
    """Test case for admin_stats_get

    Seeded and local-addition counts
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/admin/stats",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

