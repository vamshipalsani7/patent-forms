"""Fallback extractor for documents without a specialised extractor."""

from __future__ import annotations

from typing import Any, Dict


class GenericExtractor:
    """Best-effort extractor used when no specialised extractor applies.

    Selected for :attr:`models.patent_profile.DocumentType.GENERIC` (and as a
    safe fallback). Extraction logic is intentionally not implemented yet.
    """

    def extract(self, raw_text: str) -> Dict[str, Any]:
        """Extract best-effort structured fields from any document.

        Args:
            raw_text: Raw text of the document.

        Returns:
            A mapping of extracted field names to values.

        Raises:
            NotImplementedError: Always, until extraction is implemented.
        """
        raise NotImplementedError("Generic extraction is not implemented yet.")
