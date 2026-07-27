"""Fact — the atomic unit of extraction.

Every value the engine extracts from a document is wrapped in a Fact so the
user can always answer "where did this come from?". Provenance is not a nice-
to-have: without it, a suggestion is indistinguishable from an assertion, and
these values end up on signed statutory filings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class Fact(BaseModel):
    """One extracted value with full provenance."""

    key: str
    """Vocabulary key from vocabulary/registry.json, e.g. 'applicant.name'."""

    value: Any
    """The extracted value. Type matches the key's `type` in the registry."""

    document_id: str
    """documentStore id (assigned by documentUpload.js on the frontend)."""

    source_type: str
    """Classifier result — matches a sourceType in vocabulary/registry.json,
    e.g. 'form1'. Lets the autofill mapper filter by document type."""

    page: Optional[int] = None
    """1-indexed page number where the value was found. None if unknown."""

    bounding_box: Optional[list[float]] = None
    """[x, y, width, height] in page units where the text was found.
    None if the extraction method does not yield positional data."""

    confidence: float = Field(ge=0.0, le=1.0)
    """Extraction confidence 0.0–1.0. Used as a tiebreak in the profile merge."""

    method: str
    """How the value was found: 'acroform' | 'anchor' | 'ocr' | 'manual'."""

    extractor_version: str
    """e.g. 'form1@1'. Lets the pipeline identify stale facts after an
    extractor is improved without requiring a re-upload."""

    extracted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    """ISO-8601 timestamp of extraction."""
