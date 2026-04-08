"""
Grammar knowledge graph service.

Loads grammar_graph.json at startup and exposes traversal queries.

Traversal patterns:
  aspect_of       — given a verb form, find its root and aspect label
  focus_type      — given a verb root, find which focus type it belongs to
  related_form    — given a verb root, return all its aspect forms
  derived_noun    — (future) derived nominal forms
  all             — return all edges for a given node id
"""

import json
from pathlib import Path
from typing import Optional

GRAPH_PATH = "/app/data/grammar_graph.json"

_nodes: dict[str, dict] = {}   # id → node dict
_out_edges: dict[str, list[dict]] = {}   # from_id → list of edges
_in_edges: dict[str, list[dict]] = {}    # to_id   → list of edges


def load() -> None:
    global _nodes, _out_edges, _in_edges

    path = Path(GRAPH_PATH)
    if not path.exists():
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    _nodes = {n["id"]: n for n in data.get("nodes", [])}
    _out_edges = {}
    _in_edges = {}

    for edge in data.get("edges", []):
        _out_edges.setdefault(edge["from"], []).append(edge)
        _in_edges.setdefault(edge["to"], []).append(edge)


def traverse(root: str, relationship: Optional[str] = None) -> dict:
    """
    Find graph results for a node id and optional relationship filter.

    Returns a dict with the root node, relationship, and matching results.
    """
    root_lower = root.lower()

    # Try exact node id first, then search by word field
    node = _nodes.get(root_lower)
    if node is None:
        node = next(
            (n for n in _nodes.values() if n.get("word", "").lower() == root_lower),
            None,
        )

    if node is None:
        return {"root": root, "relationship": relationship, "results": [], "error": f"Node '{root}' not found in grammar graph"}

    node_id = node["id"]
    out = _out_edges.get(node_id, [])
    inc = _in_edges.get(node_id, [])

    all_edges = out + inc

    if relationship and relationship != "all":
        rel_upper = relationship.upper().replace(" ", "_")
        all_edges = [e for e in all_edges if rel_upper in e["relationship"].upper()]

    results = []
    for edge in all_edges:
        other_id = edge["to"] if edge["from"] == node_id else edge["from"]
        other_node = _nodes.get(other_id, {"id": other_id})
        results.append({
            "node": other_id,
            "node_data": other_node,
            "relationship": edge["relationship"],
            "direction": "out" if edge["from"] == node_id else "in",
        })

    return {
        "root": root,
        "node_data": node,
        "relationship": relationship,
        "results": results,
    }


def node_count() -> int:
    return len(_nodes)


def edge_count() -> int:
    return sum(len(v) for v in _out_edges.values())
