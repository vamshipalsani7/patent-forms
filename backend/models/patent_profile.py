"""Patent Profile data model.

The Patent Profile is the canonical, structured representation of an uploaded
patent-related document. Per the frozen architecture, every uploaded document
is converted into a Patent Profile, and every downstream feature (form
generation, analytics, search, etc.) consumes the Patent Profile rather than
the original PDF.

This module defines a deliberately minimal skeleton. Extend it with typed
sub-models as the extraction schema stabilises.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Classification of an uploaded patent document.

    Add a new member here when introducing support for a new document type,
    then implement a matching extractor in the ``extractors`` package.
    """

    COMPLETE_SPECIFICATION = "complete_specification"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class SourceDocument(BaseModel):
    """Metadata describing the original uploaded file."""

    filename: Optional[str] = None
    content_type: Optional[str] = None
    storage_path: Optional[str] = None


class PatentProfile(BaseModel):
    """Canonical structured representation of a patent document.

    This is intentionally a skeleton. The fields below mirror the outputs of
    the extraction pipeline:

    * ``source``        - provided by the upload/API layer
    * ``raw_text``      - produced by :class:`extractor.pdf_reader.PDFReader`
    * ``document_type`` - produced by :class:`extractor.classifier.DocumentClassifier`
    * ``fields``        - produced by the selected specialised extractor

    Replace the generic ``fields`` mapping with typed sub-models as the schema
    for each document type is finalised.
    """

    source: SourceDocument = Field(default_factory=SourceDocument)
    document_type: DocumentType = DocumentType.UNKNOWN
    raw_text: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict)
