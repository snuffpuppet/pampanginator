"""
Tests for /api/vocabulary endpoints (proxy to mcp-vocabulary).

All outbound httpx calls are mocked — no network I/O.
"""

import httpx
from unittest.mock import AsyncMock, MagicMock, patch


def _mock_http_client(method: str, status_code: int, json_body: dict):
    """Return a mock httpx.AsyncClient that responds to `method` with the given payload."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.text = str(json_body)
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    setattr(mock_client, method, AsyncMock(return_value=resp))
    return mock_client


async def test_search_vocabulary_proxies_to_mcp(client):
    results = {"results": [{"term": "mangan", "meaning": "to eat", "score": 0.95}]}
    mock_client = _mock_http_client("get", 200, results)

    with patch("routes.vocab.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/vocabulary/search?q=mangan")

    assert response.status_code == 200
    assert response.json() == results
    mock_client.get.assert_called_once()
    call_params = mock_client.get.call_args.kwargs.get("params", {})
    assert call_params.get("q") == "mangan"


async def test_search_vocabulary_passes_limit_and_authority(client):
    mock_client = _mock_http_client("get", 200, {"results": []})

    with patch("routes.vocab.httpx.AsyncClient", return_value=mock_client):
        await client.get("/api/vocabulary/search?q=test&limit=3&max_authority_level=2")

    call_params = mock_client.get.call_args.kwargs.get("params", {})
    assert call_params.get("limit") == 3
    assert call_params.get("max_authority_level") == 2


async def test_search_vocabulary_missing_query_returns_422(client):
    response = await client.get("/api/vocabulary/search")
    assert response.status_code == 422


async def test_search_vocabulary_service_unavailable_returns_503(client):
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

    with patch("routes.vocab.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/vocabulary/search?q=mangan")

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


async def test_search_vocabulary_upstream_error_propagates_status(client):
    mock_client = _mock_http_client("get", 422, {"detail": "bad param"})

    with patch("routes.vocab.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/vocabulary/search?q=mangan")

    assert response.status_code == 422


async def test_add_vocabulary_proxies_to_mcp(client):
    result = {"id": "vocab-99", "status": "created"}
    mock_client = _mock_http_client("post", 200, result)

    with patch("routes.vocab.httpx.AsyncClient", return_value=mock_client):
        response = await client.post("/api/vocabulary", json={
            "term": "mangan",
            "meaning": "to eat",
            "part_of_speech": "verb",
            "authority_level": 2,
        })

    assert response.status_code == 201
    assert response.json() == result


async def test_add_vocabulary_sends_full_body(client):
    mock_client = _mock_http_client("post", 200, {"id": "v1"})

    with patch("routes.vocab.httpx.AsyncClient", return_value=mock_client):
        await client.post("/api/vocabulary", json={
            "term": "keni",
            "meaning": "this",
            "usage_notes": "proximal demonstrative",
            "authority_level": 1,
        })

    posted_body = mock_client.post.call_args.kwargs.get("json", {})
    assert posted_body["term"] == "keni"
    assert posted_body["authority_level"] == 1


async def test_add_vocabulary_missing_required_fields_returns_422(client):
    response = await client.post("/api/vocabulary", json={"term": "mangan"})
    assert response.status_code == 422


async def test_add_vocabulary_service_unavailable_returns_503(client):
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("no route"))

    with patch("routes.vocab.httpx.AsyncClient", return_value=mock_client):
        response = await client.post("/api/vocabulary", json={
            "term": "mangan", "meaning": "to eat"
        })

    assert response.status_code == 503
