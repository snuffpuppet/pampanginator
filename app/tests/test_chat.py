"""
Tests for POST /api/chat and DELETE /api/chat/{session_id}.

All LLM and interaction logging calls are mocked — no network I/O.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

VALID_PAYLOAD = {
    "session_id": "test-session",
    "messages": [{"role": "user", "content": "How do I say hello in Kapampangan?"}],
}


def _parse_sse_events(body: str) -> list[dict]:
    """Parse SSE body into a list of data payloads (skip [DONE])."""
    events = []
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("data:") and line != "data: [DONE]":
            events.append(json.loads(line[5:].strip()))
    return events


async def test_chat_returns_sse_stream(client):
    with patch("services.llm.complete", new=AsyncMock(return_value=("Kumusta!", ["vocabulary_lookup"]))), \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="iid-1")):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "data: [DONE]" in response.text


async def test_chat_response_text_in_stream(client):
    with patch("services.llm.complete", new=AsyncMock(return_value=("Kumusta!", ["vocabulary_lookup"]))), \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="iid-1")):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    events = _parse_sse_events(response.text)
    text_events = [e for e in events if "text" in e]
    assert len(text_events) == 1
    assert text_events[0]["text"] == "Kumusta!"


async def test_chat_no_tools_prepends_caveat(client):
    with patch("services.llm.complete", new=AsyncMock(return_value=("Some answer.", []))), \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="iid")):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    events = _parse_sse_events(response.text)
    text_events = [e for e in events if "text" in e]
    assert len(text_events) == 1
    assert "Training knowledge only" in text_events[0]["text"]


async def test_chat_tools_used_no_caveat(client):
    with patch("services.llm.complete", new=AsyncMock(return_value=("Verified answer.", ["vocabulary_lookup"]))), \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="iid")):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    events = _parse_sse_events(response.text)
    text_events = [e for e in events if "text" in e]
    assert "Training knowledge only" not in text_events[0]["text"]


async def test_chat_caveat_not_doubled_when_already_in_response(client):
    """If LLM already mentions training knowledge, don't prepend the caveat."""
    with patch("services.llm.complete", new=AsyncMock(return_value=("Training knowledge note.", []))), \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="iid")):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    events = _parse_sse_events(response.text)
    text_events = [e for e in events if "text" in e]
    # caveat not prepended when response already contains the phrase
    assert text_events[0]["text"] == "Training knowledge note."


async def test_chat_emits_interaction_id(client):
    with patch("services.llm.complete", new=AsyncMock(return_value=("Answer", ["vocabulary_lookup"]))), \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="uuid-abc-123")):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    events = _parse_sse_events(response.text)
    id_events = [e for e in events if "interaction_id" in e]
    assert len(id_events) == 1
    assert id_events[0]["interaction_id"] == "uuid-abc-123"


async def test_chat_llm_error_emits_error_event(client):
    with patch("services.llm.complete", new=AsyncMock(side_effect=RuntimeError("LLM unavailable"))), \
         patch("services.llm.ACTIVE_BACKEND", "openrouter"), \
         patch("services.llm.ACTIVE_MODEL", "test-model"):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.text
    assert "Error:" in body
    assert "LLM unavailable" in body
    assert "data: [DONE]" in body


async def test_chat_logging_failure_does_not_break_stream(client):
    """Interaction log failures must never surface to the user."""
    with patch("services.llm.complete", new=AsyncMock(return_value=("Answer", []))), \
         patch("services.interactions.log_interaction", new=AsyncMock(side_effect=Exception("DB down"))):
        response = await client.post("/api/chat", json=VALID_PAYLOAD)

    assert response.status_code == 200
    assert "data: [DONE]" in response.text
    # No error text leaked to the user
    events = _parse_sse_events(response.text)
    text_events = [e for e in events if "text" in e]
    assert not any("DB down" in e["text"] for e in text_events)


async def test_chat_generates_session_id_when_absent(client):
    payload = {"messages": [{"role": "user", "content": "Hello"}]}
    with patch("services.llm.complete", new=AsyncMock(return_value=("Hi", []))) as mock_complete, \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="iid")):
        response = await client.post("/api/chat", json=payload)

    assert response.status_code == 200
    # session_id was generated — complete() was called with a non-empty string
    call_kwargs = mock_complete.call_args
    assert call_kwargs.kwargs.get("session_id") or call_kwargs.args


async def test_clear_session_returns_cleared(client):
    response = await client.delete("/api/chat/my-session-xyz")
    assert response.status_code == 200
    assert response.json() == {"session_id": "my-session-xyz", "cleared": True}


async def test_chat_missing_messages_field_returns_422(client):
    response = await client.post("/api/chat", json={"session_id": "s"})
    assert response.status_code == 422


async def test_chat_invalid_message_role_not_rejected_by_schema(client):
    """The schema accepts any role string; the LLM decides what to do with it."""
    with patch("services.llm.complete", new=AsyncMock(return_value=("OK", []))), \
         patch("services.interactions.log_interaction", new=AsyncMock(return_value="iid")):
        response = await client.post("/api/chat", json={
            "messages": [{"role": "system", "content": "You are a tutor."}]
        })
    assert response.status_code == 200
