"""Form 5 extractor — Declaration as to Inventorship.

Keys served (7 citations):
    inventor.name (6) · inventor.nationality (1)

Form 5 exists to name the true and first inventors, so it is the most
authoritative source for `inventor.name` we have — better than the
specification, whose inventor block is often left incomplete at drafting time.

The inventor names are read inside a REGION rather than from the whole document
because the form's operative sentence ("I/We, <applicant>, hereby declare that
the true and first inventor(s) …") names the *applicant* first. Whole-document
patterns pick that up as the inventor.

Note the classifier ordering this depends on: Form 5's printed body contains the
phrase "complete specification", so DocumentType.FORM5 must be tried before
FORM2_SPECIFICATION or this extractor is never reached at all.
"""

from __future__ import annotations

from extractors.base import PatternExtractor


class Form5Extractor(PatternExtractor):
    """Extracts declared inventor particulars from a Form 5."""

    EXTRACTOR_VERSION = "form5@1"
    SOURCE_TYPE = "form5"

    REGIONS = {
        "inventor": [
            r"\d?\.?\s*INVENTOR\s*\(?S?\)?\s*[:\n\r]",
            r"NAME\s+OF\s+(?:THE\s+)?INVENTOR",
            r"true\s+and\s+first\s+inventors?\s*\(?s?\)?[^\n\r]*(?:is\s*/\s*are|are|is)\s*[:\n\r]",
        ],
    }

    REGION_PATTERNS = {
        "inventor": [
            (
                "inventor.name",
                [
                    r"\(a\)\s*NAME\s*[:\-]?\s*([^\n\r]{3,120})",
                    r"NAME\s*(?:IN\s+FULL)?\s*[:\-]\s*([^\n\r]{3,120})",
                    r"\A[\s\r\n]*([A-Za-z][^\n\r]{2,119})",
                ],
                0.85,
            ),
            (
                "inventor.nationality",
                [
                    r"\(b\)\s*NATIONALITY\s*[:\-]?\s*([^\n\r]{3,60})",
                    r"NATIONALITY\s*[:\-]?\s*([^\n\r]{3,60})",
                ],
                0.85,
            ),
        ],
    }

    # Joint inventorship is the normal case on Form 5.
    MULTI_VALUE_KEYS = frozenset({"inventor.name"})

    ACROFORM_MAP = {
        "InventorName": ("inventor.name", 0.95),
        "NameOfInventor": ("inventor.name", 0.95),
        "InventorNationality": ("inventor.nationality", 0.90),
    }
