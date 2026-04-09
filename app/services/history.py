"""
Conversation history management.

Maintains per-session message history in memory. Each entry is a dict with
'role' and 'content' keys, matching the messages format shared by Anthropic
and OpenAI-compatible APIs.

Truncation: if a session exceeds MAX_TURNS, the oldest turns are dropped
(keeping the most recent MAX_TURNS pairs). The system prompt is always
prepended separately — it is never stored here.
"""

from collections import defaultdict

MAX_TURNS = 20   # each turn = one user + one assistant message

_sessions: dict[str, list[dict]] = defaultdict(list)


def get_history(session_id: str) -> list[dict]:
    return list(_sessions[session_id])


def append(session_id: str, role: str, content: str) -> None:
    _sessions[session_id].append({"role": role, "content": content})
    _truncate(session_id)


def clear(session_id: str) -> None:
    _sessions[session_id] = []


def _truncate(session_id: str) -> None:
    messages = _sessions[session_id]
    max_messages = MAX_TURNS * 2
    if len(messages) > max_messages:
        _sessions[session_id] = messages[-max_messages:]
