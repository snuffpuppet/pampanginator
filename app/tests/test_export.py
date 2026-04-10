"""
Tests for POST /api/export/training-data.

DB pool is mocked — no real database required.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch


def _row(user_message, llm_response, rating, correction_kp=None, correction_en=None):
    """Minimal dict-like mock of an asyncpg Record."""
    return {
        "user_message": user_message,
        "llm_response": llm_response,
        "rating": rating,
        "correction_kapampangan": correction_kp,
        "correction_english": correction_en,
    }


def _mock_pool(rows):
    mock_pool = MagicMock()
    mock_pool.fetch = AsyncMock(return_value=rows)
    return mock_pool


def _parse_jsonl(text: str) -> list[dict]:
    return [json.loads(line) for line in text.strip().split("\n") if line.strip()]


async def test_export_sft_thumbs_up(client):
    rows = [_row("Q1", "A1", "thumbs_up")]
    with patch("services.db.pool", return_value=_mock_pool(rows)):
        response = await client.post("/api/export/training-data", json={"format": "sft"})

    assert response.status_code == 200
    records = _parse_jsonl(response.text)
    assert len(records) == 1
    assert records[0] == {"prompt": "Q1", "response": "A1"}


async def test_export_sft_thumbs_down_uses_kapampangan_correction(client):
    rows = [_row("Q2", "Wrong answer", "thumbs_down", correction_kp="Correct KP")]
    with patch("services.db.pool", return_value=_mock_pool(rows)):
        response = await client.post("/api/export/training-data", json={"format": "sft"})

    records = _parse_jsonl(response.text)
    assert records[0]["response"] == "Correct KP"


async def test_export_sft_thumbs_down_falls_back_to_english_correction(client):
    rows = [_row("Q3", "Wrong", "thumbs_down", correction_en="Correct EN")]
    with patch("services.db.pool", return_value=_mock_pool(rows)):
        response = await client.post("/api/export/training-data", json={"format": "sft"})

    records = _parse_jsonl(response.text)
    assert records[0]["response"] == "Correct EN"


async def test_export_sft_thumbs_down_no_correction_is_skipped(client):
    rows = [_row("Q4", "Bad answer", "thumbs_down")]
    with patch("services.db.pool", return_value=_mock_pool(rows)):
        response = await client.post("/api/export/training-data", json={"format": "sft"})

    assert response.text.strip() == ""


async def test_export_dpo_produces_chosen_rejected(client):
    rows = [_row("Q5", "Bad", "thumbs_down", correction_kp="Good KP")]
    with patch("services.db.pool", return_value=_mock_pool(rows)):
        response = await client.post("/api/export/training-data", json={"format": "dpo"})

    records = _parse_jsonl(response.text)
    assert len(records) == 1
    assert records[0] == {"prompt": "Q5", "chosen": "Good KP", "rejected": "Bad"}


async def test_export_dpo_thumbs_up_is_skipped(client):
    rows = [_row("Q6", "Good", "thumbs_up")]
    with patch("services.db.pool", return_value=_mock_pool(rows)):
        response = await client.post("/api/export/training-data", json={"format": "dpo"})

    assert response.text.strip() == ""


async def test_export_mixed_rows(client):
    rows = [
        _row("Q-up", "Good answer", "thumbs_up"),
        _row("Q-down", "Bad answer", "thumbs_down", correction_kp="Fixed"),
    ]
    with patch("services.db.pool", return_value=_mock_pool(rows)):
        response = await client.post("/api/export/training-data", json={"format": "sft"})

    records = _parse_jsonl(response.text)
    assert len(records) == 2
    assert records[0]["prompt"] == "Q-up"
    assert records[1]["response"] == "Fixed"


async def test_export_invalid_format_returns_422(client):
    response = await client.post("/api/export/training-data", json={"format": "csv"})
    assert response.status_code == 422


async def test_export_content_disposition_header(client):
    with patch("services.db.pool", return_value=_mock_pool([])):
        response = await client.post("/api/export/training-data", json={"format": "sft"})

    assert "content-disposition" in response.headers
    assert "training_sft" in response.headers["content-disposition"]
    assert ".jsonl" in response.headers["content-disposition"]


async def test_export_db_error_returns_500(client):
    mock_pool = MagicMock()
    mock_pool.fetch = AsyncMock(side_effect=Exception("connection lost"))
    with patch("services.db.pool", return_value=mock_pool):
        response = await client.post("/api/export/training-data", json={"format": "sft"})

    assert response.status_code == 500
