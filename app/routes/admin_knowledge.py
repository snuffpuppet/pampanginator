"""
Admin knowledge sharing routes — Decision 19.

Exposes endpoints for the admin Contributions tab:
  GET  /api/admin/sync/status
  POST /api/admin/sync/export
  POST /api/admin/sync/reseed
  GET  /api/admin/contributions/pending
  POST /api/admin/contributions/upload
  POST /api/admin/contributions/{id}/approve
  POST /api/admin/contributions/{id}/reject
"""

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services import knowledge

router = APIRouter(tags=["admin"])


# ─── Sync status ──────────────────────────────────────────────────────────────

@router.get("/admin/sync/status")
async def sync_status():
    """Knowledge sharing sync status for the admin Sync Status view."""
    return await knowledge.get_sync_status()


# ─── Export local contributions as zip ────────────────────────────────────────

class ExportContributionsRequest(BaseModel):
    contributor: str = "unknown"
    min_authority_level: int = 1
    since: Optional[str] = None


@router.post("/admin/sync/export")
async def export_contributions(body: ExportContributionsRequest):
    """
    Export locally added (non-seeded) vocabulary and grammar entries as a zip archive.
    Returns the zip file as a download.
    """
    data = await knowledge.export_local_contributions(
        min_authority_level=body.min_authority_level,
        since=body.since,
    )

    vocab = data["vocabulary"]
    nodes = data["grammar_nodes"]
    edges = data["grammar_edges"]

    # Apply contributor override
    for entry in vocab:
        entry["contributor"] = body.contributor
    for node in nodes:
        node["contributor"] = body.contributor

    manifest = {
        "contributor": body.contributor,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "min_authority_level": body.min_authority_level,
        "since": body.since,
        "counts": {
            "vocabulary": len(vocab),
            "grammar_nodes": len(nodes),
            "grammar_edges": len(edges),
        },
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("contrib_vocabulary.json", json.dumps(vocab, indent=2, ensure_ascii=False))
        zf.writestr("contrib_grammar_nodes.json", json.dumps(nodes, indent=2, ensure_ascii=False))
        zf.writestr("contrib_grammar_edges.json", json.dumps(edges, indent=2, ensure_ascii=False))
    buf.seek(0)

    safe_name = body.contributor.lower().replace(" ", "_")
    date_str = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    filename = f"{safe_name}_{date_str}_contribution.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Force reseed from canonical files ───────────────────────────────────────

class ReseedRequest(BaseModel):
    confirm: str  # must equal "reseed" — prevents accidental calls


@router.post("/admin/sync/reseed")
async def force_reseed(body: ReseedRequest):
    """
    Truncate and reseed vocabulary and grammar tables from canonical data files.

    Requires { "confirm": "reseed" } in the request body to prevent accidental
    data loss. Local additions not yet exported will be permanently deleted.
    """
    if body.confirm != "reseed":
        raise HTTPException(status_code=400, detail='Send { "confirm": "reseed" } to confirm')
    try:
        result = await knowledge.reseed_from_canonical()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Pending contributions (Mode 3) ───────────────────────────────────────────

@router.get("/admin/contributions/pending")
async def get_pending_contributions():
    """Return pending contributions from the pending_contributions table."""
    records = await knowledge.get_pending_contributions()
    return {"count": len(records), "records": records}


# ─── Contribution zip upload (Mode 2) ─────────────────────────────────────────

@router.post("/admin/contributions/upload")
async def upload_contribution(file: UploadFile = File(...)):
    """
    Accept a contribution zip file (from package_contribution.py).
    Extracts and returns the manifest and entries for review — does not
    write to the database. Call /approve on individual entries after review.
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    content = await file.read()
    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise HTTPException(status_code=400, detail="Not a valid zip file")

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        names = zf.namelist()

        if "manifest.json" not in names:
            raise HTTPException(status_code=400, detail="Missing manifest.json in zip")

        manifest = json.loads(zf.read("manifest.json"))

        vocab = (
            json.loads(zf.read("contrib_vocabulary.json"))
            if "contrib_vocabulary.json" in names else []
        )
        nodes = (
            json.loads(zf.read("contrib_grammar_nodes.json"))
            if "contrib_grammar_nodes.json" in names else []
        )
        edges = (
            json.loads(zf.read("contrib_grammar_edges.json"))
            if "contrib_grammar_edges.json" in names else []
        )

    return {
        "manifest": manifest,
        "vocabulary": vocab,
        "grammar_nodes": nodes,
        "grammar_edges": edges,
        "counts": {
            "vocabulary": len(vocab),
            "grammar_nodes": len(nodes),
            "grammar_edges": len(edges),
        },
    }


# ─── Approve / reject individual contributions ────────────────────────────────

class ContributionReviewBody(BaseModel):
    reviewed_by: Optional[str] = None
    note: Optional[str] = None


@router.post("/admin/contributions/{contrib_id}/approve")
async def approve_contribution(contrib_id: str, body: ContributionReviewBody = ContributionReviewBody()):
    try:
        return await knowledge.approve_contribution(contrib_id, reviewed_by=body.reviewed_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/contributions/{contrib_id}/reject")
async def reject_contribution(contrib_id: str, body: ContributionReviewBody = ContributionReviewBody()):
    try:
        return await knowledge.reject_contribution(
            contrib_id, reviewed_by=body.reviewed_by, note=body.note
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
