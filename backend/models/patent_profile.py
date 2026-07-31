"""Patent Profile — merged, cross-document projection.

AMENDED FROM SCAFFOLD: the original PatentProfile held one `source: SourceDocument`
(per-document-shaped). The final architecture requires a cross-document view:
"which Form 1 OR specification OR certificate has the applicant name?" cannot be
answered by a single-document model.

This amendment splits the model into two levels:
  DocumentExtract  (models/document_extract.py) — one per uploaded PDF, immutable.
  PatentProfile    (this file)                  — merged projection across a workspace.

Backward-compat: `SourceDocument`, `DocumentType`, and `PatentProfile.fields` are
preserved so nothing that read the scaffold breaks. PatentProfile now holds a list
of DocumentExtracts and exposes `get_facts(key, source_type)` for the autofill
mapper — the only query interface; no per-form logic lives here.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from models.document_extract import DocumentExtract
from models.fact import Fact


class DocumentType(str, Enum):
    """Classification of an uploaded patent document.

    Must stay in sync with vocabulary/registry.json sourceTypes.
    Add a member here whenever adding a new extractor in extractors/.
    """

    FORM1 = "form1"
    FORM2_SPECIFICATION = "form2_specification"
    FORM3 = "form3"
    FORM5 = "form5"
    PATENT_CERTIFICATE = "patent_certificate"
    PRIORITY_DOCUMENT = "priority_document"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class SourceDocument(BaseModel):
    """Metadata describing the original uploaded file (preserved from scaffold)."""

    filename: Optional[str] = None
    content_type: Optional[str] = None
    storage_path: Optional[str] = None


class PatentProfile(BaseModel):
    """Merged projection across all DocumentExtracts in ONE workspace.

    `extracts` is the canonical source of data.
    `get_facts()` is the only query interface the autofill mapper uses.
    `fields` is a computed backward-compat dict (highest-confidence per key).

    When `workspace_id` is set, the profile refuses to hold an extract from any
    other workspace. This is the last line of defence behind the content store:
    even a profile assembled by hand from a mixed list of extracts fails loudly
    instead of silently producing cross-matter suggestions.
    """

    workspace_id: Optional[str] = None
    """The workspace this profile answers for. None means unscoped, which is
    only appropriate for tests and ad-hoc analysis — never for the API."""

    extracts: List[DocumentExtract] = Field(default_factory=list)

    @model_validator(mode="after")
    def _reject_extracts_from_other_workspaces(self) -> "PatentProfile":
        if self.workspace_id is None:
            return self
        foreign = {
            e.document_id: e.workspace_id
            for e in self.extracts
            if e.workspace_id != self.workspace_id
        }
        if foreign:
            raise ValueError(
                f"PatentProfile for workspace '{self.workspace_id}' was given extracts "
                f"belonging to other workspaces: {foreign}"
            )
        return self

    @property
    def fields(self) -> Dict[str, Any]:
        """Flat dict of the highest-confidence fact per key (backward-compat)."""
        result: Dict[str, Any] = {}
        all_facts = [f for e in self.extracts for f in e.facts]
        for fact in sorted(all_facts, key=lambda f: f.confidence):
            result[fact.key] = fact.value
        return result

    def get_facts(
        self,
        key: str,
        source_type: Optional[str] = None,
    ) -> List[Fact]:
        """All facts for a vocabulary key, ordered by confidence descending.

        Args:
            key:         Vocabulary key, e.g. 'applicant.name'.
            source_type: If given, restrict to this sourceType only — used by
                         the mapper iterating autofill.sources[] in preference
                         order (authored per-field in the definition).
        """
        facts = [
            f
            for e in self.extracts
            for f in e.facts
            if f.key == key
            and (source_type is None or f.source_type == source_type)
        ]
        return sorted(facts, key=lambda f: -f.confidence)

    def add_extract(self, extract: DocumentExtract) -> None:
        """Add a DocumentExtract to this profile (replace if same document_id).

        Raises:
            ValueError: if the extract belongs to a different workspace.
        """
        if self.workspace_id is not None and extract.workspace_id != self.workspace_id:
            raise ValueError(
                f"cannot add document '{extract.document_id}' from workspace "
                f"'{extract.workspace_id}' to a profile for workspace '{self.workspace_id}'"
            )
        self.extracts = [e for e in self.extracts if e.document_id != extract.document_id]
        self.extracts.append(extract)
