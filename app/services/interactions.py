"""
Interaction logging service (Decision 15).

After every LLM response, write a record to the interactions table with
the full context the model had access to. This makes every record self-
contained and interpretable for training data export and correction review.
"""

import json
import logging
from typing import Optional

from services import db

log = logging.getLogger(__name__)


async def log_interaction(
    *,
    session_id: str,
    user_message: str,
    llm_response: str,
    model: str,
    system_prompt_version: str,
    tools_used: list[str],
    scenario: Optional[str] = None,
    vocabulary_entries_retrieved: Optional[list[dict]] = None,
    grammar_nodes_retrieved: Optional[list[dict]] = None,
    authority_levels_used: Optional[list[int]] = None,
    kapampangan_produced: Optional[str] = None,
    english_gloss: Optional[str] = None,
) -> str:
    """
    Insert a record into the interactions table.
    Returns the new interaction id (UUID string).
    """
    row = await db.pool().fetchrow(
        """
        INSERT INTO interactions (
            session_id, scenario, user_message, system_prompt_version,
            model, tools_used, vocabulary_entries_retrieved,
            grammar_nodes_retrieved, authority_levels_used,
            llm_response, kapampangan_produced, english_gloss
        ) VALUES (
            $1, $2, $3, $4,
            $5, $6, $7::jsonb,
            $8::jsonb, $9,
            $10, $11, $12
        )
        RETURNING id
        """,
        session_id, scenario, user_message, system_prompt_version,
        model, tools_used or [],
        json.dumps(vocabulary_entries_retrieved) if vocabulary_entries_retrieved else None,
        json.dumps(grammar_nodes_retrieved) if grammar_nodes_retrieved else None,
        authority_levels_used or [],
        llm_response, kapampangan_produced, english_gloss,
    )

    interaction_id = str(row["id"])
    log.info("interaction logged", extra={
        "interaction_id": interaction_id,
        "session_id": session_id,
        "tools_used": tools_used,
        "model": model,
    })
    return interaction_id
