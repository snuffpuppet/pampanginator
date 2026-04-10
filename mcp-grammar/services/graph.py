"""
Grammar knowledge graph service — two-stage retrieval (Decision 13).

Stage 1 — Semantic search:
    Embed the query with all-MiniLM-L6-v2 and run cosine similarity search
    against grammar_nodes.embedding. Returns the top-N closest nodes.

Stage 2 — Graph traversal:
    From each matched entry node, query grammar_edges for all connected nodes.
    Returns the entry nodes, their relational neighbours, and the connecting edges.

Public API (used by routes/traverse.py):
    semantic_traverse(query, relationship, limit) → GraphFragment dict
    node_count()                                  → int (async)
    edge_count()                                  → int (async)
"""

import logging
import time
from typing import Optional

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from metrics import GRAMMAR_TRAVERSALS_TOTAL, GRAMMAR_TRAVERSAL_DURATION
from models.schemas import GrammarNode, GrammarEdge, GraphFragment
from services import embeddings, db

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def _row_to_node(row, similarity_score: Optional[float] = None) -> GrammarNode:
    return GrammarNode(
        id=row["id"],
        type=row["type"],
        label=row["label"],
        meaning=row["meaning"],
        authority_level=row["authority_level"],
        source=row["source"],
        notes=row["notes"],
        similarity_score=similarity_score,
    )


async def semantic_traverse(
    query: str,
    relationship: Optional[str] = None,
    limit: int = 3,
) -> dict:
    """
    Two-stage retrieval as per Decision 13.

    Returns a dict matching the GraphFragment shape:
        {entry_nodes, related_nodes, edges}
    """
    rel_label = relationship or "all"
    with tracer.start_as_current_span("grammar.traverse") as span:
        span.set_attribute("kapampangan.query", query)
        span.set_attribute("kapampangan.relationship", rel_label)
        span.set_attribute("kapampangan.limit", limit)
        try:
            t0 = time.time()
            result = await _two_stage(query, relationship, limit)
            duration = time.time() - t0

            total = len(result["entry_nodes"]) + len(result["related_nodes"])
            span.set_attribute("kapampangan.result_count", total)

            ctx = span.get_span_context()
            exemplar = {"TraceID": trace.format_trace_id(ctx.trace_id)} if ctx.is_valid else None
            GRAMMAR_TRAVERSAL_DURATION.labels(relationship=rel_label).observe(
                duration, exemplar=exemplar
            )
            GRAMMAR_TRAVERSALS_TOTAL.labels(relationship=rel_label).inc(exemplar=exemplar)

            log.info("grammar traverse", extra={
                "query": query, "relationship": rel_label,
                "entry_nodes": len(result["entry_nodes"]),
                "related_nodes": len(result["related_nodes"]),
                "edges": len(result["edges"]),
                "duration_s": round(duration, 4),
            })
            return result

        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            log.error("grammar traverse error", extra={"query": query, "error": str(e)})
            raise


async def _two_stage(
    query: str,
    relationship: Optional[str],
    limit: int,
) -> dict:
    """Internal two-stage implementation — no tracing/metrics."""
    p = db.pool()

    # ── Stage 1: semantic search ────────────────────────────────────────────
    vector = embeddings.embed(query)
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"

    entry_rows = await p.fetch(
        """
        SELECT id, type, label, meaning, authority_level, source, notes,
               1 - (embedding <=> $1::vector) AS similarity_score
        FROM grammar_nodes
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT $2
        """,
        vector_str, limit,
    )

    entry_nodes = [_row_to_node(r, float(r["similarity_score"])) for r in entry_rows]
    entry_ids = [n.id for n in entry_nodes]

    if not entry_ids:
        return GraphFragment(entry_nodes=[], related_nodes=[], edges=[]).model_dump()

    # ── Stage 2: graph traversal from each entry node ───────────────────────
    # Fetch all edges where either end is an entry node
    if relationship and relationship != "all":
        rel_filter = relationship.upper().replace(" ", "_")
        edge_rows = await p.fetch(
            """
            SELECT from_node, relationship, to_node
            FROM grammar_edges
            WHERE (from_node = ANY($1) OR to_node = ANY($1))
              AND UPPER(relationship) LIKE '%' || $2 || '%'
            """,
            entry_ids, rel_filter,
        )
    else:
        edge_rows = await p.fetch(
            """
            SELECT from_node, relationship, to_node
            FROM grammar_edges
            WHERE from_node = ANY($1) OR to_node = ANY($1)
            """,
            entry_ids,
        )

    edges = [
        GrammarEdge(
            from_node=r["from_node"],
            relationship=r["relationship"],
            to_node=r["to_node"],
        )
        for r in edge_rows
    ]

    # Collect IDs of related nodes (neighbours not already in entry_nodes)
    entry_id_set = set(entry_ids)
    related_ids = {
        r["from_node"] if r["to_node"] in entry_id_set else r["to_node"]
        for r in edge_rows
        if not (r["from_node"] in entry_id_set and r["to_node"] in entry_id_set)
    } - entry_id_set

    related_nodes: list[GrammarNode] = []
    if related_ids:
        related_rows = await p.fetch(
            """
            SELECT id, type, label, meaning, authority_level, source, notes
            FROM grammar_nodes
            WHERE id = ANY($1)
            """,
            list(related_ids),
        )
        related_nodes = [_row_to_node(r) for r in related_rows]

    return GraphFragment(
        entry_nodes=entry_nodes,
        related_nodes=related_nodes,
        edges=edges,
    ).model_dump()


async def node_count() -> int:
    row = await db.pool().fetchrow("SELECT COUNT(*) FROM grammar_nodes")
    return row[0]


async def edge_count() -> int:
    row = await db.pool().fetchrow("SELECT COUNT(*) FROM grammar_edges")
    return row[0]
