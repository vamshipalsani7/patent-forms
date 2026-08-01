"""Form 1 extractor — Application for Grant of Patent.

By far the richest source in the library: 124 of the ~272 authored
`autofill.sources[]` citations name `form1`, because a filed Form 1 restates
almost every party fact the other 33 forms need.

Keys served:
    applicant.name (28) · signatory.name (25) · application.number (21)
    application.filingDate (17) · applicant.address (15) · inventor.name (6)
    invention.title (5) · applicant.nationality (4)

Originally this file carried its own AcroForm reader, anchor loop and page
mapper, and its docstring instructed the next author to copy the whole file per
document type. That engine now lives in extractors/base.py; adding a document
type means declaring patterns, not duplicating ~250 lines of PDF plumbing.
"""

from __future__ import annotations

from extractors.base import PatternExtractor

# Module-level aliases, kept because callers and tests import them directly.
# The class attributes below are what the pipeline actually reads.
EXTRACTOR_VERSION = "form1@1"
SOURCE_TYPE = "form1"


class Form1Extractor(PatternExtractor):
    """Extracts structured facts from a Form 1 PDF."""

    EXTRACTOR_VERSION = EXTRACTOR_VERSION
    SOURCE_TYPE = SOURCE_TYPE

    PATTERNS = [
        (
            "application.number",
            [
                # "Application No. : 202211012345" or "Application No: 1234/DEL/2015"
                r"Application\s+No\.?\s*:?\s*([0-9]{1,6}/[A-Za-z]{2,5}/[0-9]{4})",
                r"Application\s+No\.?\s*:?\s*([0-9]{9,12})",
            ],
            0.80,
        ),
        (
            "application.filingDate",
            [
                r"(?:Date\s+of\s+[Ff]iling|Filing\s+Date)\s*[:\-]?\s*([^\n\r]{6,40})",
            ],
            0.80,
        ),
        (
            "invention.title",
            [
                # Section 5 header followed by the title on the next line(s)
                r"5\.\s*TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*[\n\r]+([^\n\r]{5,200})",
                r"TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*[\n\r]+([^\n\r]{5,200})",
                # Some PDFs put the title on the same line after a colon
                r"TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*:\s*([^\n\r]{5,200})",
            ],
            0.80,
        ),
        (
            "applicant.name",
            [
                # "Name in Full" label followed by name on the next line
                r"Name\s+in\s+Full\s*[\n\r]+([^\n\r|]{3,100})",
                # Table-cell variant: "Name in Full | <name> |"
                r"Name\s+in\s+Full\s*\|?\s*([^|\n\r]{3,100})",
                # "3A. APPLICANT(S)" section header → next non-empty line
                r"3A\.\s*APPLICANT\(S\)\s*[\n\r]+(?:[^\n\r]*[\n\r]+)?([^\n\r]{3,100})",
            ],
            0.80,
        ),
        (
            "applicant.address",
            [
                r"Address\s+for\s+Service[^\n\r]*[\n\r]+([^\n\r]{5,200})",
                r"(?:^|\n)\s*Address\s*[:\-]\s*([^\n\r]{5,200})",
            ],
            0.75,
        ),
        (
            "applicant.nationality",
            [
                r"Nationality\s*[:\-]?\s*([^\n\r|]{3,60})",
            ],
            0.75,
        ),
        (
            "signatory.name",
            [
                # "Name" after "Signature" at the bottom of Form 1
                r"(?:Signature.*?[\n\r]+)Name\s*:?\s*([^\n\r]{3,100})",
                # Simple Name field at the end
                r"Name\s+of\s+(?:the\s+)?(?:applicant|signatory)\s*:?\s*([^\n\r]{3,100})",
            ],
            0.75,
        ),
    ]

    REGIONS = {
        "inventor": [
            r"(?:6|7)\.\s*INVENTOR\s*\(?S?\)?",
            r"NAME\s+OF\s+(?:THE\s+)?INVENTOR",
        ],
    }

    REGION_PATTERNS = {
        "inventor": [
            (
                "inventor.name",
                [
                    r"Name\s+in\s+Full\s*[\n\r|]+\s*([^\n\r|]{3,100})",
                    r"NAME\s*[:\-]\s*([^\n\r]{3,120})",
                ],
                0.75,
            ),
        ],
    }

    MULTI_VALUE_KEYS = frozenset({"inventor.name"})

    ACROFORM_MAP = {
        "ApplicationNo":    ("application.number", 0.95),
        "Application No":   ("application.number", 0.95),
        "FilingDate":       ("application.filingDate", 0.95),
        "TitleOfInvention": ("invention.title", 0.95),
        "Title":            ("invention.title", 0.90),
        "ApplicantName":    ("applicant.name", 0.95),
        "NameinFull":       ("applicant.name", 0.95),
        "Name in Full":     ("applicant.name", 0.95),
        "ApplicantAddress": ("applicant.address", 0.90),
        "Nationality":      ("applicant.nationality", 0.90),
        "SignatoryName":    ("signatory.name", 0.90),
    }
