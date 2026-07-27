"""DocumentExtract — immutable per-document extraction result.

One DocumentExtract is produced per uploaded PDF. It is never merged with
others and never edited — it is the raw extraction record. The PatentProfile
consumes a list of these and projects them into a merged, conflict-resolved
view of all facts across a workspace.

Why keep this separate from PatentProfile: auto-fill needs cross-document
answers (e.g. applicant name from Form 1 OR the specification OR the
certificate). A single-document model cannot answer cross-document questions.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from models.fact import Fact


class DocumentExtract(BaseModel):
    """Immutable extraction record for one uploaded PDF."""

    document_id: str
    """documentStore id — the frontend's handle for this document."""

    source_type: str
    """Classifier output, matching a sourceType in vocabulary/registry.json."""

    original_filename: str

    page_count: int = 0

    facts: list[Fact] = Field(default_factory=list)
    """All facts extracted from this document."""

    extractor_version: str
    """Version string of the extractor that produced this record."""

    extracted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
