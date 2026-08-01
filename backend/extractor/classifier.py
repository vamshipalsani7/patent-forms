"""Document classification stage — anchor-based, deterministic.

Vocabulary rationale: the output values are exactly the `sourceType` strings
in vocabulary/registry.json. DocumentType enum members must stay aligned.
"""

from __future__ import annotations

import re

from models.patent_profile import DocumentType


# Anchor phrases in descending specificity.  The classifier tries each type in
# the order listed and returns the first confident match.  Case-insensitive.
# These anchors come directly from the printed form headers documented in
# docs/specifications/ — fixed-layout statutory forms whose headers haven't
# changed since 2003 are the most stable possible anchors.
#
# ORDER IS LOAD-BEARING.  Statutory forms with unique printed titles come first;
# broad descriptive anchors come last.  Specifically, FORM5 must precede
# FORM2_SPECIFICATION: the printed body of Form 5 contains the phrase "complete
# specification", so with the reverse order every Form 5 classified as a
# specification and its inventor facts were never extracted.

_ANCHORS: list[tuple[DocumentType, list[str]]] = [
    (
        DocumentType.FORM1,
        [
            r"APPLICATION\s+FOR\s+GRANT\s+OF\s+PATENT",
            r"FORM\s*(?:NO\.?\s*)?1\b",
            r"See\s+Section\s+7,?\s*54\s+(?:and|&)\s+135",
        ],
    ),
    (
        DocumentType.FORM3,
        [
            r"STATEMENT\s+AND\s+UNDERTAKING\s+UNDER\s+SECTION\s+8",
            r"FORM\s*(?:NO\.?\s*)?3\b",
        ],
    ),
    (
        DocumentType.FORM5,
        [
            r"DECLARATION\s+AS\s+TO\s+INVENTORSHIP",
            r"FORM\s*(?:NO\.?\s*)?5\b",
        ],
    ),
    (
        DocumentType.FORM16_REGISTRATION,
        [
            r"APPLICATION\s+FOR\s+REGISTRATION\s+OF\s+(?:A\s+)?(?:TITLE|ASSIGNMENT|INTEREST)",
            r"FORM\s*(?:NO\.?\s*)?16\b",
            r"See\s+sections?\s+69\(1\)",
        ],
    ),
    (
        DocumentType.FORM26_AUTHORISATION,
        [
            r"FORM\s+FOR\s+AUTHORISATION\s+OF\s+A\s+PATENT\s+AGENT",
            r"POWER\s+OF\s+ATTORNEY",
            r"FORM\s*(?:NO\.?\s*)?26\b",
            r"See\s+sections?\s+127\s+and\s+132",
        ],
    ),
    (
        DocumentType.FORM28,
        [
            r"TO\s+BE\s+SUBMITTED\s+BY\s+A\s+SMALL\s+ENTITY",
            r"FORM\s*(?:NO\.?\s*)?28\b",
        ],
    ),
    (
        DocumentType.FORM2_SPECIFICATION,
        [
            r"COMPLETE\s+SPECIFICATION",
            r"PROVISIONAL\s+SPECIFICATION",
            r"FORM\s*(?:NO\.?\s*)?2\b",
        ],
    ),
    (
        DocumentType.PATENT_CERTIFICATE,
        [
            r"PATENT\s+CERTIFICATE",
            r"This\s+is\s+to\s+certify\s+that\s+a\s+patent",
            r"CERTIFICATE\s+OF\s+GRANT\s+OF\s+PATENT",
        ],
    ),
    (
        DocumentType.ASSIGNMENT_DOCUMENT,
        [
            r"DEED\s+OF\s+ASSIGNMENT",
            r"ASSIGNMENT\s+DEED",
            r"THIS\s+ASSIGNMENT\s+IS\s+MADE",
            r"hereinafter\s+referred\s+to\s+as\s+(?:the\s+)?[\"'“‘]?ASSIGNEE",
        ],
    ),
    (
        DocumentType.PCT_DOCUMENT,
        [
            r"PATENT\s+COOPERATION\s+TREATY",
            r"INTERNATIONAL\s+APPLICATION\s+(?:NO|NUMBER)",
            r"PCT/[A-Z]{2}\d{4}/\d+",
        ],
    ),
    (
        DocumentType.PRIORITY_DOCUMENT,
        [
            r"CERTIFIED\s+COPY",
            r"PRIORITY\s+DOCUMENT",
            r"CONVENTION\s+APPLICATION",
        ],
    ),
    (
        DocumentType.PUBLICATION_RECORD,
        [
            r"PATENT\s+OFFICE\s+JOURNAL",
            r"OFFICIAL\s+JOURNAL\s+OF\s+THE\s+PATENT\s+OFFICE",
        ],
    ),
]


class DocumentClassifier:
    """Classifies a document from its raw text using static anchor phrases."""

    def classify(self, raw_text: str) -> DocumentType:
        """Return the DocumentType matched by the first anchor set that fires.

        Returns DocumentType.UNKNOWN when no confident match is found — not
        GENERIC (which is a processing mode, not a classification outcome).
        """
        # Work from the first 3000 characters for speed; headers appear early.
        head = raw_text[:3000].upper()
        for doc_type, patterns in _ANCHORS:
            for pattern in patterns:
                if re.search(pattern, head, re.IGNORECASE):
                    return doc_type
        return DocumentType.UNKNOWN
