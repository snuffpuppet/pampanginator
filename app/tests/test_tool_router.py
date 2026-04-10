"""
Unit tests for services/tool_router.py.

Tests load_tools(), get_tool_definitions(), and dispatch() in isolation.
All outbound httpx calls are mocked.
"""

import os
import tempfile

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


SAMPLE_TOOLS_YAML = """\
tools:
  - name: vocabulary_lookup
    description: Look up Kapampangan vocabulary terms
    endpoint: http://vocab:8001/lookup
    method: POST
    timeout_seconds: 10
    parameters:
      - name: term
        type: string
        description: The word to look up
        required: true
      - name: limit
        type: integer
        description: Maximum number of results
        required: false

  - name: grammar_lookup
    description: Look up Kapampangan grammar rules
    endpoint: http://grammar:8002/traverse
    method: POST
    timeout_seconds: 10
    parameters:
      - name: root
        type: string
        description: Verb root form
        required: true
"""


@pytest.fixture
def tools_yaml(tmp_path):
    f = tmp_path / "tools.yaml"
    f.write_text(SAMPLE_TOOLS_YAML)
    return str(f)


@pytest.fixture(autouse=True)
def reset_tool_state():
    """Restore _tools to its original state after each test."""
    from services import tool_router
    original = tool_router._tools[:]
    yield
    tool_router._tools = original


# --- load_tools ---

def test_load_tools_registers_both_tools(tools_yaml):
    from services.tool_router import load_tools, get_tool_definitions
    load_tools(tools_yaml)
    tools = get_tool_definitions()
    assert len(tools) == 2
    names = {t["name"] for t in tools}
    assert names == {"vocabulary_lookup", "grammar_lookup"}


def test_load_tools_sets_required_parameters(tools_yaml):
    from services.tool_router import load_tools, get_tool_definitions
    load_tools(tools_yaml)
    tools = get_tool_definitions()
    vocab = next(t for t in tools if t["name"] == "vocabulary_lookup")
    assert "term" in vocab["input_schema"]["required"]
    assert "limit" not in vocab["input_schema"]["required"]


def test_load_tools_sets_parameter_types(tools_yaml):
    from services.tool_router import load_tools, get_tool_definitions
    load_tools(tools_yaml)
    tools = get_tool_definitions()
    vocab = next(t for t in tools if t["name"] == "vocabulary_lookup")
    assert vocab["input_schema"]["properties"]["term"]["type"] == "string"
    assert vocab["input_schema"]["properties"]["limit"]["type"] == "integer"


# --- get_tool_definitions ---

def test_get_definitions_anthropic_format_has_input_schema(tools_yaml):
    from services.tool_router import load_tools, get_tool_definitions
    load_tools(tools_yaml)
    tools = get_tool_definitions(format="anthropic")
    for tool in tools:
        assert "input_schema" in tool
        assert "name" in tool
        assert "description" in tool


def test_get_definitions_anthropic_format_excludes_private_keys(tools_yaml):
    from services.tool_router import load_tools, get_tool_definitions
    load_tools(tools_yaml)
    tools = get_tool_definitions(format="anthropic")
    for tool in tools:
        assert not any(k.startswith("_") for k in tool)


def test_get_definitions_openai_format_structure(tools_yaml):
    from services.tool_router import load_tools, get_tool_definitions
    load_tools(tools_yaml)
    tools = get_tool_definitions(format="openai")
    for tool in tools:
        assert tool["type"] == "function"
        assert "function" in tool
        fn = tool["function"]
        assert "name" in fn
        assert "description" in fn
        assert "parameters" in fn


def test_get_definitions_openai_format_names_match(tools_yaml):
    from services.tool_router import load_tools, get_tool_definitions
    load_tools(tools_yaml)
    tools = get_tool_definitions(format="openai")
    names = {t["function"]["name"] for t in tools}
    assert names == {"vocabulary_lookup", "grammar_lookup"}


# --- dispatch ---

async def test_dispatch_unknown_tool_returns_error():
    from services.tool_router import dispatch
    result = await dispatch("nonexistent_tool", {})
    assert "error" in result
    assert "nonexistent_tool" in result["error"]


async def test_dispatch_successful_call(tools_yaml):
    from services.tool_router import load_tools, dispatch
    load_tools(tools_yaml)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"term": "mangan"}]}
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.request = AsyncMock(return_value=mock_resp)

    with patch("services.tool_router.httpx.AsyncClient", return_value=mock_client):
        result = await dispatch("vocabulary_lookup", {"term": "mangan"})

    assert "results" in result
    mock_client.request.assert_called_once_with(
        "POST", "http://vocab:8001/lookup", json={"term": "mangan"}
    )


async def test_dispatch_http_error_returns_error_dict(tools_yaml):
    from services.tool_router import load_tools, dispatch
    load_tools(tools_yaml)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.request = AsyncMock(
        side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=mock_resp)
    )

    with patch("services.tool_router.httpx.AsyncClient", return_value=mock_client):
        result = await dispatch("vocabulary_lookup", {"term": "mangan"})

    assert "error" in result
    assert "500" in result["error"]
    assert "detail" in result


async def test_dispatch_connection_error_returns_unreachable(tools_yaml):
    from services.tool_router import load_tools, dispatch
    load_tools(tools_yaml)

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.request = AsyncMock(side_effect=httpx.RequestError("connection refused"))

    with patch("services.tool_router.httpx.AsyncClient", return_value=mock_client):
        result = await dispatch("vocabulary_lookup", {"term": "mangan"})

    assert "error" in result
    assert "unreachable" in result["error"]


async def test_dispatch_endpoint_overridable_via_env(tools_yaml, monkeypatch):
    """VOCABULARY_LOOKUP_ENDPOINT env var should override the YAML endpoint."""
    from services.tool_router import load_tools, dispatch
    load_tools(tools_yaml)

    monkeypatch.setenv("VOCABULARY_LOOKUP_ENDPOINT", "http://localhost:9999/lookup")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.request = AsyncMock(return_value=mock_resp)

    with patch("services.tool_router.httpx.AsyncClient", return_value=mock_client):
        await dispatch("vocabulary_lookup", {"term": "test"})

    called_url = mock_client.request.call_args.args[1]
    assert called_url == "http://localhost:9999/lookup"
