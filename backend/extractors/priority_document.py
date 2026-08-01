"""Priority Document extractor — certified copies from foreign patent offices.

Keys served (9 citations, concentrated in Form 3's foreign-application table):
    foreignApplications[].country · .number · .filingDate (2 each)
    applicant.name (2) · invention.title (1)

The `foreignApplications[]` keys are deliberately NOT multi-valued here. One
certified copy is one foreign application; several priorities means several
uploaded documents, and each produces its own DocumentExtract. Harvesting
several application numbers out of a single certified copy would be picking up
the cited prior art printed on its cover page.

Foreign offices share no layout, so extraction leans on the two labels that are
near-universal on a certified copy ("Application Number", "Filing Date") plus
the issuing office's own name for the country.
"""

from __future__ import annotations

from extractors.base import PatternExtractor


class PriorityDocumentExtractor(PatternExtractor):
    """Extracts the foreign application's particulars from a certified copy."""

    EXTRACTOR_VERSION = "priority_document@1"
    SOURCE_TYPE = "priority_document"

    PATTERNS = [
        (
            "foreignApplications[].number",
            [
                r"(?:Application|Appln\.?)\s+(?:Number|No\.?|Serial\s+No\.?)\s*[:\-]?\s*"
                r"([A-Z0-9][A-Z0-9/\-,\. ]{3,30})",
            ],
            0.80,
        ),
        (
            "foreignApplications[].filingDate",
            [
                r"(?:Filing\s+Date|Date\s+of\s+Filing|Filed\s+on)\s*[:\-]?\s*([^\n\r]{6,40})",
            ],
            0.80,
        ),
        (
            "foreignApplications[].country",
            [
                # An explicit label is authoritative when present.
                r"Country\s*(?:of\s+(?:Filing|Origin))?\s*[:\-]\s*([^\n\r]{2,60})",
                # Otherwise read it off the issuing office's letterhead. Only
                # offices whose printed name *contains* the country as a usable
                # string are listed — "European Patent Office" and "WIPO" name no
                # country, so they are deliberately absent rather than guessed at.
                r"\b(UNITED\s+STATES)\s+PATENT\s+AND\s+TRADEMARK\s+OFFICE",
                r"\b(JAPAN)\s+PATENT\s+OFFICE",
                r"\b(CHINA)\s+NATIONAL\s+INTELLECTUAL\s+PROPERTY\s+ADMINISTRATION",
                r"INTELLECTUAL\s+PROPERTY\s+OFFICE\s+OF\s+(?:THE\s+)?([A-Z][A-Za-z ]{3,40})",
            ],
            0.75,
        ),
        (
            "applicant.name",
            [
                r"Applicant\s*(?:\(s\))?\s*(?:Name)?\s*[:\-]\s*([^\n\r]{3,120})",
                r"(?:^|\n)\s*Inventor\s*/\s*Applicant\s*[:\-]\s*([^\n\r]{3,120})",
            ],
            0.80,
        ),
        (
            "invention.title",
            [
                r"Title\s*(?:of\s+(?:the\s+)?Invention)?\s*[:\-]\s*([^\n\r]{5,200})",
            ],
            0.80,
        ),
    ]
