"""
Knowledge sharing service — sync status queries and contribution management.

Supports the admin Contributions tab (Decision 19).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
import yaml

from services import db

log = logging.getLogger(__name__)

KNOWLEDGE_SHARING_CONFIG_PATH = Path("/app/config/knowledge_sharing.yaml")

VOCAB_URL = os.environ.get("VOCABULARY_SERVICE_URL", "http://mcp-vocabulary:8001")
GRAMMAR_URL = os.environ.get("GRAMMAR_SERVICE_URL", "http://grammar:8002")


def load_ks_config() -> dict:
    """Load config/knowledge_sharing.yaml. Returns defaults if file not found."""
    if KNOWLEDGE_SHARING_CONFIG_PATH.exists():
        try:
            return yaml.safe_load(KNOWLEDGE_SHARING_CONFIG_PATH.read_text()) or {}
        except Exception:
            pass
    return {"mode": "git", "contributor_name": "unknown", "reseed_on_startup": False}


async def get_sync_status() -> dict:
    """
    Return sync status for the admin Sync Status view:
    - Last seeded date (from vocab service)
    - Count of local additions (from vocab and grammar services)
    - Knowledge sharing mode
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        v_resp = await client.get(f"{VOCAB_URL}/admin/stats")
        v_resp.raise_for_status()
        vocab_stats = v_resp.json()

        g_resp = await client.get(f"{GRAMMAR_URL}/admin/stats")
        g_resp.raise_for_status()
        grammar_stats = g_resp.json()

    config = load_ks_config()

    return {
        "mode": config.get("mode", "git"),
        "contributor_name": config.get("contributor_name", "unknown"),
        "last_seeded": vocab_stats.get("last_seeded"),
        "seeded_count": {"vocabulary": vocab_stats.get("seeded_count", 0)},
        "local_additions": {
            "vocabulary": vocab_stats.get("local_additions", 0),
            "grammar_nodes": grammar_stats.get("local_additions", 0),
        },
        "canonical_url": config.get("canonical_url", ""),
    }


async def get_pending_contributions() -> list[dict]:
    """Return pending contributions from the pending_contributions table (Mode 3)."""
    rows = await db.pool().fetch(
        """
        SELECT id, submitted_at, contributor, contribution_type, payload,
               source_mode, authority_level, review_status, reviewed_by, reviewed_at, review_note
        FROM pending_contributions
        WHERE review_status = 'pending'
        ORDER BY submitted_at DESC
        """
    )
    result = []
    for row in rows:
        r = dict(row)
        r["id"] = str(r["id"])
        r["submitted_at"] = r["submitted_at"].isoformat()
        if r["reviewed_at"]:
            r["reviewed_at"] = r["reviewed_at"].isoformat()
        if isinstance(r["payload"], str):
            r["payload"] = json.loads(r["payload"])
        result.append(r)
    return result


async def approve_contribution(contrib_id: str, reviewed_by: str | None = None) -> dict:
    """Approve a pending contribution — forward to vocabulary or grammar service."""
    pool = db.pool()
    row = await pool.fetchrow(
        "SELECT * FROM pending_contributions WHERE id = $1::uuid", contrib_id
    )
    if not row:
        raise ValueError(f"Contribution {contrib_id} not found")

    payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
    contribution_type = row["contribution_type"]
    authority_level = row["authority_level"]

    if contribution_type == "vocabulary":
        payload["authority_level"] = authority_level
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{VOCAB_URL}/vocabulary", json=payload)
            if not resp.is_success:
                raise RuntimeError(f"Vocabulary service rejected entry: {resp.text}")

    elif contribution_type == "grammar_node":
        # Grammar nodes require embedding — auto-apply via grammar service when
        # POST /node is available. Currently recorded for manual processing.
        log.warning("grammar_node contribution approval not yet auto-applied",
                    extra={"id": contrib_id})

    await pool.execute(
        """
        UPDATE pending_contributions
        SET review_status = 'approved', reviewed_by = $2, reviewed_at = NOW()
        WHERE id = $1::uuid
        """,
        contrib_id, reviewed_by,
    )
    return {"id": contrib_id, "status": "approved"}


async def reject_contribution(contrib_id: str, reviewed_by: str | None = None,
                              note: str | None = None) -> dict:
    await db.pool().execute(
        """
        UPDATE pending_contributions
        SET review_status = 'rejected', reviewed_by = $2, reviewed_at = NOW(), review_note = $3
        WHERE id = $1::uuid
        """,
        contrib_id, reviewed_by, note,
    )
    return {"id": contrib_id, "status": "rejected"}


async def reseed_from_canonical() -> dict:
    """
    Trigger a full reseed on both MCP servers by calling their /admin/reseed endpoints.
    Equivalent to running import_knowledge.py --mode full on each server.
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        v_resp = await client.post(f"{VOCAB_URL}/admin/reseed")
        v_resp.raise_for_status()
        g_resp = await client.post(f"{GRAMMAR_URL}/admin/reseed")
        g_resp.raise_for_status()

    return {
        "vocabulary": v_resp.json().get("reseeded", 0),
        "grammar_nodes": g_resp.json().get("reseeded", 0),
    }


async def export_local_contributions(min_authority_level: int = 1,
                                     since: str | None = None) -> dict[str, Any]:
    """
    Fetch local (non-seeded) vocabulary and grammar entries from their respective services.
    Returns dict with vocabulary, grammar_nodes, grammar_edges lists.
    """
    params: dict[str, Any] = {"min_authority_level": min_authority_level}
    if since:
        params["since"] = since

    async with httpx.AsyncClient(timeout=30.0) as client:
        v_resp = await client.get(f"{VOCAB_URL}/admin/export", params=params)
        v_resp.raise_for_status()
        vocab_data = v_resp.json()

        g_resp = await client.get(f"{GRAMMAR_URL}/admin/export", params=params)
        g_resp.raise_for_status()
        grammar_data = g_resp.json()

    return {
        "vocabulary": vocab_data.get("vocabulary", []),
        "grammar_nodes": grammar_data.get("grammar_nodes", []),
        "grammar_edges": grammar_data.get("grammar_edges", []),
    }
