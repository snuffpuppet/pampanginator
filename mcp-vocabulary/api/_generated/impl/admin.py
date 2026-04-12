"""
Admin API implementation.

Subclasses BaseAdminApi for POST /admin/reseed, GET /admin/stats, GET /admin/export.
"""

import json
from datetime import date
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field

from mcp_vocabulary_api.apis.admin_api_base import BaseAdminApi
from mcp_vocabulary_api.models.admin_export_response import AdminExportResponse
from mcp_vocabulary_api.models.admin_stats_response import AdminStatsResponse
from mcp_vocabulary_api.models.reseed_response import ReseedResponse
from mcp_vocabulary_api.models.vocabulary_entry import VocabularyEntry

from services import db, seed


class AdminApi(BaseAdminApi):

    async def admin_reseed_post(self) -> ReseedResponse:
        count = await seed.seed_if_needed(force=True)
        return ReseedResponse(reseeded=count)

    async def admin_stats_get(self) -> AdminStatsResponse:
        pool = db.pool()
        last_seed_row = await pool.fetchrow(
            "SELECT MIN(created_at) FROM vocabulary WHERE seeded_from_canonical = TRUE"
        )
        seeded_row = await pool.fetchrow(
            "SELECT COUNT(*) FROM vocabulary WHERE seeded_from_canonical = TRUE"
        )
        local_row = await pool.fetchrow(
            "SELECT COUNT(*) FROM vocabulary WHERE seeded_from_canonical = FALSE"
        )
        return AdminStatsResponse(
            last_seeded=last_seed_row[0].isoformat() if last_seed_row[0] else None,
            seeded_count=seeded_row[0],
            local_additions=local_row[0],
        )

    async def admin_export_get(
        self,
        min_authority_level: Optional[Annotated[int, Field(le=4, strict=True, ge=1)]],
        since: Annotated[Optional[date], Field(description="ISO date — only entries added after this date")],
    ) -> AdminExportResponse:
        pool = db.pool()
        resolved_level = min_authority_level if min_authority_level is not None else 1

        conditions = ["seeded_from_canonical = FALSE", "authority_level <= $1"]
        params: list = [resolved_level]
        if since:
            params.append(str(since))
            conditions.append(f"created_at >= ${len(params)}::date")

        rows = await pool.fetch(
            f"""
            SELECT term, meaning, part_of_speech, aspect_forms, examples,
                   usage_notes, authority_level, source, verified_by, notes, contributor, added_date
            FROM vocabulary
            WHERE {' AND '.join(conditions)}
            ORDER BY added_date, term
            """,
            *params,
        )

        vocabulary = []
        for row in rows:
            entry: dict = {"term": row["term"], "meaning": row["meaning"]}
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
            if row["notes"]:
                entry["notes"] = row["notes"]
            vocabulary.append(VocabularyEntry(**entry))

        return AdminExportResponse(vocabulary=vocabulary)
