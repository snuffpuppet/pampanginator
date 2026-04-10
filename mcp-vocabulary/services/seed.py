"""
Startup seeding for the vocabulary table.

Reads data/vocabulary.json (mounted at /app/data/vocabulary.json) and inserts
every entry into the vocabulary table with seeded_from_canonical=True.

Called from main.py lifespan after the DB pool and embedding model are ready.
"""

import json
import logging
import os
from pathlib import Path

from services import embeddings, db

log = logging.getLogger(__name__)

DATA_FILE = Path("/app/data/vocabulary.json")


def _build_embedding_text(term: str, meaning: str, usage_notes: str | None,
                          examples: list | None, aspect_forms: dict | None) -> str:
    parts = [f"{term} — {meaning}."]
    if usage_notes:
        parts.append(usage_notes + ".")
    if examples:
        ex_texts = [e.get("kapampangan", "") + " (" + e.get("english", "") + ")"
                    for e in examples if e.get("kapampangan")]
        if ex_texts:
            parts.append("Examples: " + " ".join(ex_texts) + ".")
    if aspect_forms:
        forms_text = ", ".join(f"{k}: {v}" for k, v in aspect_forms.items() if v)
        if forms_text:
            parts.append("Also expressed as: " + forms_text + ".")
    return " ".join(parts)


async def seed_if_needed(force: bool = False) -> int:
    """Seed vocabulary from canonical data file if table is empty or RESEED_ON_STARTUP=true.

    Pass force=True to truncate and reseed regardless of table state.
    Returns the number of entries seeded.
    """
    reseed = force or os.environ.get("RESEED_ON_STARTUP", "false").lower() == "true"

    count_row = await db.pool().fetchrow("SELECT COUNT(*) FROM vocabulary")
    count = count_row[0]

    if count > 0 and not reseed:
        log.info("vocabulary seed skipped — database populated", extra={"entry_count": count})
        return

    if not DATA_FILE.exists():
        log.info("vocabulary seed skipped — data file not found", extra={"path": str(DATA_FILE)})
        return 0

    entries = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not entries:
        log.info("vocabulary seed skipped — data file is empty")
        return 0

    if reseed and count > 0:
        await db.pool().execute("TRUNCATE vocabulary RESTART IDENTITY CASCADE")
        log.info("vocabulary table truncated for reseed")

    seeded = 0
    for entry in entries:
        term = entry.get("term", "")
        meaning = entry.get("meaning", "")
        if not term or not meaning:
            continue

        aspect_forms = entry.get("aspect_forms")
        examples = entry.get("examples")
        usage_notes = entry.get("usage_notes")
        part_of_speech = entry.get("part_of_speech")
        source = entry.get("source")
        authority_level = entry.get("authority_level", 3)
        verified_by = entry.get("verified_by")
        notes = entry.get("notes")
        contributor = entry.get("contributor")
        added_date = entry.get("added_date") or entry.get("verified_date")

        embedding_text = _build_embedding_text(term, meaning, usage_notes, examples, aspect_forms)
        vector = embeddings.embed(embedding_text)
        vector_str = "[" + ",".join(str(v) for v in vector) + "]"

        await db.pool().execute(
            """
            INSERT INTO vocabulary
                (term, meaning, part_of_speech, aspect_forms, examples,
                 usage_notes, embedding_text, embedding, authority_level, source,
                 verified_by, notes, seeded_from_canonical, contributor, added_date)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8::vector, $9, $10,
                    $11, $12, TRUE, $13, $14::date)
            ON CONFLICT DO NOTHING
            """,
            term, meaning, part_of_speech,
            json.dumps(aspect_forms) if aspect_forms else None,
            json.dumps(examples) if examples else None,
            usage_notes, embedding_text, vector_str, authority_level, source,
            verified_by, notes, contributor, added_date,
        )
        seeded += 1

    log.info("vocabulary seeded from canonical file",
             extra={"seeded": seeded, "total_in_file": len(entries)})
    return seeded
