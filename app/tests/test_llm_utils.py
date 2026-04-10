"""
Unit tests for _try_parse_text_tool_call in services/llm.py.

This function detects and parses tool calls that smaller LLMs emit as plain
text JSON instead of using the structured tool_calls API mechanism.
"""

import pytest
from unittest.mock import patch

# Simulate the two tools the app knows about
_TOOL_DEFS = [
    {"type": "function", "function": {"name": "vocabulary_lookup", "description": "", "parameters": {}}},
    {"type": "function", "function": {"name": "grammar_lookup", "description": "", "parameters": {}}},
]


@pytest.fixture(autouse=True)
def mock_known_tools():
    """Patch get_tool_definitions so the parser sees vocabulary_lookup and grammar_lookup."""
    with patch("services.llm.get_tool_definitions", return_value=_TOOL_DEFS):
        yield


from services.llm import _try_parse_text_tool_call


# --- Happy paths ---

def test_valid_json_vocabulary_lookup():
    result = _try_parse_text_tool_call(
        '{"name": "vocabulary_lookup", "parameters": {"term": "mangan"}}'
    )
    assert result is not None
    name, params = result
    assert name == "vocabulary_lookup"
    assert params == {"term": "mangan"}


def test_valid_json_grammar_lookup():
    result = _try_parse_text_tool_call(
        '{"name": "grammar_lookup", "parameters": {"root": "mangan"}}'
    )
    assert result is not None
    name, params = result
    assert name == "grammar_lookup"


def test_accepts_arguments_key_instead_of_parameters():
    result = _try_parse_text_tool_call(
        '{"name": "vocabulary_lookup", "arguments": {"term": "aldo"}}'
    )
    assert result is not None
    assert result[1] == {"term": "aldo"}


def test_empty_parameters_dict():
    result = _try_parse_text_tool_call(
        '{"name": "grammar_lookup", "parameters": {}}'
    )
    assert result is not None
    assert result[1] == {}


# --- Normalisation ---

def test_uppercase_tool_name_normalized():
    result = _try_parse_text_tool_call(
        '{"name": "VOCABULARY_LOOKUP", "parameters": {"term": "test"}}'
    )
    assert result is not None
    assert result[0] == "vocabulary_lookup"


def test_mixed_case_tool_name_normalized():
    result = _try_parse_text_tool_call(
        '{"name": "Vocabulary_Lookup", "parameters": {"term": "test"}}'
    )
    assert result is not None
    assert result[0] == "vocabulary_lookup"


def test_space_separated_tool_name_normalized():
    result = _try_parse_text_tool_call(
        '{"name": "vocabulary lookup", "parameters": {"term": "test"}}'
    )
    assert result is not None
    assert result[0] == "vocabulary_lookup"


# --- Fixup of broken JSON produced by smaller models ---

def test_unquoted_tool_name_value():
    """Some models output: {"name": vocabulary_lookup, ...} without quotes on the value."""
    result = _try_parse_text_tool_call(
        '{"name": vocabulary_lookup, "parameters": {"term": "mangan"}}'
    )
    assert result is not None
    assert result[0] == "vocabulary_lookup"


# --- Rejection cases ---

def test_plain_text_returns_none():
    assert _try_parse_text_tool_call("Mangan means to eat in Kapampangan.") is None


def test_empty_string_returns_none():
    assert _try_parse_text_tool_call("") is None


def test_whitespace_only_returns_none():
    assert _try_parse_text_tool_call("   ") is None


def test_unknown_tool_name_returns_none():
    result = _try_parse_text_tool_call(
        '{"name": "delete_database", "parameters": {}}'
    )
    assert result is None


def test_json_without_name_key_returns_none():
    assert _try_parse_text_tool_call('{"tool": "vocabulary_lookup", "parameters": {}}') is None


def test_non_dict_json_returns_none():
    assert _try_parse_text_tool_call('["vocabulary_lookup", {}]') is None


def test_totally_broken_json_returns_none():
    assert _try_parse_text_tool_call("{{{not valid json at all") is None


def test_non_dict_parameters_returns_none():
    result = _try_parse_text_tool_call(
        '{"name": "vocabulary_lookup", "parameters": "just a string"}'
    )
    assert result is None


def test_response_text_starting_with_brace_but_not_tool_call_returns_none():
    result = _try_parse_text_tool_call('{"status": "ok", "message": "Hello!"}')
    assert result is None
