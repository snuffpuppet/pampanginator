# coding: utf-8

from fastapi.testclient import TestClient


from mcp_vocabulary_api.models.status_response import StatusResponse  # noqa: F401


def test_status_get(client: TestClient):
    """Test case for status_get

    Index stats and liveness
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/status",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

