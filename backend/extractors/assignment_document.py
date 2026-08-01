"""Assignment Deed extractor — transfers of proprietorship.

Keys served (10 citations, all on Form 16 and the post-grant transfer forms):
    assignee.name (4) · assignee.address (4) · assignee.nationality (2)

This is the least structured document we extract from: a deed is drafted by a
firm, not printed from a statutory template, so there is no fixed layout to
anchor on. Confidences are correspondingly lower than the certificate's.

The controlling risk here is not a missed value — it is capturing the ASSIGNOR
as the ASSIGNEE. The two parties are described in identical prose ("a company
incorporated under the laws of …, having its registered office at …") a few
lines apart, so a value taken from the wrong block looks entirely correct in
review and transfers the patent to the wrong party on a filed Form 16.

Every prose pattern below therefore ends with a *tempered* bridge to the
ASSIGNEE marker::

    (?:(?!ASSIGNOR)[\\s\\S]){0,400}?ASSIGNEE

which allows the capture to sit up to 400 characters before the word ASSIGNEE
but fails outright if the word ASSIGNOR appears in between. A deed that does not
match one of these shapes yields nothing, which is the correct outcome: the user
types two fields, instead of reviewing a confident and wrong answer.
"""

from __future__ import annotations

from extractors.base import PatternExtractor

# Bridge from a captured value to the ASSIGNEE marker that qualifies it, which
# cannot cross the assignor's block. See the module docstring.
_TO_ASSIGNEE = r"(?:(?!ASSIGNOR)[\s\S]){0,400}?ASSIGNEE"


class AssignmentDocumentExtractor(PatternExtractor):
    """Extracts the assignee's particulars from a deed of assignment."""

    EXTRACTOR_VERSION = "assignment_document@1"
    SOURCE_TYPE = "assignment_document"

    PATTERNS = [
        (
            "assignee.name",
            [
                # Structured deeds with a party schedule.
                r"ASSIGNEE\s*(?:\(S\))?\s*(?:NAME)?\s*[:\-]\s*([^\n\r]{3,150})",
                # Recital form: "AND\n<party>, a company …\n… hereinafter …
                # ASSIGNEE". The party name opens its block, so this is tried
                # before the adjacent-marker pattern below.
                r"(?:^|\n)\s*AND\s*[\n\r]+\s*([^\n\r,]{3,150})" + _TO_ASSIGNEE,
                # Single-line form: "Globex Corporation (hereinafter … ASSIGNEE)".
                # The capture is anchored to the start of a line: without that
                # anchor it matches the tail of whatever line precedes the
                # marker, which on a normal deed is the last fragment of the
                # address — this returned "USA" as the assignee's name.
                r"(?:^|\n)[ \t]*([^\n\r,]{3,150}?)\s*,?\s*\(\s*(?:hereinafter\s+)?"
                r"(?:referred\s+to\s+as\s+|called\s+)?(?:the\s+)?[\"'“‘]?ASSIGNEE",
            ],
            0.80,
        ),
        (
            "assignee.address",
            [
                r"ASSIGNEE\s*(?:\(S\))?[\s\S]{0,200}?Address\s*[:\-]\s*([^\n\r]{5,200})",
                r"having\s+its\s+(?:registered\s+office|principal\s+place\s+of\s+business|"
                r"office|address)\s+at\s+([^\n\r]{5,200})" + _TO_ASSIGNEE,
            ],
            0.75,
        ),
        (
            "assignee.nationality",
            [
                r"ASSIGNEE\s*(?:\(S\))?[\s\S]{0,200}?Nationality\s*[:\-]\s*([^\n\r]{3,60})",
                r"(?:incorporated|organis\w+|organiz\w+|existing)\s+under\s+the\s+laws\s+of\s+"
                r"(?:the\s+)?([^\n\r,\.]{3,60})" + _TO_ASSIGNEE,
            ],
            0.70,
        ),
    ]
