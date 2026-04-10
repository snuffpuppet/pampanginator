"""
Admin endpoints for the vocabulary MCP server.

POST /admin/reseed  — truncates and reseeds vocabulary from canonical data files.
GET  /admin/stats   — returns seeded/local counts for the app's sync status display.
GET  /admin/export  — exports locally added vocabulary entries as JSON.
"""

import json

from fastapi import APIRouter, Query

from services import db

router = APIRouter(tags=["admin"])


@router.post("/admin/reseed")
async def trigger_reseed():
    """Force a full reseed of the vocabulary table from data/vocabulary.json."""
    from services import seed
    count = await seed.seed_if_needed(force=True)
    return {"reseeded": count}


@router.get("/admin/stats")
async def get_stats():
    """Return seeded and local-addition counts for the orchestration app's sync status view."""
    pool = db.pool()

    last_seed_row = await pool.fetchrow(
        "SELECT MIN(created_at) FROM vocabulary WHERE seeded_from_canonical = TRUE"
    )
    seeded_row = await pool.fetchrow(
        "SELECT COUNT(*) FROM vocabulary WHERE seeded_from_canonical = TRUE"
    )
    local_row = await pool.fetchrow(
        "SELECT COUNT(*) FROM vocabulary WHERE seeded_from_canonical = FALSE"
    )

    return {
        "last_seeded": last_seed_row[0].isoformat() if last_seed_row[0] else None,
        "seeded_count": seeded_row[0],
        "local_additions": local_row[0],
    }


@router.get("/admin/export")
async def export_local(
    min_authority_level: int = Query(1, ge=1, le=4),
    since: str | None = Query(None, description="ISO date — only entries added after this date"),
):
    """Export locally added vocabulary entries (seeded_from_canonical = FALSE)."""
    pool = db.pool()

    conditions = ["seeded_from_canonical = FALSE", "authority_level <= $1"]
    params: list = [min_authority_level]
    if since:
        params.append(since)
        conditions.append(f"created_at >= ${len(params)}::date")

    rows = await pool.fetch(
        f"""
        SELECT term, meaning, part_of_speech, aspect_forms, examples,
               usage_notes, authority_level, source, verified_by, notes, contributor, added_date
        FROM vocabulary
        WHERE {' AND '.join(conditions)}
        ORDER BY added_date, term
        """,
        *params,
    )

    vocabulary = []
    for row in rows:
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

    return {"vocabulary": vocabulary}
