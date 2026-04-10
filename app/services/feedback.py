"""
Feedback capture and review service (Decision 15, 18).

Handles writing feedback records, surfacing the review queue, and
applying approved corrections to the vocabulary table.
"""

import json
import logging
from typing import Optional

from services import db

log = logging.getLogger(__name__)


async def write_feedback(
    *,
    interaction_id: Optional[str],
    rating: str,
    correction_kapampangan: Optional[str] = None,
    correction_english: Optional[str] = None,
    correction_note: Optional[str] = None,
    corrected_by: Optional[str] = None,
    authority_level: int = 3,
) -> str:
    """Insert a feedback record. Returns the new feedback id."""
    row = await db.pool().fetchrow(
        """
        INSERT INTO feedback (
            interaction_id, rating,
            correction_kapampangan, correction_english, correction_note,
            corrected_by, authority_level
        ) VALUES ($1::uuid, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        interaction_id, rating,
        correction_kapampangan, correction_english, correction_note,
        corrected_by, authority_level,
    )
    feedback_id = str(row["id"])
    log.info("feedback written", extra={
        "feedback_id": feedback_id,
        "interaction_id": interaction_id,
        "rating": rating,
    })
    return feedback_id


async def get_pending() -> list[dict]:
    """Return all unreviewed feedback records ordered by timestamp descending."""
    rows = await db.pool().fetch(
        """
        SELECT
            f.id, f.interaction_id, f.timestamp, f.rating,
            f.correction_kapampangan, f.correction_english,
            f.correction_note, f.corrected_by, f.authority_level,
            f.reviewed, f.applied,
            i.user_message, i.llm_response, i.session_id, i.model
        FROM feedback f
        LEFT JOIN interactions i ON i.id = f.interaction_id
        WHERE f.reviewed = FALSE
        ORDER BY f.timestamp DESC
        """,
    )
    return [_feedback_row(r) for r in rows]


async def get_all(
    *,
    rating: Optional[str] = None,
    authority_level: Optional[int] = None,
    applied: Optional[bool] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
) -> list[dict]:
    """Return all feedback records with optional filters."""
    clauses = []
    params: list = []
    idx = 1

    if rating:
        clauses.append(f"f.rating = ${idx}")
        params.append(rating)
        idx += 1
    if authority_level is not None:
        clauses.append(f"f.authority_level = ${idx}")
        params.append(authority_level)
        idx += 1
    if applied is not None:
        clauses.append(f"f.applied = ${idx}")
        params.append(applied)
        idx += 1
    if after:
        clauses.append(f"f.timestamp >= ${idx}::timestamptz")
        params.append(after)
        idx += 1
    if before:
        clauses.append(f"f.timestamp <= ${idx}::timestamptz")
        params.append(before)
        idx += 1

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = await db.pool().fetch(
        f"""
        SELECT
            f.id, f.interaction_id, f.timestamp, f.rating,
            f.correction_kapampangan, f.correction_english,
            f.correction_note, f.corrected_by, f.authority_level,
            f.reviewed, f.applied,
            i.user_message, i.llm_response, i.session_id, i.model
        FROM feedback f
        LEFT JOIN interactions i ON i.id = f.interaction_id
        {where}
        ORDER BY f.timestamp DESC
        """,
        *params,
    )
    return [_feedback_row(r) for r in rows]


async def approve(
    feedback_id: str,
    *,
    authority_level: Optional[int] = None,
) -> dict:
    """
    Mark feedback as reviewed=true, applied=true.

    If correction_kapampangan is set, write the corrected term to the
    vocabulary table at the specified authority_level (defaulting to the
    authority_level stored on the feedback record).
    """
    row = await db.pool().fetchrow(
        "SELECT * FROM feedback WHERE id = $1::uuid",
        feedback_id,
    )
    if row is None:
        raise ValueError(f"Feedback {feedback_id} not found")

    effective_level = authority_level or row["authority_level"]

    # Write correction to vocabulary if one was provided
    if row["correction_kapampangan"]:
        await _apply_correction_to_vocabulary(
            feedback_id=feedback_id,
            correction_kapampangan=row["correction_kapampangan"],
            correction_english=row["correction_english"],
            correction_note=row["correction_note"],
            authority_level=effective_level,
        )

    await db.pool().execute(
        """
        UPDATE feedback
        SET reviewed = TRUE, applied = TRUE, authority_level = $2
        WHERE id = $1::uuid
        """,
        feedback_id, effective_level,
    )
    log.info("feedback approved", extra={"feedback_id": feedback_id, "authority_level": effective_level})
    return {"id": feedback_id, "reviewed": True, "applied": True}


async def reject(feedback_id: str) -> dict:
    """Mark feedback as reviewed=true, applied=false."""
    result = await db.pool().execute(
        "UPDATE feedback SET reviewed = TRUE, applied = FALSE WHERE id = $1::uuid",
        feedback_id,
    )
    if result == "UPDATE 0":
        raise ValueError(f"Feedback {feedback_id} not found")
    log.info("feedback rejected", extra={"feedback_id": feedback_id})
    return {"id": feedback_id, "reviewed": True, "applied": False}


async def _apply_correction_to_vocabulary(
    *,
    feedback_id: str,
    correction_kapampangan: str,
    correction_english: Optional[str],
    correction_note: Optional[str],
    authority_level: int,
) -> None:
    """
    Write the corrected term to the vocabulary table by calling the vocabulary
    MCP server's POST /vocabulary endpoint. This keeps the service boundary
    intact — the orchestration layer does not write to vocabulary directly.
    """
    import httpx
    import os

    vocab_url = os.getenv("VOCABULARY_SERVICE_URL", "http://mcp-vocabulary:8001")
    payload = {
        "term": correction_kapampangan,
        "meaning": correction_english or correction_kapampangan,
        "usage_notes": correction_note,
        "authority_level": authority_level,
        "source": "correction",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{vocab_url}/vocabulary", json=payload)
        resp.raise_for_status()

    log.info("correction applied to vocabulary via MCP server", extra={
        "term": correction_kapampangan,
        "authority_level": authority_level,
        "feedback_id": feedback_id,
    })


def _feedback_row(row) -> dict:
    return {
        "id": str(row["id"]),
        "interaction_id": str(row["interaction_id"]) if row["interaction_id"] else None,
        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
        "rating": row["rating"],
        "correction_kapampangan": row["correction_kapampangan"],
        "correction_english": row["correction_english"],
        "correction_note": row["correction_note"],
        "corrected_by": row["corrected_by"],
        "authority_level": row["authority_level"],
        "reviewed": row["reviewed"],
        "applied": row["applied"],
        "interaction": {
            "user_message": row["user_message"],
            "llm_response": row["llm_response"],
            "session_id": str(row["session_id"]) if row["session_id"] else None,
            "model": row["model"],
        } if row["user_message"] else None,
    }
