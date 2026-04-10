"""
Vocabulary search service.

All searches run against the PostgreSQL vocabulary table using pgvector
cosine similarity. The embedding model is loaded at startup in embeddings.py
and used here to embed query strings before searching.

Public API (used by routes/lookup.py):
    search(query, limit, max_authority_level) → list[dict]
    add_entry(entry_data)                     → dict
    entry_count()                             → int
"""

import json
import logging
import time
from typing import Optional

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from metrics import VOCABULARY_LOOKUPS_TOTAL, VOCABULARY_LOOKUP_DURATION
from services import embeddings, db

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def _build_embedding_text(term: str, meaning: str, usage_notes: Optional[str],
                          examples: Optional[list], aspect_forms: Optional[dict]) -> str:
    """Construct the embedding text for a vocabulary entry per Decision 12 format."""
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


def _row_to_dict(row) -> dict:
    return {
        "id": str(row["id"]),
        "term": row["term"],
        "meaning": row["meaning"],
        "part_of_speech": row["part_of_speech"],
        "aspect_forms": json.loads(row["aspect_forms"]) if row["aspect_forms"] else None,
        "examples": json.loads(row["examples"]) if row["examples"] else None,
        "usage_notes": row["usage_notes"],
        "authority_level": row["authority_level"],
        "source": row["source"],
        "verified_by": row["verified_by"],
        "verified_date": str(row["verified_date"]) if row["verified_date"] else None,
        "notes": row["notes"],
    }


async def search(query: str, limit: int = 5,
                 max_authority_level: int = 4) -> list[dict]:
    """
    Embed `query` and run cosine similarity search against vocabulary.embedding.
    Returns up to `limit` entries ordered by similarity, filtered to
    authority_level <= max_authority_level.
    """
    with tracer.start_as_current_span("vocabulary.search") as span:
        span.set_attribute("kapampangan.query", query)
        span.set_attribute("kapampangan.limit", limit)
        try:
            t0 = time.time()
            vector = embeddings.embed(query)
            vector_str = "[" + ",".join(str(v) for v in vector) + "]"

            rows = await db.pool().fetch(
                """
                SELECT id, term, meaning, part_of_speech, aspect_forms, examples,
                       usage_notes, authority_level, source, verified_by, verified_date, notes,
                       1 - (embedding <=> $1::vector) AS similarity_score
                FROM vocabulary
                WHERE embedding IS NOT NULL
                  AND authority_level <= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                vector_str, max_authority_level, limit,
            )

            results = []
            for row in rows:
                entry = _row_to_dict(row)
                entry["similarity_score"] = float(row["similarity_score"])
                results.append(entry)

            duration = time.time() - t0
            span.set_attribute("kapampangan.result_count", len(results))

            ctx = span.get_span_context()
            exemplar = {"TraceID": trace.format_trace_id(ctx.trace_id)} if ctx.is_valid else None
            VOCABULARY_LOOKUP_DURATION.observe(duration, exemplar=exemplar)
            VOCABULARY_LOOKUPS_TOTAL.labels(
                result="found" if results else "not_found"
            ).inc(exemplar=exemplar)

            log.info("vocabulary search", extra={
                "query": query, "count": len(results), "duration_s": round(duration, 4)
            })
            return results

        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            log.error("vocabulary search error", extra={"query": query, "error": str(e)})
            raise


async def add_entry(data: dict) -> dict:
    """
    Insert a new vocabulary entry. Generates the embedding from the entry fields.
    Returns the full inserted row including the generated id.
    """
    term = data["term"]
    meaning = data["meaning"]
    aspect_forms = data.get("aspect_forms")
    examples = data.get("examples")
    usage_notes = data.get("usage_notes")
    part_of_speech = data.get("part_of_speech")
    source = data.get("source")
    authority_level = data.get("authority_level", 3)

    # authority_level 1 if source is native_speaker and not explicitly set lower
    if source == "native_speaker" and data.get("authority_level") is None:
        authority_level = 1

    embedding_text = _build_embedding_text(term, meaning, usage_notes, examples, aspect_forms)
    vector = embeddings.embed(embedding_text)
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"

    row = await db.pool().fetchrow(
        """
        INSERT INTO vocabulary
            (term, meaning, part_of_speech, aspect_forms, examples,
             usage_notes, embedding_text, embedding, authority_level, source)
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8::vector, $9, $10)
        RETURNING id, term, meaning, part_of_speech, aspect_forms, examples,
                  usage_notes, authority_level, source, verified_by, verified_date, notes
        """,
        term, meaning, part_of_speech,
        json.dumps(aspect_forms) if aspect_forms else None,
        json.dumps(examples) if examples else None,
        usage_notes, embedding_text, vector_str, authority_level, source,
    )

    log.info("vocabulary entry added", extra={"term": term, "authority_level": authority_level})
    return _row_to_dict(row)


# ---------------------------------------------------------------------------
# Legacy sync lookup — kept so routes that haven't migrated yet don't break.
# Wraps the async search with a synchronous shim only used by the old GET
# /lookup/{term} route. New code should call search() directly.
# ---------------------------------------------------------------------------

def lookup(term: str, limit: int = 6) -> list[dict]:
    """Synchronous shim — do not use in new code. Use search() instead."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(search(term, limit=limit))
    except RuntimeError:
        return asyncio.run(search(term, limit=limit))


async def entry_count() -> int:
    row = await db.pool().fetchrow("SELECT COUNT(*) FROM vocabulary")
    return row[0]
