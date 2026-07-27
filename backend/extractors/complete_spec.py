"""Extractor for Complete Specification patent documents."""

from __future__ import annotations

from typing import Any, Dict


class CompleteSpecificationExtractor:
    """Extracts structured fields from a Complete Specification document.

    Extraction logic is intentionally not implemented yet.
    """

    def extract(self, raw_text: str) -> Dict[str, Any]:
        """Extract structured fields from a Complete Specification.

        Args:
            raw_text: Raw text of the document.

        Returns:
            A mapping of extracted field names to values, suitable for
            populating a :class:`models.patent_profile.PatentProfile`.

        Raises:
            NotImplementedError: Always, until extraction is implemented.
        """
        raise NotImplementedError(
            "Complete Specification extraction is not implemented yet."
        )
