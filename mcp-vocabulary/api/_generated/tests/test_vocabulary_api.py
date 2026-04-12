# coding: utf-8

from fastapi.testclient import TestClient


from typing import Any  # noqa: F401
from mcp_vocabulary_api.models.add_vocabulary_request import AddVocabularyRequest  # noqa: F401
from mcp_vocabulary_api.models.vocabulary_entry import VocabularyEntry  # noqa: F401


def test_vocabulary_post(client: TestClient):
    """Test case for vocabulary_post

    Add a vocabulary entry
    """
    add_vocabulary_request = {"examples":[{"key":""},{"key":""}],"meaning":"meaning","part_of_speech":"part_of_speech","term":"term","aspect_forms":{"key":"aspect_forms"},"authority_level":1,"source":"source","usage_notes":"usage_notes"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/vocabulary",
    #    headers=headers,
    #    json=add_vocabulary_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

