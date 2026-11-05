"""Professional filenames for the filing package.

A file that lands in a patent professional's downloads folder has to be
self-explanatory six months later, next to a dozen other matters. So the names
carry the form number and what the form does — ``Form18_RequestForExamination.pdf``
— never ``output.pdf`` and never a name with spaces (spaces break command-line
tooling and get percent-escaped in e-mail links).

The descriptive part comes from the definition's own official name, so it stays
correct for all 34 forms without a per-form table to maintain.
"""

from __future__ import annotations

import re

# Words dropped from the descriptive part: they are true of nearly every IPO
# form and add length without adding meaning.
_FILLER = {
    "for", "of", "the", "a", "an", "to", "in", "on", "and", "or", "any",
    "be", "is", "as", "by", "under", "with", "made", "such", "his", "its",
}

# Long enough to identify the form, short enough to stay readable in a file
# listing and in an e-mail attachment line.
_MAX_WORDS = 3


def _camel(text: str, max_words: int = _MAX_WORDS) -> str:
    """'Request / Express Request for Examination…' -> 'RequestExpressExamination'.

    Filler words are dropped and repeats collapsed, because several official
    names restate the same word ("Request / Express Request …") and a filename
    that stutters looks careless.
    """
    words = re.findall(r"[A-Za-z0-9]+", text or "")
    kept, seen = [], set()
    for word in words:
        lower = word.lower()
        if lower in _FILLER or lower in seen:
            continue
        seen.add(lower)
        kept.append(word)
    if not kept:
        kept = words[:max_words]
    return "".join(w[:1].upper() + w[1:].lower() for w in kept[:max_words])


def form_slug(definition: dict) -> str:
    """``Form18_RequestExaminationApplicationPatent`` — the shared filename stem.

    Uses ``formNumber`` (which may be '18A', not just digits) and the official
    name, so two related forms never collide.
    """
    number = str(definition.get("formNumber", "")).strip() or "Unknown"
    number = re.sub(r"[^A-Za-z0-9]", "", number)
    descriptor = _camel(definition.get("officialName", ""))
    return f"Form{number}_{descriptor}" if descriptor else f"Form{number}"


def filenames(definition: dict) -> dict:
    """Every filename in the package, keyed by part.

    Returns:
        { 'pdf', 'docx', 'summary', 'provenance', 'zip' } -> filename
    """
    stem = form_slug(definition)
    number = re.sub(r"[^A-Za-z0-9]", "", str(definition.get("formNumber", "")).strip()) or "Unknown"
    return {
        "pdf": f"{stem}.pdf",
        "docx": f"{stem}.docx",
        "summary": f"Form{number}_FilingSummary.pdf",
        "provenance": f"Form{number}_Provenance.pdf",
        "zip": f"Form{number}_FilingPackage.zip",
    }
