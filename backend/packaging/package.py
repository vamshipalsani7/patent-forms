"""Assembling the complete filing package.

One call produces everything a professional needs before filing — the official
PDF, the editable DOCX, the filing summary and the provenance report — plus the
ZIP that carries all four. The user never chooses which file to generate; the
package is prepared as a whole.

Provenance entries are derived here from the suggestions the mapper already
produced, so this module adds no second field-mapping: it only turns a
suggestion into a sentence a professional can read.
"""

from __future__ import annotations

import io
import re
import zipfile
from datetime import date
from typing import Optional

from packaging.docx_builder import build_form_docx
from packaging.layout import ValueBook, field_label, normalise_path
from packaging.naming import filenames
from packaging.pdf_builder import build_form_pdf
from packaging.reports import build_filing_summary_pdf, build_provenance_pdf

# Order matters: it is the order the ZIP lists and the download screen shows.
PARTS = ("pdf", "docx", "summary", "provenance")


def _section_context(section: dict) -> str:
    """A short, readable section name: '1. APPLICANT(S) / OTHER…' -> 'Applicant(s)'.

    Used to disambiguate a field whose official label is a bare word. On the form
    "NAME" is clear from its position on the page; in an audit list it is not.
    """
    title = str(section.get("title") or "").strip()
    title = re.sub(r"^\s*\d+[A-Za-z]?[.)]\s*", "", title)   # drop "1. " / "3A) "
    title = re.split(r"[/(]", title)[0].strip()             # keep the leading phrase
    words = title.split()[:3]
    # A context ending in a preposition/article reads as a fragment
    # ("Request By The - Name"), so trim those tails off.
    while words and words[-1].lower() in {"by", "the", "of", "for", "to", "and", "a", "an", "in", "on"}:
        words.pop()
    if not words:
        return ""
    short = " ".join(words)
    return short.title() if short.isupper() else short


def field_labels(definition: dict) -> dict:
    """{field path (without instance indices): human label} for the whole form.

    Used to name fields in the provenance report — the label the user saw on
    screen, never a vocabulary key or a path. A very short label is prefixed with
    its section so the audit row stands on its own ("Applicant(s) - Name").
    """
    labels: dict = {}

    def walk(fields, base, context):
        for field in fields:
            path = base + "." + field["id"]
            label = field_label(field)
            if label:
                readable = label.title() if label.isupper() else label
                # Only a bare single word genuinely needs its section for meaning.
                if context and len(readable.split()) <= 1:
                    readable = "%s - %s" % (context, readable)
                labels[path] = readable
            if field.get("fields"):
                walk(field["fields"], path, context)
            for column in field.get("columns", []) or []:
                col_label = str(column.get("label") or column.get("id") or "")
                if col_label:
                    labels[path + "." + column["id"]] = col_label

    for section in definition.get("sections", []):
        walk(section.get("fields", []), section["id"], _section_context(section))
    return labels


def provenance_entries(
    definition: dict,
    suggestions: Optional[dict] = None,
    values: Optional[dict] = None,
) -> list:
    """Turn mapper suggestions into readable audit rows.

    Only fields the AI actually supplied appear — a value the user typed
    themselves has no document to cite. A value since edited is still listed,
    marked as edited, because the audit question is "where did this come from?"
    and the honest answer is "from there, then changed".

    Structural bookkeeping (a repeatable group's instance count) is skipped: it
    is renderer state, not a value on the form.
    """
    suggestions = suggestions or {}
    values = values or {}
    labels = field_labels(definition)
    book = ValueBook(values)
    entries = []

    for path in sorted(suggestions.keys()):
        suggestion = suggestions[path] or {}
        if suggestion.get("structural") or path.endswith("#count"):
            continue
        fact = suggestion.get("fact") or {}
        # A value the user entered themselves is not evidence from a document.
        if fact.get("source_type") == "user" or fact.get("method") == "manual":
            continue

        suggested = suggestion.get("value")
        current = values.get(path, suggested)
        edited = _as_plain(current) != _as_plain(suggested)
        shown = book.text(path) or _as_plain(current)
        if not shown:
            continue

        entries.append({
            "field": labels.get(normalise_path(path), normalise_path(path).split(".")[-1]),
            "value": shown,
            "source": suggestion.get("source_label") or "Uploaded document",
            "page": fact.get("page"),
            "edited": edited,
        })
    return entries


def _as_plain(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        import json
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def build_package(
    definition: dict,
    values: Optional[dict] = None,
    visible_paths: Optional[list] = None,
    counts: Optional[dict] = None,
    documents: Optional[list] = None,
    suggestions: Optional[dict] = None,
    generated_on: Optional[date] = None,
) -> dict:
    """Build every document in the filing package.

    Returns:
        { part: {'filename': str, 'bytes': bytes, 'media_type': str} } for each
        of PARTS, plus 'zip' carrying all four.
    """
    names = filenames(definition)
    entries = provenance_entries(definition, suggestions, values)

    built = {
        "pdf": {
            "filename": names["pdf"],
            "bytes": build_form_pdf(definition, values, visible_paths),
            "media_type": "application/pdf",
        },
        "docx": {
            "filename": names["docx"],
            "bytes": build_form_docx(definition, values, visible_paths),
            "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
        "summary": {
            "filename": names["summary"],
            "bytes": build_filing_summary_pdf(definition, counts, documents, generated_on),
            "media_type": "application/pdf",
        },
        "provenance": {
            "filename": names["provenance"],
            "bytes": build_provenance_pdf(definition, entries, generated_on),
            "media_type": "application/pdf",
        },
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for part in PARTS:
            archive.writestr(built[part]["filename"], built[part]["bytes"])
    built["zip"] = {
        "filename": names["zip"],
        "bytes": buffer.getvalue(),
        "media_type": "application/zip",
    }
    return built
