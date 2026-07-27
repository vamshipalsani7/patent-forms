"""Data models for the Patent Forms backend.

Houses the canonical :class:`patent_profile.PatentProfile` and its supporting
types. Per the frozen architecture, the Patent Profile is the single structured
representation that every downstream feature consumes.
"""

from __future__ import annotations

from models.patent_profile import (
    DocumentType,
    PatentProfile,
    SourceDocument,
)

__all__ = ["PatentProfile", "SourceDocument", "DocumentType"]
