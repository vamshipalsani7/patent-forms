"""Profile assembly stage — selects the right extractor, produces DocumentExtract.

To add support for a new document type:
  1. Add a DocumentType member in models/patent_profile.py.
  2. Add classifier anchors for it in extractor/classifier.py.
  3. Subclass PatternExtractor in extractors/ declaring its patterns.
  4. Register it in _EXTRACTOR_REGISTRY below.
  That is the entire change required — no other file needs modification.

Steps 1 and 2 are not optional: an extractor registered against a DocumentType
the classifier can never emit is dead code that looks live.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from models.document_extract import DocumentExtract
from models.patent_profile import DocumentType
from extractors.assignment_document import AssignmentDocumentExtractor
from extractors.form1 import Form1Extractor
from extractors.form2_specification import Form2SpecificationExtractor
from extractors.form5 import Form5Extractor
from extractors.form26_authorisation import Form26AuthorisationExtractor
from extractors.patent_certificate import PatentCertificateExtractor
from extractors.pct_document import PctDocumentExtractor
from extractors.priority_document import PriorityDocumentExtractor


# Registry maps DocumentType → extractor instance.
# Only types with specialised extractors are listed; everything else returns an
# empty DocumentExtract (no facts, no error) with its classification recorded.
#
# Listed in descending autofill demand — the number of `autofill.sources[]`
# entries across the 34 form definitions that cite each sourceType. That count
# is what justifies an extractor existing at all.
_EXTRACTOR_REGISTRY: dict[DocumentType, object] = {
    DocumentType.FORM1: Form1Extractor(),                              # 124
    DocumentType.PATENT_CERTIFICATE: PatentCertificateExtractor(),     #  63
    DocumentType.FORM26_AUTHORISATION: Form26AuthorisationExtractor(),  #  32
    DocumentType.FORM2_SPECIFICATION: Form2SpecificationExtractor(),   #  20
    DocumentType.ASSIGNMENT_DOCUMENT: AssignmentDocumentExtractor(),   #  10
    DocumentType.PRIORITY_DOCUMENT: PriorityDocumentExtractor(),       #   9
    DocumentType.FORM5: Form5Extractor(),                              #   7
    DocumentType.PCT_DOCUMENT: PctDocumentExtractor(),                 #   6
}
# Not registered, deliberately:
#   form3, form16_registration, form28, publication_record — classifiable, but
#   too little authored demand to justify pattern work yet (form16_registration
#   is cited once; the others not at all).
#   FER, Hearing Notice, Controller Order — see docs/backlog.md. No definition
#   consumes a fact from them, so there is nothing for an extractor to feed.


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
