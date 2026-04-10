#!/usr/bin/env python3
"""
import_knowledge.py — Import canonical grammar data into grammar-postgres.

Used after pulling updated canonical files from the repository or after a
maintainer publishes an updated canonical file.

Usage:
    # Incremental — only new entries added
    python scripts/import_knowledge.py --input data/ --mode incremental

    # Full reseed — truncate tables and reimport everything
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


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://kapampangan:kapampangan_dev@localhost:5434/kapampangan")

_model = None


def embed(text: str) -> list[float]:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print("  Loading embedding model (first run may take a moment)…")
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model.encode(text, normalize_embeddings=True).tolist()


def _vec_str(vector: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vector) + "]"


async def import_grammar_nodes(conn: asyncpg.Connection, nodes: list[dict],
                               mode: str, dry_run: bool) -> tuple[int, int]:
    """Returns (imported, skipped). Called before edges."""
    if mode == "full":
        if not dry_run:
            await conn.execute("TRUNCATE grammar_edges")
            await conn.execute("TRUNCATE grammar_nodes")
        print(f"  [full] grammar tables truncated")

    existing_ids: set[str] = set()
    if mode == "incremental":
        rows = await conn.fetch("SELECT id FROM grammar_nodes")
        existing_ids = {r[0] for r in rows}

    imported = skipped = 0
    total = len(nodes)

    for i, node in enumerate(nodes, 1):
        node_id = node.get("id", "").strip()
        if not node_id:
            skipped += 1
            continue

        if mode == "incremental" and node_id in existing_ids:
            skipped += 1
            continue

        print(f"  [{i}/{total}] {node_id}", end="\r", flush=True)

        if not dry_run:
            embedding_text = node.get("embedding_text") or f"{node_id} — {node.get('meaning', '')}."
            vector = embed(embedding_text)

            await conn.execute(
                """
                INSERT INTO grammar_nodes
                    (id, type, label, meaning, embedding_text, embedding,
                     authority_level, source, verified_by, notes,
                     seeded_from_canonical, contributor, added_date)
                VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8, $9, $10,
                        TRUE, $11, $12::date)
                ON CONFLICT (id) DO NOTHING
                """,
                node_id,
                node.get("type", "unknown"),
                node.get("label"),
                node.get("meaning"),
                embedding_text,
                _vec_str(vector),
                node.get("authority_level", 3),
                node.get("source"),
                node.get("verified_by"),
                node.get("notes"),
                node.get("contributor"),
                node.get("added_date") or node.get("verified_date"),
            )

        imported += 1
        existing_ids.add(node_id)

    print()
    return imported, skipped


async def import_grammar_edges(conn: asyncpg.Connection, edges: list[dict],
                               mode: str, dry_run: bool) -> tuple[int, int]:
    """Returns (imported, skipped). Called after nodes."""
    existing_edges: set[tuple] = set()
    if mode == "incremental":
        rows = await conn.fetch("SELECT from_node, relationship, to_node FROM grammar_edges")
        existing_edges = {(r[0], r[1], r[2]) for r in rows}

    imported = skipped = 0

    for edge in edges:
        from_node = edge.get("from_node", "")
        relationship = edge.get("relationship", "")
        to_node = edge.get("to_node", "")
        if not from_node or not relationship or not to_node:
            skipped += 1
            continue

        key = (from_node, relationship, to_node)
        if mode == "incremental" and key in existing_edges:
            skipped += 1
            continue

        if not dry_run:
            await conn.execute(
                """
                INSERT INTO grammar_edges (from_node, relationship, to_node)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
                """,
                from_node, relationship, to_node,
            )

        imported += 1
        existing_edges.add(key)

    return imported, skipped


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import canonical grammar data into grammar-postgres")
    parser.add_argument("--input", default="data/", metavar="DIR",
                        help="Directory containing grammar_nodes.json and grammar_edges.json (default: data/)")
    parser.add_argument("--mode", choices=["incremental", "full"], default="incremental",
                        help="incremental: only import new entries (default). "
                             "full: truncate and reimport all entries.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be imported without writing to the database")
    args = parser.parse_args()

    input_dir = Path(args.input)
    nodes_file = input_dir / "grammar_nodes.json"
    edges_file = input_dir / "grammar_edges.json"

    if not input_dir.exists():
        print(f"Error: input directory '{input_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.mode == "full" and not args.dry_run:
        answer = input(
            "\nWARNING: Full mode will truncate grammar_nodes and grammar_edges.\n"
            "All local additions not previously exported will be lost.\n"
            "Continue? [y/N] "
        ).strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    if args.dry_run:
        print("[DRY RUN] No changes will be written to the database.\n")

    grammar_nodes = json.loads(nodes_file.read_text(encoding="utf-8")) if nodes_file.exists() else []
    grammar_edges = json.loads(edges_file.read_text(encoding="utf-8")) if edges_file.exists() else []

    print(f"Input: {input_dir.resolve()}")
    print(f"  grammar_nodes.json: {len(grammar_nodes)} nodes")
    print(f"  grammar_edges.json: {len(grammar_edges)} edges")
    print()

    print("Connecting to database…")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("Importing grammar nodes…")
        n_imported, n_skipped = await import_grammar_nodes(conn, grammar_nodes, args.mode, args.dry_run)

        print("Importing grammar edges…")
        e_imported, e_skipped = await import_grammar_edges(conn, grammar_edges, args.mode, args.dry_run)
    finally:
        await conn.close()

    print()
    label = "[DRY RUN] Would have imported" if args.dry_run else "Imported"
    print(f"{label}:")
    print(f"  Grammar nodes: {n_imported} new, {n_skipped} skipped")
    print(f"  Grammar edges: {e_imported} new, {e_skipped} skipped")


if __name__ == "__main__":
    asyncio.run(main())
