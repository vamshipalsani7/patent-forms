"""The two accompanying documents: filing summary and provenance report.

Filing summary — a one-page record of what was prepared: which form, when, from
which documents, and how much was completed automatically versus by hand. It
travels with the filing as the professional's own record.

Provenance report — the audit trail: for each value the AI supplied, which
document it came from and which page. It is NOT filed with the IPO; it exists so
a professional (or a later colleague) can answer "where did this come from?"
without re-reading the source documents.

Both are written in professional language. Neither exposes a vocabulary key, a
sourceType, a mapper path, a confidence figure or any JSON.
"""

from __future__ import annotations

import io
from datetime import date
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_MARGIN = 18 * mm
_RULE = colors.HexColor("#333333")
_MUTED = colors.HexColor("#666666")

PREPARED_BY = "AI Patent Filing Assistant"


def _styles() -> dict:
    base = getSampleStyleSheet()
    body = base["BodyText"]
    return {
        "title": ParagraphStyle("t", parent=body, fontName="Helvetica-Bold",
                                fontSize=16, spaceAfter=2, leading=19),
        "sub": ParagraphStyle("s", parent=body, fontName="Helvetica",
                              fontSize=9, textColor=_MUTED, leading=12),
        "h": ParagraphStyle("h", parent=body, fontName="Helvetica-Bold",
                            fontSize=10, spaceBefore=12, spaceAfter=4, leading=13),
        "label": ParagraphStyle("l", parent=body, fontName="Helvetica",
                                fontSize=8.5, textColor=_MUTED, leading=11),
        "value": ParagraphStyle("v", parent=body, fontName="Helvetica-Bold",
                                fontSize=10.5, leading=13),
        "item": ParagraphStyle("i", parent=body, fontName="Helvetica",
                               fontSize=9.5, leading=13),
        "note": ParagraphStyle("n", parent=body, fontName="Helvetica-Oblique",
                               fontSize=8, textColor=_MUTED, leading=10),
    }


def _esc(text) -> str:
    return (str(text if text is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _doc(buffer, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=_MARGIN, rightMargin=_MARGIN,
        topMargin=_MARGIN, bottomMargin=_MARGIN, title=title,
        author="", subject="", creator="",
    )


def _format_date(value: Optional[date]) -> str:
    return (value or date.today()).strftime("%d %B %Y")


def _pairs_table(pairs: list, st: dict, width: float) -> Table:
    """Two-column label/value block, used for the summary's facts."""
    rows = [[Paragraph(_esc(k), st["label"]), Paragraph(_esc(v), st["value"])]
            for k, v in pairs]
    table = Table(rows, colWidths=[width * 0.38, width * 0.62])
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#DDDDDD")),
    ]))
    return table


def build_filing_summary_pdf(
    definition: dict,
    counts: Optional[dict] = None,
    documents: Optional[list] = None,
    generated_on: Optional[date] = None,
) -> bytes:
    """One-page record of the prepared filing.

    Args:
        definition: the form definition.
        counts:     {'autoFilled', 'edited', 'missing'} as the review computed
                    them — the same numbers the user saw on screen.
        documents:  friendly names of the source documents used, e.g.
                    ['Complete Specification', 'Patent Certificate'].
    """
    counts = counts or {}
    documents = documents or []
    missing = int(counts.get("missing") or 0)

    st = _styles()
    buffer = io.BytesIO()
    doc = _doc(buffer, "Patent Filing Summary")
    width = A4[0] - 2 * _MARGIN

    story = [
        Paragraph("Patent Filing Summary", st["title"]),
        Paragraph("Prepared " + _format_date(generated_on), st["sub"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=_RULE),
        Paragraph("Prepared form", st["h"]),
        _pairs_table([
            ("Form", "Form %s" % definition.get("formNumber", "")),
            ("Title", definition.get("officialName", "")),
            ("Generated", _format_date(generated_on)),
        ], st, width),
        Paragraph("Documents used", st["h"]),
    ]

    if documents:
        for name in documents:
            # ZapfDingbats '3' is a check mark and is one of the 14 PDF core
            # fonts, so it prints on any viewer without embedding a font.
            story.append(Paragraph(
                '<font name="ZapfDingbats">3</font>  ' + _esc(name), st["item"]))
    else:
        story.append(Paragraph("No source documents were used for this form.", st["item"]))

    story.append(Paragraph("Completion", st["h"]))
    story.append(_pairs_table([
        ("Automatically filled", str(int(counts.get("autoFilled") or 0))),
        ("Edited by user", str(int(counts.get("edited") or 0))),
        ("Missing", str(missing)),
    ], st, width))

    story.append(Paragraph("Status", st["h"]))
    status = "Ready for Filing" if missing == 0 else "Incomplete - %d field%s still required" % (
        missing, "" if missing == 1 else "s")
    story.append(Paragraph(_esc(status), st["value"]))
    story.append(Spacer(1, 10))
    story.append(_pairs_table([("Prepared by", PREPARED_BY)], st, width))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "This summary is a record of preparation. Verify every value against the "
        "source documents before filing.", st["note"]))

    doc.build(story)
    return buffer.getvalue()


def build_provenance_pdf(
    definition: dict,
    entries: Optional[list] = None,
    generated_on: Optional[date] = None,
) -> bytes:
    """The audit trail: where each automatically-filled value came from.

    Args:
        entries: [{'field': 'Applicant Name', 'source': 'Complete Specification',
                   'page': 2, 'value': 'ACME…', 'edited': False}]
                 Already-friendly names; this function adds no interpretation.
    """
    entries = entries or []
    st = _styles()
    buffer = io.BytesIO()
    doc = _doc(buffer, "Provenance Report")
    width = A4[0] - 2 * _MARGIN

    story = [
        Paragraph("Provenance Report", st["title"]),
        Paragraph("Form %s - %s" % (definition.get("formNumber", ""),
                                    definition.get("officialName", "")), st["sub"]),
        Paragraph("Prepared " + _format_date(generated_on), st["sub"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=_RULE),
        Spacer(1, 4),
        Paragraph("For audit only - not filed with the Patent Office. It records "
                  "where each automatically completed value was found.", st["note"]),
    ]

    if not entries:
        story.append(Spacer(1, 12))
        story.append(Paragraph("No values were completed automatically for this form.",
                               st["item"]))
        doc.build(story)
        return buffer.getvalue()

    head = [Paragraph("Field", st["label"]), Paragraph("Value", st["label"]),
            Paragraph("Source document", st["label"]), Paragraph("Page", st["label"])]
    rows = [head]
    for entry in entries:
        source = entry.get("source") or "-"
        if entry.get("edited"):
            source = "Edited by user (originally from %s)" % source
        page = entry.get("page")
        rows.append([
            Paragraph(_esc(entry.get("field")), st["item"]),
            Paragraph(_esc(entry.get("value")), st["item"]),
            Paragraph(_esc(source), st["item"]),
            Paragraph(_esc(page if page is not None else "-"), st["item"]),
        ])

    table = Table(rows, colWidths=[width * 0.26, width * 0.32, width * 0.32, width * 0.10],
                  repeatRows=1)
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, _RULE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(Spacer(1, 8))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
