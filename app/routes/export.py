"""
Training data export endpoint.

Runs the export query and streams the result as a JSONL download.
Mirrors the CLI script at scripts/export_training_data.py but as an HTTP
endpoint so the admin UI can trigger downloads without shell access.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services import db

log = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    format: str = Field("sft", description="sft | dpo")
    min_authority_level: int = Field(1, ge=1, le=4)
    after: Optional[str] = None
    before: Optional[str] = None


@router.post("/training-data", summary="Export training data as JSONL download")
async def export_training_data(body: ExportRequest):
    """
    Query interactions joined to approved feedback and stream the result as
    a JSONL file download. Same logic as scripts/export_training_data.py.
    """
    if body.format not in ("sft", "dpo"):
        raise HTTPException(status_code=422, detail="format must be sft or dpo")

    clauses = [
        "f.reviewed = TRUE",
        "f.applied = TRUE",
        f"f.authority_level <= {body.min_authority_level}",
    ]
    params: list = []
    idx = 1
    if body.after:
        clauses.append(f"f.timestamp >= ${idx}::timestamptz")
        params.append(body.after)
        idx += 1
    if body.before:
        clauses.append(f"f.timestamp <= ${idx}::timestamptz")
        params.append(body.before)
        idx += 1

    where = " AND ".join(clauses)

    try:
        rows = await db.pool().fetch(
            f"""
            SELECT i.user_message, i.llm_response,
                   f.rating, f.correction_kapampangan, f.correction_english
            FROM feedback f
            JOIN interactions i ON i.id = f.interaction_id
            WHERE {where}
            ORDER BY f.timestamp
            """,
            *params,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    def generate():
        total = 0
        exported = 0
        for row in rows:
            total += 1
            prompt = row["user_message"]
            original = row["llm_response"]
            correction = row["correction_kapampangan"] or row["correction_english"]
            rating = row["rating"]

            if body.format == "sft":
                if rating == "thumbs_up":
                    yield json.dumps({"prompt": prompt, "response": original}) + "\n"
                    exported += 1
                elif rating == "thumbs_down" and correction:
                    yield json.dumps({"prompt": prompt, "response": correction}) + "\n"
                    exported += 1
            else:  # dpo
                if rating == "thumbs_down" and correction:
                    yield json.dumps({
                        "prompt": prompt,
                        "chosen": correction,
                        "rejected": original,
                    }) + "\n"
                    exported += 1

    filename = f"training_{body.format}_{body.min_authority_level}.jsonl"
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
