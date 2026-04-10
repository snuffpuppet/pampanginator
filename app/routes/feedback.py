from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from services import feedback as feedback_svc

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    interaction_id: Optional[str] = Field(None, description="UUID of the interaction being rated")
    rating: str = Field(..., description="thumbs_up | thumbs_down")
    correction_kapampangan: Optional[str] = None
    correction_english: Optional[str] = None
    correction_note: Optional[str] = None
    corrected_by: Optional[str] = None
    authority_level: int = Field(default=3, ge=1, le=4)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"interaction_id": "uuid-here", "rating": "thumbs_up"},
                {
                    "interaction_id": "uuid-here",
                    "rating": "thumbs_down",
                    "correction_kapampangan": "E ku pa mangan.",
                    "correction_english": "I haven't eaten yet.",
                    "correction_note": "Model used mengan instead of mangan for the progressive form",
                    "corrected_by": "native_speaker",
                    "authority_level": 1,
                },
            ]
        }
    }


class ApproveRequest(BaseModel):
    authority_level: Optional[int] = Field(
        None, ge=1, le=4,
        description="Override the authority_level stored on the feedback record"
    )


@router.post("", status_code=201, summary="Submit feedback for an interaction")
async def submit_feedback(body: FeedbackRequest):
    if body.rating not in ("thumbs_up", "thumbs_down"):
        raise HTTPException(status_code=422, detail="rating must be thumbs_up or thumbs_down")
    try:
        feedback_id = await feedback_svc.write_feedback(
            interaction_id=body.interaction_id,
            rating=body.rating,
            correction_kapampangan=body.correction_kapampangan,
            correction_english=body.correction_english,
            correction_note=body.correction_note,
            corrected_by=body.corrected_by,
            authority_level=body.authority_level,
        )
        return {"id": feedback_id, "status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", summary="Get unreviewed feedback records")
async def pending_feedback():
    """Returns all feedback where reviewed=false, ordered by timestamp descending."""
    try:
        records = await feedback_svc.get_pending()
        return {"count": len(records), "records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", summary="Get all feedback records with optional filters")
async def all_feedback(
    rating: Optional[str] = Query(None, description="thumbs_up | thumbs_down"),
    authority_level: Optional[int] = Query(None, ge=1, le=4),
    applied: Optional[bool] = Query(None),
    after: Optional[str] = Query(None, description="ISO date/datetime"),
    before: Optional[str] = Query(None, description="ISO date/datetime"),
):
    try:
        records = await feedback_svc.get_all(
            rating=rating,
            authority_level=authority_level,
            applied=applied,
            after=after,
            before=before,
        )
        return {"count": len(records), "records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{feedback_id}/approve", summary="Approve a correction")
async def approve_feedback(feedback_id: str, body: ApproveRequest = ApproveRequest()):
    """
    Sets reviewed=true, applied=true.
    If correction_kapampangan is set on the record, writes it to the
    vocabulary table via the MCP vocabulary server at the specified
    authority_level.
    """
    try:
        result = await feedback_svc.approve(feedback_id, authority_level=body.authority_level)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{feedback_id}/reject", summary="Reject a correction")
async def reject_feedback(feedback_id: str):
    """Sets reviewed=true, applied=false. No correction is written."""
    try:
        result = await feedback_svc.reject(feedback_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
