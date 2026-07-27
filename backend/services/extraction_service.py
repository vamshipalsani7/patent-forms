"""High-level extraction service.

Orchestrates the full pipeline that converts an uploaded document into a
:class:`models.patent_profile.PatentProfile`::

    PDF file -> raw text -> document type -> Patent Profile

This service is the single entry point intended for use by the API layer
(``app.py``). Per the frozen architecture, forms and all downstream features
consume the resulting Patent Profile, never the original PDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from extractor.classifier import DocumentClassifier
from extractor.pdf_reader import PDFReader
from extractor.profile_builder import ProfileBuilder
from models.patent_profile import PatentProfile, SourceDocument


class ExtractionService:
    """Converts uploaded documents into Patent Profiles.

    Pipeline collaborators are injected to keep the service easy to test and
    extend; sensible defaults are constructed when none are supplied.
    """

    def __init__(
        self,
        pdf_reader: Optional[PDFReader] = None,
        classifier: Optional[DocumentClassifier] = None,
        profile_builder: Optional[ProfileBuilder] = None,
    ) -> None:
        self.pdf_reader = pdf_reader or PDFReader()
        self.classifier = classifier or DocumentClassifier()
        self.profile_builder = profile_builder or ProfileBuilder()

    def build_profile(
        self,
        file_path: Union[str, Path],
        source: Optional[SourceDocument] = None,
    ) -> PatentProfile:
        """Run the full extraction pipeline for a single document.

        Args:
            file_path: Path to the uploaded PDF on disk (see ``uploads/``).
            source: Metadata describing the original uploaded file.

        Returns:
            The assembled :class:`PatentProfile`.

        Raises:
            NotImplementedError: Always, until the pipeline is implemented.
        """
        raise NotImplementedError("Extraction pipeline is not implemented yet.")
