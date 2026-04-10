from pydantic import BaseModel, Field
from typing import Optional


class GrammarNode(BaseModel):
    id: str
    type: str
    label: Optional[str] = None
    meaning: Optional[str] = None
    authority_level: int = 3
    source: Optional[str] = None
    notes: Optional[str] = None
    similarity_score: Optional[float] = Field(
        None, description="Cosine similarity score from Stage 1 search (entry nodes only)"
    )


class GrammarEdge(BaseModel):
    from_node: str
    relationship: str
    to_node: str


class GraphFragment(BaseModel):
    """
    Two-stage retrieval result (Decision 13).

    entry_nodes   — nodes matched by semantic search (Stage 1)
    related_nodes — nodes connected to entry nodes via grammar_edges (Stage 2)
    edges         — all edges linking entry_nodes to related_nodes
    """
    entry_nodes: list[GrammarNode]
    related_nodes: list[GrammarNode]
    edges: list[GrammarEdge]


class TraverseRequest(BaseModel):
    root: str = Field(
        ...,
        description=(
            "Natural language query or Kapampangan verb root / concept ID. "
            "Embedded and matched semantically against grammar_nodes. "
            "Examples: 'mangan', 'completed aspect', 'how do I form the past tense', 'actor_focus'"
        ),
    )
    relationship: Optional[str] = Field(
        None,
        description="Filter Stage 2 edges by relationship type. "
                    "aspect_of | focus_type | related_form | derived_noun | all",
    )
    limit: int = Field(
        3, ge=1, le=10,
        description="Number of entry nodes to retrieve in Stage 1 semantic search",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"root": "mangan"},
                {"root": "mangan", "relationship": "aspect_of"},
                {"root": "completed aspect of verbs"},
                {"root": "actor_focus", "limit": 2},
            ]
        }
    }
