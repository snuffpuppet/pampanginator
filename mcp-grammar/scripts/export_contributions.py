#!/usr/bin/env python3
"""
export_contributions.py — Export locally added grammar nodes and edges.

Exports grammar_nodes entries that were added locally (seeded_from_canonical=FALSE)
and meet the authority level threshold, plus any edges connecting them.

Usage:
    python scripts/export_contributions.py \\
        --since 2024-03-01 \\
        --min_authority_level 1 \\
        --contributor "Maria Santos" \\
        --output contrib/

Outputs:
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


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://kapampangan:kapampangan_dev@localhost:5434/kapampangan")


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
    parser = argparse.ArgumentParser(description="Export locally added grammar contributions")
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

    print("Connecting to database…")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("Exporting grammar nodes…")
        grammar_nodes = await export_grammar_nodes(conn, args.since, args.min_authority_level)

        node_ids = {n["id"] for n in grammar_nodes}
        print("Exporting grammar edges…")
        grammar_edges = await export_grammar_edges(conn, node_ids)
    finally:
        await conn.close()

    if args.contributor:
        for node in grammar_nodes:
            node["contributor"] = args.contributor

    nodes_file = output_dir / "contrib_grammar_nodes.json"
    edges_file = output_dir / "contrib_grammar_edges.json"
    manifest_file = output_dir / "manifest.json"

    nodes_file.write_text(json.dumps(grammar_nodes, indent=2, ensure_ascii=False), encoding="utf-8")
    edges_file.write_text(json.dumps(grammar_edges, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "contributor": args.contributor or "unknown",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "min_authority_level": args.min_authority_level,
        "since": args.since,
        "counts": {
            "grammar_nodes": len(grammar_nodes),
            "grammar_edges": len(grammar_edges),
        },
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print()
    print("Export complete:")
    print(f"  Grammar nodes:  {len(grammar_nodes)}")
    print(f"  Grammar edges:  {len(grammar_edges)}")
    print(f"  Output:         {output_dir.resolve()}")
    if not grammar_nodes:
        print()
        print("No locally added entries found matching the filter criteria.")
    else:
        print()
        print("Next steps (Mode 1 — git):")
        print(f"  git add {output_dir}/ && git commit -m 'Add contributions from {args.contributor or 'contributor'}'")
        print()
        print("Next steps (Mode 2 — maintainer sync):")
        print(f"  python scripts/package_contribution.py --input {output_dir}/ "
              f"--contributor '{args.contributor or 'contributor'}'")


if __name__ == "__main__":
    asyncio.run(main())
