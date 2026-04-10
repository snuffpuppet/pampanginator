#!/usr/bin/env python3
"""
import_knowledge.py — Import canonical vocabulary data into vocab-postgres.

Used after pulling updated canonical files from the repository or after a
maintainer publishes an updated canonical file.

Usage:
    # Incremental — only new entries added
    python scripts/import_knowledge.py --input data/ --mode incremental

    # Full reseed — truncate table and reimport everything
    python scripts/import_knowledge.py --input data/ --mode full

    # Dry run — show what would be imported without writing
    python scripts/import_knowledge.py --input data/ --mode incremental --dry-run
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://kapampangan:kapampangan_dev@localhost:5433/kapampangan")

_model = None


def embed(text: str) -> list[float]:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print("  Loading embedding model (first run may take a moment)…")
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model.encode(text, normalize_embeddings=True).tolist()


def _build_vocab_embedding_text(entry: dict) -> str:
    term = entry.get("term", "")
    meaning = entry.get("meaning", "")
    usage_notes = entry.get("usage_notes")
    examples = entry.get("examples")
    aspect_forms = entry.get("aspect_forms")

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


def _vec_str(vector: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vector) + "]"


async def import_vocabulary(conn: asyncpg.Connection, entries: list[dict],
                            mode: str, dry_run: bool) -> tuple[int, int]:
    """Returns (imported, skipped)."""
    if mode == "full":
        if not dry_run:
            await conn.execute("TRUNCATE vocabulary RESTART IDENTITY CASCADE")
        print(f"  [full] vocabulary table truncated")

    existing_terms: set[str] = set()
    if mode == "incremental":
        rows = await conn.fetch("SELECT lower(term) FROM vocabulary")
        existing_terms = {r[0] for r in rows}

    imported = skipped = 0
    total = len(entries)

    for i, entry in enumerate(entries, 1):
        term = entry.get("term", "").strip()
        meaning = entry.get("meaning", "").strip()
        if not term or not meaning:
            skipped += 1
            continue

        if mode == "incremental" and term.lower() in existing_terms:
            skipped += 1
            continue

        print(f"  [{i}/{total}] {term}", end="\r", flush=True)

        if not dry_run:
            embedding_text = _build_vocab_embedding_text(entry)
            vector = embed(embedding_text)

            await conn.execute(
                """
                INSERT INTO vocabulary
                    (term, meaning, part_of_speech, aspect_forms, examples,
                     usage_notes, embedding_text, embedding, authority_level, source,
                     verified_by, notes, seeded_from_canonical, contributor, added_date)
                VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8::vector, $9, $10,
                        $11, $12, TRUE, $13, $14::date)
                ON CONFLICT DO NOTHING
                """,
                term, meaning,
                entry.get("part_of_speech"),
                json.dumps(entry["aspect_forms"]) if entry.get("aspect_forms") else None,
                json.dumps(entry["examples"]) if entry.get("examples") else None,
                entry.get("usage_notes"),
                embedding_text,
                _vec_str(vector),
                entry.get("authority_level", 3),
                entry.get("source"),
                entry.get("verified_by"),
                entry.get("notes"),
                entry.get("contributor"),
                entry.get("added_date") or entry.get("verified_date"),
            )

        imported += 1
        if mode == "incremental":
            existing_terms.add(term.lower())

    print()
    return imported, skipped


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import canonical vocabulary into vocab-postgres")
    parser.add_argument("--input", default="data/", metavar="DIR",
                        help="Directory containing vocabulary.json (default: data/)")
    parser.add_argument("--mode", choices=["incremental", "full"], default="incremental",
                        help="incremental: only import new entries (default). "
                             "full: truncate and reimport all entries.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be imported without writing to the database")
    args = parser.parse_args()

    input_dir = Path(args.input)
    vocab_file = input_dir / "vocabulary.json"

    if not input_dir.exists():
        print(f"Error: input directory '{input_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.mode == "full" and not args.dry_run:
        answer = input(
            "\nWARNING: Full mode will truncate the vocabulary table.\n"
            "All local additions not previously exported will be lost.\n"
            "Continue? [y/N] "
        ).strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    if args.dry_run:
        print("[DRY RUN] No changes will be written to the database.\n")

    vocab_entries = json.loads(vocab_file.read_text(encoding="utf-8")) if vocab_file.exists() else []

    print(f"Input: {input_dir.resolve()}")
    print(f"  vocabulary.json: {len(vocab_entries)} entries")
    print()

    print("Connecting to database…")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("Importing vocabulary…")
        v_imported, v_skipped = await import_vocabulary(conn, vocab_entries, args.mode, args.dry_run)
    finally:
        await conn.close()

    print()
    label = "[DRY RUN] Would have imported" if args.dry_run else "Imported"
    print(f"{label}:")
    print(f"  Vocabulary entries: {v_imported} new, {v_skipped} skipped")


if __name__ == "__main__":
    asyncio.run(main())
