"""The official IPO PDF — the document that is actually filed.

Laid out from the form definition, in the official section order, with the
printed header transcribed from the government form. Content flows naturally, so
a long form paginates as a long form does on paper; margins, alignment and
section order are preserved on print.

What deliberately does NOT appear: any provenance, confidence, review colour,
vocabulary key or other internal detail. A filed document must read as an IPO
form, not as a report about one. Fields the Patent Office completes print as
empty ruled lines, and a signature area stays blank unless the user actually
signed it.
"""

from __future__ import annotations

import base64
import io
import re
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from packaging.layout import ValueBook, printed_header, walk_section

_MARGIN = 18 * mm
_RULE = colors.HexColor("#333333")
_MUTED = colors.HexColor("#666666")


def _styles() -> dict:
    base = getSampleStyleSheet()
    body = base["BodyText"]
    return {
        "formTitle": ParagraphStyle(
            "formTitle", parent=body, fontName="Helvetica-Bold", fontSize=15,
            alignment=TA_CENTER, spaceAfter=3, leading=18),
        "statute": ParagraphStyle(
            "statute", parent=body, fontName="Helvetica", fontSize=8.5,
            alignment=TA_CENTER, leading=11),
        "subject": ParagraphStyle(
            "subject", parent=body, fontName="Helvetica-Bold", fontSize=10.5,
            alignment=TA_CENTER, spaceBefore=6, leading=13),
        "citation": ParagraphStyle(
            "citation", parent=body, fontName="Helvetica-Oblique", fontSize=8,
            alignment=TA_CENTER, textColor=_MUTED, leading=10),
        "section": ParagraphStyle(
            "section", parent=body, fontName="Helvetica-Bold", fontSize=9.5,
            spaceBefore=10, spaceAfter=4, leading=12),
        "label": ParagraphStyle(
            "label", parent=body, fontName="Helvetica", fontSize=8.5,
            textColor=_MUTED, leading=11),
        "value": ParagraphStyle(
            "value", parent=body, fontName="Helvetica-Bold", fontSize=9.5, leading=12),
        "boiler": ParagraphStyle(
            "boiler", parent=body, fontName="Helvetica", fontSize=9, leading=12,
            spaceBefore=3, spaceAfter=3),
        "groupLabel": ParagraphStyle(
            "groupLabel", parent=body, fontName="Helvetica-Bold", fontSize=9,
            spaceBefore=6, spaceAfter=2, leading=11),
        "note": ParagraphStyle(
            "note", parent=body, fontName="Helvetica", fontSize=8, leading=10,
            textColor=_MUTED),
        "cell": ParagraphStyle(
            "cell", parent=body, fontName="Helvetica", fontSize=8.5, leading=10.5),
        "cellHead": ParagraphStyle(
            "cellHead", parent=body, fontName="Helvetica-Bold", fontSize=8.5, leading=10.5),
    }


