"""Profile assembly stage of the extraction pipeline.

Given the raw text and detected document type, selects the appropriate
specialised extractor from the ``extractors`` package, runs it, and assembles
the final :class:`models.patent_profile.PatentProfile`.
"""

from __future__ import annotations

from typing import Optional

from models.patent_profile import DocumentType, PatentProfile, SourceDocument


class ProfileBuilder:
    """Builds a :class:`PatentProfile` from extracted document data.

    Assembly logic is intentionally not implemented yet. Concrete
    implementations will map a :class:`DocumentType` to the matching extractor
    and populate the profile's structured fields.
    """

    def build(
        self,
        raw_text: str,
        document_type: DocumentType,
        source: Optional[SourceDocument] = None,
    ) -> PatentProfile:
        """Assemble a Patent Profile from pipeline outputs.

        Args:
            raw_text: Raw text extracted from the document.
            document_type: Document type detected by the classifier.
            source: Metadata describing the original uploaded file.

        Returns:
            A fully populated :class:`PatentProfile`.

        Raises:
            NotImplementedError: Always, until assembly is implemented.
        """
        raise NotImplementedError("Profile assembly is not implemented yet.")
