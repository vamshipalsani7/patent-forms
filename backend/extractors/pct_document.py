"""PCT document extractor — international applications under the Patent
Cooperation Treaty.

Keys served (6 citations, on the national-phase entry forms):
    application.number (3) · application.filingDate (3)

Narrow by design. A PCT publication carries a great deal more — international
search report data, designated states, IPC classes — none of which any of the 34
form definitions asks for. Extracting it would be modelling the document rather
than serving the forms, which is the drift the demand-driven vocabulary rule
exists to prevent. If a definition later cites a new key from this source, the
pattern gets added then.

`application.number` here is the international application number
(PCT/IN2019/050123), which is what the national-phase forms print in that field.
"""

from __future__ import annotations

from extractors.base import PatternExtractor


class PctDocumentExtractor(PatternExtractor):
    """Extracts the international application's identifiers from a PCT document."""

    EXTRACTOR_VERSION = "pct_document@1"
    SOURCE_TYPE = "pct_document"

    PATTERNS = [
        (
            "application.number",
            [
                r"International\s+Application\s+(?:No\.?|Number)\s*[:\-]?\s*"
                r"(PCT\s*/\s*[A-Z]{2}\s*\d{4}\s*/\s*\d{4,8})",
                # Bare form, for cover sheets that print the number without a label.
                r"\b(PCT\s*/\s*[A-Z]{2}\s*\d{4}\s*/\s*\d{4,8})\b",
            ],
            0.85,
        ),
        (
            "application.filingDate",
            [
                # The parenthesised numeric restatement — "12 March 2019
                # (12.03.2019)" — is excluded from the capture; normalize_date
                # reads the spelled-out month, which is unambiguous.
                r"International\s+Filing\s+Date\s*[:\-]?\s*([^\n\r(]{5,40})",
                r"Date\s+of\s+International\s+Filing\s*[:\-]?\s*([^\n\r(]{5,40})",
            ],
            0.85,
        ),
    ]
