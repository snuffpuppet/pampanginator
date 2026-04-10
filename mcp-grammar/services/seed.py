"""
Startup seeding for the grammar_nodes and grammar_edges tables.

Reads data/grammar_nodes.json and data/grammar_edges.json (mounted at /app/data/)
and inserts every entry with seeded_from_canonical=True.

Called from main.py lifespan after the DB pool and embedding model are ready.
Nodes are seeded before edges because edges reference nodes via foreign key.
"""

import json
import logging
import os
from pathlib import Path

from services import embeddings, db

log = logging.getLogger(__name__)

NODES_FILE = Path("/app/data/grammar_nodes.json")
EDGES_FILE = Path("/app/data/grammar_edges.json")


async def seed_if_needed(force: bool = False) -> int:
    """Seed grammar graph from canonical data files if tables are empty or RESEED_ON_STARTUP=true.

    Pass force=True to truncate and reseed regardless of table state.
    Returns the number of nodes seeded.
    """
    reseed = force or os.environ.get("RESEED_ON_STARTUP", "false").lower() == "true"

    count_row = await db.pool().fetchrow("SELECT COUNT(*) FROM grammar_nodes")
    count = count_row[0]

    if count > 0 and not reseed:
        log.info("grammar seed skipped — database populated", extra={"node_count": count})
        return

    if not NODES_FILE.exists():
        log.info("grammar seed skipped — nodes file not found", extra={"path": str(NODES_FILE)})
        return 0

    nodes = json.loads(NODES_FILE.read_text(encoding="utf-8"))
    edges = json.loads(EDGES_FILE.read_text(encoding="utf-8")) if EDGES_FILE.exists() else []

    if not nodes and not edges:
        log.info("grammar seed skipped — data files are empty")
        return 0

    if reseed and count > 0:
        # Edges reference nodes — truncate edges first, then nodes
        await db.pool().execute("TRUNCATE grammar_edges")
        await db.pool().execute("TRUNCATE grammar_nodes")
        log.info("grammar tables truncated for reseed")

    # Stage 1 — seed nodes
    seeded_nodes = 0
    for node in nodes:
        node_id = node.get("id", "")
        if not node_id:
            continue

        embedding_text = node.get("embedding_text") or f"{node_id} — {node.get('meaning', '')}."
        vector = embeddings.embed(embedding_text)
        vector_str = "[" + ",".join(str(v) for v in vector) + "]"

        await db.pool().execute(
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
            vector_str,
            node.get("authority_level", 3),
            node.get("source"),
            node.get("verified_by"),
            node.get("notes"),
            node.get("contributor"),
            node.get("added_date") or node.get("verified_date"),
        )
        seeded_nodes += 1

    # Stage 2 — seed edges (after all nodes exist)
    seeded_edges = 0
    for edge in edges:
        from_node = edge.get("from_node", "")
        to_node = edge.get("to_node", "")
        relationship = edge.get("relationship", "")
        if not from_node or not to_node or not relationship:
            continue

        await db.pool().execute(
            """
            INSERT INTO grammar_edges (from_node, relationship, to_node)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING
            """,
            from_node, relationship, to_node,
        )
        seeded_edges += 1

    log.info("grammar seeded from canonical files",
             extra={"seeded_nodes": seeded_nodes, "seeded_edges": seeded_edges,
                    "total_nodes": len(nodes), "total_edges": len(edges)})
    return seeded_nodes
