"""Form 2 extractor — Complete and Provisional Specification.

One extractor serves both. They share the Form 2 cover-page layout and differ
only in the body (a provisional has no claims), and the fields we extract all
live on the cover page. The classifier maps both to
DocumentType.FORM2_SPECIFICATION, matching the single `form2_specification`
sourceType the registry declares.

Keys served (20 citations):
    applicant.name (8) · invention.title (4) · inventor.name (3)
    applicant.nationality · applicant.country · applicant.address
    inventor.nationality · inventor.address (1 each)

Why this one needs REGIONS while the certificate does not: the applicant and
inventor blocks are printed with identical sub-labels — "(a) NAME", "(b)
NATIONALITY", "(c) ADDRESS" under each heading. Matched against the whole
document, `NATIONALITY:` would return the applicant's nationality for
`inventor.nationality`, which is both wrong and completely invisible in review,
because it is a plausible value in a plausible field.
"""

from __future__ import annotations

from extractors.base import PatternExtractor

# Sub-labels shared by the applicant and inventor blocks, applied per region.
_NAME = [
    r"\(a\)\s*NAME\s*[:\-]?\s*([^\n\r]{3,120})",
    r"NAME\s*(?:IN\s+FULL)?\s*[:\-]\s*([^\n\r]{3,120})",
    # Unlabelled layouts print the name on the first line under the heading.
    r"\A[\s\r\n]*([A-Za-z][^\n\r]{2,119})",
]
_NATIONALITY = [
    r"\(b\)\s*NATIONALITY\s*[:\-]?\s*([^\n\r]{3,60})",
    r"NATIONALITY\s*[:\-]?\s*([^\n\r]{3,60})",
]
_ADDRESS = [
    r"\(c\)\s*ADDRESS\s*[:\-]?\s*([^\n\r]{5,200})",
    r"ADDRESS\s*[:\-]?\s*([^\n\r]{5,200})",
]


class Form2SpecificationExtractor(PatternExtractor):
    """Extracts cover-page facts from a Complete or Provisional Specification."""

    EXTRACTOR_VERSION = "form2_specification@1"
    SOURCE_TYPE = "form2_specification"

    REGIONS = {
        "applicant": [
            r"APPLICANT\s*\(?S?\)?\s*[:\n\r]",
            r"NAME\s+OF\s+(?:THE\s+)?APPLICANT",
        ],
        "inventor": [
            r"INVENTOR\s*\(?S?\)?\s*[:\n\r]",
            r"NAME\s+OF\s+(?:THE\s+)?INVENTOR",
        ],
    }

    REGION_PATTERNS = {
        "applicant": [
            ("applicant.name", _NAME, 0.85),
            ("applicant.nationality", _NATIONALITY, 0.85),
            ("applicant.address", _ADDRESS, 0.85),
            ("applicant.country", [r"COUNTRY\s*[:\-]?\s*([^\n\r]{2,60})"], 0.80),
        ],
        "inventor": [
            ("inventor.name", _NAME, 0.85),
            ("inventor.nationality", _NATIONALITY, 0.85),
            ("inventor.address", _ADDRESS, 0.85),
        ],
    }

    PATTERNS = [
        (
            "invention.title",
            [
                r"TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*[:\-]?\s*[\n\r]+\s*([^\n\r]{5,200})",
                r"TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*[:\-]\s*([^\n\r]{5,200})",
            ],
            0.85,
        ),
    ]

    # A specification routinely names several inventors; keeping only the first
    # would silently drop co-inventors from Form 5 and Form 1.
    MULTI_VALUE_KEYS = frozenset({"inventor.name"})
