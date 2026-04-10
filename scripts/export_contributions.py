#!/usr/bin/env python3
"""
export_contributions.py — Export locally approved knowledge additions.

Exports vocabulary entries and grammar nodes/edges that were added locally
(seeded_from_canonical=FALSE) and meet the authority level threshold. These
are contributions ready to be shared back to the canonical knowledge base.

Usage:
    python scripts/export_contributions.py \\
        --since 2024-03-01 \\
        --min_authority_level 1 \\
        --contributor "Maria Santos" \\
        --output contrib/

Outputs:
    {output}/contrib_vocabulary.json
    {output}/contrib_grammar_nodes.json
    {output}/contrib_grammar_edges.json
    {output}/manifest.json
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import asyncpg


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://kapampangan:kapampangan_dev@localhost:5432/kapampangan")


async def export_vocabulary(conn: asyncpg.Connection, since: str | None,
                            min_authority_level: int) -> list[dict]:
    conditions = ["seeded_from_canonical = FALSE", "authority_level <= $1"]
    params: list = [min_authority_level]

    if since:
        params.append(since)
        conditions.append(f"created_at >= ${len(params)}::date")

    where = " AND ".join(conditions)
    rows = await conn.fetch(
        f"""
        SELECT term, meaning, part_of_speech, aspect_forms, examples,
               usage_notes, authority_level, source, verified_by, verified_date,
               notes, contributor, added_date
        FROM vocabulary
        WHERE {where}
        ORDER BY added_date, term
        """,
        *params,
    )

    entries = []
    for row in rows:
        entry = {
            "term": row["term"],
            "meaning": row["meaning"],
        }
        if row["part_of_speech"]:
            entry["part_of_speech"] = row["part_of_speech"]
        if row["aspect_forms"]:
            entry["aspect_forms"] = json.loads(row["aspect_forms"])
        if row["examples"]:
            entry["examples"] = json.loads(row["examples"])
        if row["usage_notes"]:
            entry["usage_notes"] = row["usage_notes"]
        entry["authority_level"] = row["authority_level"]
        if row["source"]:
            entry["source"] = row["source"]
        if row["verified_by"]:
            entry["verified_by"] = row["verified_by"]
        if row["verified_date"]:
            entry["verified_date"] = str(row["verified_date"])
        if row["notes"]:
            entry["notes"] = row["notes"]
        if row["contributor"]:
            entry["contributor"] = row["contributor"]
        if row["added_date"]:
            entry["added_date"] = str(row["added_date"])
        entries.append(entry)

    return entries


async def export_grammar_nodes(conn: asyncpg.Connection, since: str | None,
                               min_authority_level: int) -> list[dict]:
    conditions = ["seeded_from_canonical = FALSE", "authority_level <= $1"]
    params: list = [min_authority_level]

    if since:
        params.append(since)
        conditions.append(f"added_date >= ${len(params)}::date")

    where = " AND ".join(conditions)
    rows = await conn.fetch(
        f"""
        SELECT id, type, label, meaning, embedding_text,
               authority_level, source, verified_by, verified_date,
               notes, contributor, added_date
        FROM grammar_nodes
        WHERE {where}
        ORDER BY added_date, id
        """,
        *params,
    )

    return [
        {
            k: (str(v) if hasattr(v, "isoformat") else v)
            for k, v in dict(row).items()
            if v is not None
        }
        for row in rows
    ]


async def export_grammar_edges(conn: asyncpg.Connection,
                               node_ids: set[str]) -> list[dict]:
    """Export edges where at least one endpoint is a locally added node."""
    if not node_ids:
        return []

    rows = await conn.fetch(
        """
        SELECT from_node, relationship, to_node
        FROM grammar_edges
        WHERE from_node = ANY($1) OR to_node = ANY($1)
        ORDER BY from_node, relationship, to_node
        """,
        list(node_ids),
    )

    return [dict(row) for row in rows]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Export locally approved knowledge contributions")
    parser.add_argument("--since", metavar="DATE",
                        help="Only export entries added after this date (ISO format: YYYY-MM-DD)")
    parser.add_argument("--min_authority_level", type=int, default=1,
                        metavar="LEVEL",
                        help="Minimum authority level to export (1=highest, 4=LLM inferred). "
                             "Default: 1 (native speaker verified only)")
    parser.add_argument("--contributor", metavar="NAME",
                        help="Tag all exported entries with this contributor name")
    parser.add_argument("--output", default="contrib/", metavar="DIR",
                        help="Output directory (default: contrib/)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to database…")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("Exporting vocabulary…")
        vocab_entries = await export_vocabulary(conn, args.since, args.min_authority_level)

        print("Exporting grammar nodes…")
        grammar_nodes = await export_grammar_nodes(conn, args.since, args.min_authority_level)

        node_ids = {n["id"] for n in grammar_nodes}
        print("Exporting grammar edges…")
        grammar_edges = await export_grammar_edges(conn, node_ids)

    finally:
        await conn.close()

    # Apply contributor override if specified
    if args.contributor:
        for entry in vocab_entries:
            entry["contributor"] = args.contributor
        for node in grammar_nodes:
            node["contributor"] = args.contributor

    # Write output files
    vocab_file = output_dir / "contrib_vocabulary.json"
    nodes_file = output_dir / "contrib_grammar_nodes.json"
    edges_file = output_dir / "contrib_grammar_edges.json"
    manifest_file = output_dir / "manifest.json"

    vocab_file.write_text(json.dumps(vocab_entries, indent=2, ensure_ascii=False), encoding="utf-8")
    nodes_file.write_text(json.dumps(grammar_nodes, indent=2, ensure_ascii=False), encoding="utf-8")
    edges_file.write_text(json.dumps(grammar_edges, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "contributor": args.contributor or "unknown",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "min_authority_level": args.min_authority_level,
        "since": args.since,
        "counts": {
            "vocabulary": len(vocab_entries),
            "grammar_nodes": len(grammar_nodes),
            "grammar_edges": len(grammar_edges),
        },
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Summary
    print()
    print("Export complete:")
    print(f"  Vocabulary entries:  {len(vocab_entries)}")
    print(f"  Grammar nodes:       {len(grammar_nodes)}")
    print(f"  Grammar edges:       {len(grammar_edges)}")
    print(f"  Output directory:    {output_dir.resolve()}")
    print()
    if len(vocab_entries) + len(grammar_nodes) == 0:
        print("No locally added entries found matching the filter criteria.")
        print("Add entries via the vocabulary page or admin interface first.")
    else:
        print("Next steps (Mode 1 — git):")
        print(f"  git add {output_dir}/ && git commit -m 'Add contributions from {args.contributor or 'contributor'}'")
        print()
        print("Next steps (Mode 2 — maintainer sync):")
        print(f"  python scripts/package_contribution.py --input {output_dir}/ "
              f"--contributor '{args.contributor or 'contributor'}'")


if __name__ == "__main__":
    asyncio.run(main())
