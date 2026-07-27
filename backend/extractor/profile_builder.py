"""Profile assembly stage — selects the right extractor, produces DocumentExtract.

To add support for a new document type:
  1. Add a DocumentType member in models/patent_profile.py.
  2. Implement an extractor in extractors/ that has extract_from_file().
  3. Register it in _EXTRACTOR_REGISTRY below.
  That is the entire change required — no other file needs modification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from models.document_extract import DocumentExtract
from models.patent_profile import DocumentType
from extractors.form1 import Form1Extractor


# Registry maps DocumentType → extractor instance.
# Only types with specialised extractors are listed; everything else falls
# through to _extract_generic() which returns an empty DocumentExtract (no
# facts, no error).
_EXTRACTOR_REGISTRY: dict[DocumentType, object] = {
    DocumentType.FORM1: Form1Extractor(),
}


class ProfileBuilder:
    """Builds a DocumentExtract from pipeline outputs."""

    def build(
        self,
        file_path: Union[str, Path],
        document_id: str,
        original_filename: str,
        document_type: DocumentType,
        page_texts: list[tuple[int, str]],
    ) -> DocumentExtract:
        """Assemble a DocumentExtract for one uploaded PDF.

        Args:
            file_path:          Path to the PDF on disk.
            document_id:        The documentStore id from the frontend.
            original_filename:  Original file name (for the extract record).
            document_type:      Output of DocumentClassifier.classify().
            page_texts:         [(page_number, text), …] from PDFReader.
        """
        extractor = _EXTRACTOR_REGISTRY.get(document_type)
        page_count = len(page_texts)

        if extractor is None:
            return DocumentExtract(
                document_id=document_id,
                source_type=document_type.value,
                original_filename=original_filename,
                page_count=page_count,
                facts=[],
                extractor_version="none@0",
            )

        facts = extractor.extract_from_file(file_path, document_id, page_texts)

        return DocumentExtract(
            document_id=document_id,
            source_type=document_type.value,
            original_filename=original_filename,
            page_count=page_count,
            facts=facts,
            extractor_version=getattr(extractor, "EXTRACTOR_VERSION", "unknown@0"),
        )
