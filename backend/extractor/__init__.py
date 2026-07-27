"""Core extraction pipeline.

Converts an uploaded patent document into a
:class:`models.patent_profile.PatentProfile` in three ordered stages::

    1. pdf_reader.PDFReader           - PDF file  -> raw text
    2. classifier.DocumentClassifier  - raw text  -> document type
    3. profile_builder.ProfileBuilder - raw text + type -> Patent Profile

This package owns the *pipeline orchestration* only. Specialised, per
document-type field extraction lives in the sibling ``extractors`` package.

Frozen architecture principle: every uploaded document is converted into a
Patent Profile. Forms are never generated directly from PDFs, and every future
feature consumes the Patent Profile produced here.
"""

from __future__ import annotations

from extractor.classifier import DocumentClassifier
from extractor.pdf_reader import PDFReader
from extractor.profile_builder import ProfileBuilder

__all__ = ["PDFReader", "DocumentClassifier", "ProfileBuilder"]
