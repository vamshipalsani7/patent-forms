"""Specialised, per-document-type field extractors.

Each extractor consumes the raw text of a document and produces the structured
fields used to populate a :class:`models.patent_profile.PatentProfile`.
Extractors are selected by
:class:`extractor.profile_builder.ProfileBuilder` based on the document type
detected by :class:`extractor.classifier.DocumentClassifier`.

To add support for a new document type:
    1. Add a value to :class:`models.patent_profile.DocumentType`.
    2. Implement an extractor in this package that satisfies the
       :class:`Extractor` protocol below.
    3. Register it with the ``ProfileBuilder``.
"""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class Extractor(Protocol):
    """Contract implemented by every specialised extractor."""

    def extract(self, raw_text: str) -> Dict[str, Any]:
        """Return structured fields extracted from ``raw_text``."""
        ...