def _esc(text: str) -> str:
    """Escape for reportlab's mini-HTML paragraph markup."""
    return (str(text or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _value_row(label: str, text: str, st: dict, width: float) -> Table:
    """One labelled entry: label above, value (or a ruled blank) below.

    A blank prints as an underline, which is how a paper form invites an entry —
    and is what an office-use or unsigned field must look like when filed.
    """
    value_flow = (Paragraph(_esc(text), st["value"]) if text
                  else HRFlowable(width="100%", thickness=0.5, color=_RULE,
                                  spaceBefore=7, spaceAfter=1))
    table = Table([[Paragraph(_esc(label), st["label"])], [value_flow]],
                  colWidths=[width])
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _signature_flow(label: str, image: Optional[str], st: dict, width: float) -> list:
    """A signature area: the drawn signature if the user signed, else a blank rule."""
    flows = [Paragraph(_esc(label), st["label"])]
    drawn = None
    if image:
        try:
            header, _, payload = image.partition(",")
            if "base64" in header and payload:
                raw = base64.b64decode(payload)
                drawn = Image(io.BytesIO(raw), width=55 * mm, height=16 * mm)
                drawn.hAlign = "LEFT"
        except Exception:  # noqa: BLE001 — a corrupt signature must not stop a filing
            drawn = None
    if drawn is not None:
        flows.append(drawn)
    else:
        flows.append(HRFlowable(width="60%", thickness=0.5, color=_RULE,
                                spaceBefore=12, spaceAfter=2))
    return flows


def _table_flow(item: dict, st: dict, width: float) -> list:
    """A definition table, drawn as a real table with its official columns."""
    columns = item["columns"]
    if not columns:
        return []
    head = [Paragraph(_esc(c["label"]), st["cellHead"]) for c in columns]
    body = []
    for row in item["rows"]:
        body.append([Paragraph(_esc(row.get(c["id"], "")), st["cell"]) for c in columns])
    if not body:  # keep one empty row so the table reads as a form to complete
        body.append([Paragraph("", st["cell"]) for _ in columns])

    col_width = width / len(columns)
    table = Table([head] + body, colWidths=[col_width] * len(columns), repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, _RULE),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEFEF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    flows = []
    if item.get("label"):
        flows.append(Paragraph(_esc(item["label"]), st["groupLabel"]))
    flows.append(table)
    flows.append(Spacer(1, 4))
    return flows


def _item_flows(item: dict, st: dict, width: float, depth: int = 0) -> list:
    kind = item["kind"]
    if kind == "boilerplate":
        return [Paragraph(_esc(item["text"]), st["boiler"])]
    if kind == "value":
        return [_value_row(item["label"], item["text"], st, width)]
    if kind == "list":
        flows = [Paragraph(_esc(item["label"]), st["label"])]
        if item["items"]:
            for i, entry in enumerate(item["items"], 1):
                flows.append(Paragraph("%d. %s" % (i, _esc(entry)), st["value"]))
        else:
            flows.append(HRFlowable(width="100%", thickness=0.5, color=_RULE,
                                    spaceBefore=7, spaceAfter=1))
        flows.append(Spacer(1, 3))
        return flows
    if kind == "table":
        return _table_flow(item, st, width)
    if kind == "signature":
        return _signature_flow(item["label"], item.get("image"), st, width)
    if kind == "group":
        flows = []
        multi = item.get("repeatable") and len(item["instances"]) > 1
        for index, instance in enumerate(item["instances"], 1):
            heading = item["label"] or ""
            if multi:
                heading = ("%s %d" % (heading, index)).strip()
            if heading:
                flows.append(Paragraph(_esc(heading), st["groupLabel"]))
            for child in instance:
                flows.extend(_item_flows(child, st, width - 6, depth + 1))
        return flows
    return []


def _header_flows(definition: dict, st: dict) -> list:
    header = printed_header(definition)
    flows = [Paragraph(_esc(header["formTitle"]), st["formTitle"])]
    if header.get("statute"):
        flows.append(Paragraph(_esc(header["statute"]), st["statute"]))
    if header.get("subject"):
        flows.append(Paragraph(_esc(header["subject"]), st["subject"]))
    if header.get("citation"):
        flows.append(Paragraph(_esc(header["citation"]), st["citation"]))
    flows.append(Spacer(1, 4))
    flows.append(HRFlowable(width="100%", thickness=1, color=_RULE))
    return flows


def _footer(canvas, doc, form_number: str) -> None:
    """Page furniture only — a form number and page count, as a paper form carries.

    Nothing here identifies the software or the extraction: a filed document
    must not advertise how it was produced.
    """
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(_MUTED)
    canvas.drawString(_MARGIN, 10 * mm, "Form %s" % form_number)
    canvas.drawRightString(A4[0] - _MARGIN, 10 * mm, "Page %d" % doc.page)
    canvas.restoreState()


def build_form_pdf(
    definition: dict,
    values: Optional[dict] = None,
    visible_paths: Optional[list] = None,
) -> bytes:
    """Render the official IPO PDF for one completed form.

    Args:
        definition:    the form definition (the same one the renderer draws).
        values:        the editor's values, flat path -> value.
        visible_paths: field paths the renderer actually drew. Supplying it keeps
                       the filed document identical to the form the user
                       reviewed; omitting it prints every field.

    Returns:
        PDF bytes.
    """
    book = ValueBook(values, visible_paths)
    st = _styles()
    buffer = io.BytesIO()
    form_number = str(definition.get("formNumber", ""))

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=_MARGIN, rightMargin=_MARGIN,
        topMargin=_MARGIN, bottomMargin=_MARGIN + 6 * mm,
        title="Form %s - %s" % (form_number, definition.get("officialName", "")),
        author="", subject="", creator="",
    )
    width = A4[0] - 2 * _MARGIN

    story = _header_flows(definition, st)
    for section in definition.get("sections", []):
        items = list(walk_section(section, book))
        if not items:
            continue
        title = str(section.get("title") or "").strip()
        block = []
        if title:
            block.append(Paragraph(_esc(title), st["section"]))
        for item in items:
            block.extend(_item_flows(item, st, width))
        # Keep a short section whole; let a long one paginate naturally.
        story.extend(block if len(block) > 12 else [KeepTogether(block)])

    notes = definition.get("notes") or []
    if notes:
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.5, color=_RULE))
        story.append(Paragraph("Notes", st["section"]))
        for note in notes:
            story.append(Paragraph("&bull; " + _esc(note), st["note"]))

    render = lambda canvas, d: _footer(canvas, d, form_number)  # noqa: E731
    doc.build(story, onFirstPage=render, onLaterPages=render)
    return buffer.getvalue()
