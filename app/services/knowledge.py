"""
Knowledge sharing service — sync status queries and contribution management.

Supports the admin Contributions tab (Decision 19).
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from services import db

log = logging.getLogger(__name__)

KNOWLEDGE_SHARING_CONFIG_PATH = Path("/app/config/knowledge_sharing.yaml")


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
    - Last seeded date (min created_at where seeded_from_canonical=true)
    - Count of local additions (seeded_from_canonical=false)
    - Knowledge sharing mode
    """
    pool = db.pool()

    last_seed_row = await pool.fetchrow(
        "SELECT MIN(created_at) FROM vocabulary WHERE seeded_from_canonical = TRUE"
    )
    last_seeded = last_seed_row[0].isoformat() if last_seed_row[0] else None

    local_vocab_row = await pool.fetchrow(
        "SELECT COUNT(*) FROM vocabulary WHERE seeded_from_canonical = FALSE"
    )
    local_vocab_count = local_vocab_row[0]

    local_nodes_row = await pool.fetchrow(
        "SELECT COUNT(*) FROM grammar_nodes WHERE seeded_from_canonical = FALSE"
    )
    local_nodes_count = local_nodes_row[0]

    seeded_vocab_row = await pool.fetchrow(
        "SELECT COUNT(*) FROM vocabulary WHERE seeded_from_canonical = TRUE"
    )
    seeded_vocab_count = seeded_vocab_row[0]

    config = load_ks_config()

    return {
        "mode": config.get("mode", "git"),
        "contributor_name": config.get("contributor_name", "unknown"),
        "last_seeded": last_seeded,
        "seeded_count": {"vocabulary": seeded_vocab_count},
        "local_additions": {
            "vocabulary": local_vocab_count,
            "grammar_nodes": local_nodes_count,
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
    """Approve a pending contribution — write to vocabulary or grammar table."""
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
        # Insert into vocabulary — the MCP vocabulary server's add endpoint handles embedding
        # Here we insert directly since this is a one-off admin action
        import httpx
        import os
        vocab_url = os.environ.get("VOCABULARY_SERVICE_URL", "http://mcp-vocabulary:8001")
        async with httpx.AsyncClient() as client:
            payload["authority_level"] = authority_level
            resp = await client.post(f"{vocab_url}/vocabulary", json=payload, timeout=30)
            if not resp.is_success:
                raise RuntimeError(f"Vocabulary service rejected entry: {resp.text}")

    elif contribution_type == "grammar_node":
        # Grammar nodes require embedding — insert via grammar MCP server when available,
        # otherwise record for manual processing
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
    import httpx
    import os

    vocab_url = os.environ.get("VOCABULARY_SERVICE_URL", "http://mcp-vocabulary:8001")
    grammar_url = os.environ.get("GRAMMAR_SERVICE_URL", "http://mcp-grammar:8002")

    async with httpx.AsyncClient() as client:
        v_resp = await client.post(f"{vocab_url}/admin/reseed", timeout=300)
        v_resp.raise_for_status()
        g_resp = await client.post(f"{grammar_url}/admin/reseed", timeout=300)
        g_resp.raise_for_status()

    return {
        "vocabulary": v_resp.json().get("reseeded", 0),
        "grammar_nodes": g_resp.json().get("reseeded", 0),
    }


async def export_local_contributions(min_authority_level: int = 1,
                                     since: str | None = None) -> dict[str, Any]:
    """
    Query local (non-seeded) vocabulary and grammar entries for export.
    Returns dict with vocabulary, grammar_nodes, grammar_edges lists.
    """
    pool = db.pool()

    vocab_conditions = ["seeded_from_canonical = FALSE", "authority_level <= $1"]
    vocab_params: list = [min_authority_level]
    if since:
        vocab_params.append(since)
        vocab_conditions.append(f"created_at >= ${len(vocab_params)}::date")

    vocab_rows = await pool.fetch(
        f"""
        SELECT term, meaning, part_of_speech, aspect_forms, examples,
               usage_notes, authority_level, source, verified_by, notes, contributor, added_date
        FROM vocabulary
        WHERE {' AND '.join(vocab_conditions)}
        ORDER BY added_date, term
        """,
        *vocab_params,
    )

    vocabulary = []
    for row in vocab_rows:
        entry: dict = {"term": row["term"], "meaning": row["meaning"]}
        if row["part_of_speech"]: entry["part_of_speech"] = row["part_of_speech"]
        if row["aspect_forms"]: entry["aspect_forms"] = json.loads(row["aspect_forms"])
        if row["examples"]: entry["examples"] = json.loads(row["examples"])
        if row["usage_notes"]: entry["usage_notes"] = row["usage_notes"]
        entry["authority_level"] = row["authority_level"]
        if row["source"]: entry["source"] = row["source"]
        if row["verified_by"]: entry["verified_by"] = row["verified_by"]
        if row["notes"]: entry["notes"] = row["notes"]
        if row["contributor"]: entry["contributor"] = row["contributor"]
        if row["added_date"]: entry["added_date"] = str(row["added_date"])
        vocabulary.append(entry)

    node_conditions = ["seeded_from_canonical = FALSE", "authority_level <= $1"]
    node_params: list = [min_authority_level]
    if since:
        node_params.append(since)
        node_conditions.append(f"added_date >= ${len(node_params)}::date")

    node_rows = await pool.fetch(
        f"""
        SELECT id, type, label, meaning, embedding_text,
               authority_level, source, verified_by, notes, contributor, added_date
        FROM grammar_nodes
        WHERE {' AND '.join(node_conditions)}
        ORDER BY added_date, id
        """,
        *node_params,
    )
    grammar_nodes = [
        {k: (str(v) if hasattr(v, "isoformat") else v) for k, v in dict(row).items() if v is not None}
        for row in node_rows
    ]

    node_ids = [n["id"] for n in grammar_nodes]
    grammar_edges: list[dict] = []
    if node_ids:
        edge_rows = await pool.fetch(
            "SELECT from_node, relationship, to_node FROM grammar_edges "
            "WHERE from_node = ANY($1) OR to_node = ANY($1) ORDER BY from_node",
            node_ids,
        )
        grammar_edges = [dict(r) for r in edge_rows]

    return {"vocabulary": vocabulary, "grammar_nodes": grammar_nodes, "grammar_edges": grammar_edges}
