"""Document classification stage of the extraction pipeline.

Given the raw text of a document, determines its
:class:`models.patent_profile.DocumentType` so the correct specialised
extractor (see the ``extractors`` package) can be selected downstream.
"""

from __future__ import annotations

from models.patent_profile import DocumentType


class DocumentClassifier:
    """Determines the :class:`DocumentType` of a document from its raw text.

    Classification logic is intentionally not implemented yet.
    """

    def classify(self, raw_text: str) -> DocumentType:
        """Classify a document from its raw text.

        Args:
            raw_text: Raw text extracted from the document.

        Returns:
            The detected document type. Implementations should return
            :attr:`DocumentType.UNKNOWN` when no confident match is found.

        Raises:
            NotImplementedError: Always, until classification is implemented.
        """
        raise NotImplementedError("Document classification is not implemented yet.")
