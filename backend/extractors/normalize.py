"""Value normalisation shared by every extractor.

Two jobs, both of which exist because a Fact is a suggestion that lands on a
signed statutory filing:

  clean_value()    strips the artefacts a PDF text layer leaves behind, so the
                   user is not asked to review "Acme  Innovations  Pvt |".
  normalize_date() converts whatever the document printed into the ISO-8601
                   form the registry declares for `type: "date"` keys.

Date handling is deliberately conservative: an unrecognised format returns None
and the fact is simply not emitted. A wrong date on Form 3 or Form 27 is worse
than a blank one, because a blank is visible and a wrong date is not.
"""

from __future__ import annotations

import re
from typing import Optional

_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Ordinal suffixes appear constantly in Indian legal prose: "the 30th day of March".
_ORDINAL = re.compile(r"(\d{1,2})(?:st|nd|rd|th)\b", re.IGNORECASE)

_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
_NUMERIC = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")
_DAY_MONTH_YEAR = re.compile(
    r"\b(\d{1,2})\s+(?:day\s+of\s+)?([A-Za-z]{3,9})\.?,?\s+(\d{4})\b"
)
_MONTH_DAY_YEAR = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})\b")


def clean_value(raw: str) -> str:
    """Collapse PDF whitespace artefacts and strip table/label punctuation."""
    value = re.sub(r"\s{2,}", " ", raw.strip())
    return value.strip(" |,;:\t–—\"'“”‘’")


def normalize_date(raw: str) -> Optional[str]:
    """Return ``YYYY-MM-DD``, or None if no date can be read confidently.

    Recognised: ``2018-03-30``; ``30/03/2018``, ``30-03-2018``, ``30.03.2018``;
    ``30 March 2018`` and ``30th day of March, 2018``; ``March 30, 2018``.

    Numeric ``dd/mm/yyyy`` is read day-first, the Indian convention used
    throughout IPO documents. An ambiguous value such as ``03/04/2018`` is
    therefore 3 April, never 4 March. Where a document is known to be foreign
    (a US priority document, say), prefer a spelled-out month pattern rather
    than relying on this.
    """
    if not raw:
        return None

    text = _ORDINAL.sub(r"\1", raw.strip())

    match = _ISO.search(text)
    if match:
        return _assemble(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    match = _NUMERIC.search(text)
    if match:
        return _assemble(int(match.group(3)), int(match.group(2)), int(match.group(1)))

    match = _DAY_MONTH_YEAR.search(text)
    if match:
        month = _MONTHS.get(match.group(2).lower())
        if month:
            return _assemble(int(match.group(3)), month, int(match.group(1)))

    match = _MONTH_DAY_YEAR.search(text)
    if match:
        month = _MONTHS.get(match.group(1).lower())
        if month:
            return _assemble(int(match.group(3)), month, int(match.group(2)))

    return None


def _assemble(year: int, month: int, day: int) -> Optional[str]:
    """Format a Y/M/D triple, rejecting anything outside a plausible range."""
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        return None
    if not 1800 <= year <= 2200:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"
