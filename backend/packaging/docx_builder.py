"""The editable DOCX — for internal review and last-minute edits.

Deliberately NOT a pixel copy of the IPO form. Its job is to be easy to open,
read and change in Word: the same fields, in the same official section order,
with headings and grouping preserved, so an edit made here is obviously the same
field as on the filed PDF.

It reads the same definition walk as the PDF (packaging.layout), so the two
documents cannot disagree about what the form contains.
"""

from __future__ import annotations

import io
from typing import Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

from packaging.layout import ValueBook, printed_header, walk_section

_BLANK = "—"  # em dash: an entry left for the Patent Office or for signing
_MUTED = RGBColor(0x60, 0x60, 0x60)


def _header(document, definition: dict) -> None:
    header = printed_header(definition)
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(header["formTitle"])
    run.bold = True
    run.font.size = Pt(16)

    for text, size, italic in (
        (header.get("statute", ""), 9, False),
        (header.get("subject", ""), 11, False),
        (header.get("citation", ""), 8, True),
    ):
        if not text:
            continue
        para = document.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text)
        run.font.size = Pt(size)
        run.italic = italic
        if text == header.get("subject"):
            run.bold = True


def _labelled(document, label: str, text: str, indent: int = 0) -> None:
    """One entry: a muted label followed by the value in bold, on one line.

    Keeping label and value in a single paragraph is what makes the file easy to
    edit — the user clicks straight after the label and types.
    """
    para = document.add_paragraph()
    if indent:
        para.paragraph_format.left_indent = Pt(12 * indent)
    para.paragraph_format.space_after = Pt(2)
    if label:
        run = para.add_run(label + ": ")
        run.font.size = Pt(9)
        run.font.color.rgb = _MUTED
    value = para.add_run(text if text else _BLANK)
    value.bold = bool(text)
    value.font.size = Pt(10.5)


def _write_item(document, item: dict, indent: int = 0) -> None:
    kind = item["kind"]

    if kind == "boilerplate":
        para = document.add_paragraph()
        if indent:
            para.paragraph_format.left_indent = Pt(12 * indent)
        run = para.add_run(item["text"])
        run.font.size = Pt(9.5)
        return

    if kind == "value":
        _labelled(document, item["label"], item["text"], indent)
        return

    if kind == "list":
        if item["items"]:
            for entry in item["items"]:
                _labelled(document, item["label"], entry, indent)
        else:
            _labelled(document, item["label"], "", indent)
        return

    if kind == "signature":
        # The drawn signature is not carried into the editable copy: this file is
        # for editing, and the filed PDF is where a signature belongs.
        _labelled(document, item["label"], "(signed)" if item.get("image") else "", indent)
        return

    if kind == "table":
        columns = item["columns"]
        if not columns:
            return
        if item.get("label"):
            para = document.add_paragraph()
            run = para.add_run(item["label"])
            run.bold = True
            run.font.size = Pt(10)
        table = document.add_table(rows=1, cols=len(columns))
        table.style = "Table Grid"
        for cell, column in zip(table.rows[0].cells, columns):
            cell.text = column["label"]
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True
                    run.font.size = Pt(9)
        for row in item["rows"] or [{}]:
            cells = table.add_row().cells
            for cell, column in zip(cells, columns):
                cell.text = row.get(column["id"], "")
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(9)
        document.add_paragraph()
        return

    if kind == "group":
        multi = item.get("repeatable") and len(item["instances"]) > 1
        for index, instance in enumerate(item["instances"], 1):
            heading = item["label"] or ""
            if multi:
                heading = ("%s %d" % (heading, index)).strip()
            if heading:
                para = document.add_paragraph()
                if indent:
                    para.paragraph_format.left_indent = Pt(12 * indent)
                para.paragraph_format.space_before = Pt(6)
                run = para.add_run(heading)
                run.bold = True
                run.font.size = Pt(10)
            for child in instance:
                _write_item(document, child, indent + 1)


def build_form_docx(
    definition: dict,
    values: Optional[dict] = None,
    visible_paths: Optional[list] = None,
) -> bytes:
    """Render the editable Word copy of one completed form. Returns DOCX bytes."""
    book = ValueBook(values, visible_paths)
    document = Document()
    _header(document, definition)

    for section in definition.get("sections", []):
        items = list(walk_section(section, book))
        if not items:
            continue
        title = str(section.get("title") or "").strip()
        if title:
            document.add_heading(title, level=2)
        for item in items:
            _write_item(document, item)

    notes = definition.get("notes") or []
    if notes:
        document.add_heading("Notes", level=2)
        for note in notes:
            para = document.add_paragraph(note, style="List Bullet")
            for run in para.runs:
                run.font.size = Pt(9)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
