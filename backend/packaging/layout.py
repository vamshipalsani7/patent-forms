"""Shared reading of a form definition for document generation.

The PDF and the DOCX must contain the same fields, in the same order, with the
same values — differing only in how they are laid out. That shared understanding
lives here, so neither generator re-derives it and the two can never drift.

Nothing in this module knows about reportlab or python-docx: it walks a form
definition and yields plain, already-resolved items ("a heading", "a labelled
value", "a table with these rows"), which each generator then draws in its own
way.
"""

from __future__ import annotations

import re
from typing import Any, Iterator, Optional

# A section the Patent Office completes, not the applicant. Its fields are
# printed as empty ruled lines on the filed document, whatever the editor holds.
_OFFICE_SECTION = re.compile(r"office\s*use|for\s*office", re.I)


def is_office_section(section: dict) -> bool:
    """True for a 'FOR OFFICE USE ONLY' block.

    Deliberately narrow: a title merely mentioning the office (Form 1's
    "APPLICANT'S REFERENCE / IDENTIFICATION NO. (AS ALLOTTED BY OFFICE)") is
    completed by the applicant and must still print its value.
    """
    title = section.get("title") or ""
    if _OFFICE_SECTION.search(title):
        return True
    return str(section.get("id", "")).lower().startswith("office_use")


def normalise_path(path: str) -> str:
    """Strip repeatable-instance indices: 'a.b.0.c' -> 'a.b.c'."""
    return re.sub(r"\.\d+(?=\.|$)", "", path)


class ValueBook:
    """The editor's values, with the lookups the generators need.

    `visible_paths`, when supplied, is the set of field paths the renderer
    actually drew for the user — conditional fields whose condition was not met
    are absent. Honouring it is what keeps the filed document identical to the
    form the user reviewed and compared, without this module re-implementing the
    renderer's condition logic.
    """

    def __init__(
        self,
        values: Optional[dict] = None,
        visible_paths: Optional[list] = None,
    ) -> None:
        self.values = values or {}
        self._visible = None
        if visible_paths:
            self._visible = {normalise_path(p) for p in visible_paths}

    def get(self, path: str) -> Any:
        return self.values.get(path)

    def text(self, path: str) -> str:
        """A field's value as printable text ('' when empty)."""
        return _as_text(self.values.get(path))

    def is_visible(self, path: str) -> bool:
        if self._visible is None:
            return True
        return normalise_path(path) in self._visible

    def instance_count(self, path: str) -> int:
        """How many instances a repeatable group has (renderer stores path#count)."""
        raw = self.values.get(path + "#count")
        try:
            count = int(raw)
        except (TypeError, ValueError):
            count = 1
        return max(1, count)

    def rows(self, path: str) -> list:
        """A table's rows: the renderer holds [{columnId: value}, ...]."""
        value = self.values.get(path)
        return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []

    def list_values(self, path: str) -> list:
        """A repeatable scalar's entries, blanks removed."""
        value = self.values.get(path)
        if isinstance(value, list):
            return [_as_text(v) for v in value if _as_text(v)]
        text = _as_text(value)
        return [text] if text else []


def _as_text(value: Any) -> str:
    """Render one stored value as plain text for a document.

    Booleans become the mark a paper form uses; a data URL (a drawn signature)
    is never printed as text — the generators handle it as an image.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else ""
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(", ".join(_as_text(v) for v in item.values() if _as_text(v)))
            else:
                parts.append(_as_text(item))
        return "; ".join(p for p in parts if p)
    text = str(value)
    if text.startswith("data:"):
        return ""
    return text.strip()


def option_label(field: dict, value: Any) -> str:
    """The human label of a chosen option, not its stored code."""
    text = _as_text(value)
    if not text:
        return ""
    for option in field.get("options", []) or []:
        if str(option.get("value")) == text:
            return str(option.get("label", option.get("value")))
    return text


def selected_labels(field: dict, value: Any) -> str:
    """Labels of every ticked option in a checkbox group."""
    if not isinstance(value, list):
        return option_label(field, value)
    labels = [option_label(field, v) for v in value]
    return ", ".join(l for l in labels if l)


def field_label(field: dict) -> str:
    return str(field.get("label") or field.get("id") or "").strip()


def walk_section(
    section: dict, book: ValueBook
) -> Iterator[dict]:
    """Yield printable items for one section, in official order.

    Item shapes (all values already resolved to text):
        {kind: 'boilerplate', text}
        {kind: 'value',   label, text, blank}       — a labelled entry
        {kind: 'list',    label, items}             — a repeatable scalar
        {kind: 'table',   label, columns, rows}     — columns/rows of text
        {kind: 'group',   label, instances:[[item]]}— a (repeatable) group
        {kind: 'signature', label, image}           — image is a data URL or None
    """
    office = is_office_section(section)
    for item in _walk_fields(section.get("fields", []), section["id"], book, office):
        yield item


def _walk_fields(fields: list, base: str, book: ValueBook, office: bool) -> Iterator[dict]:
    for field in fields:
        path = f"{base}.{field['id']}"
        if not book.is_visible(path):
            continue
        for item in _field_items(field, path, book, office):
            yield item


def _field_items(field: dict, path: str, book: ValueBook, office: bool) -> Iterator[dict]:
    kind = field.get("kind")
    label = field_label(field)

    if kind == "boilerplate":
        text = str(field.get("text") or "").strip()
        if text:
            yield {"kind": "boilerplate", "text": text}
        return

    if kind in ("signature", "signatureBlock") and not field.get("fields"):
        raw = book.get(path)
        image = raw if isinstance(raw, str) and raw.startswith("data:") and not office else None
        yield {"kind": "signature", "label": label or "Signature", "image": image}
        return

    if kind == "table":
        columns = [
            {"id": c["id"], "label": str(c.get("label") or c.get("id"))}
            for c in field.get("columns", []) or []
        ]
        rows = []
        if not office:
            for row in book.rows(path):
                rows.append({c["id"]: _as_text(row.get(c["id"])) for c in columns})
        yield {"kind": "table", "label": label, "columns": columns, "rows": rows}
        return

    if field.get("fields"):
        instances = []
        count = book.instance_count(path) if field.get("repeatable") else 1
        for index in range(count):
            inst_base = f"{path}.{index}" if field.get("repeatable") else path
            instances.append(list(_walk_fields(field["fields"], inst_base, book, office)))
        yield {"kind": "group", "label": label, "instances": instances,
               "repeatable": bool(field.get("repeatable"))}
        return

    if field.get("repeatable"):
        items = [] if office else book.list_values(path)
        yield {"kind": "list", "label": label, "items": items}
        return

    # Plain scalar — including discrete kinds, resolved to their option labels.
    if office:
        text = ""
    elif kind in ("radio", "dropdown", "strikeoutChoice"):
        text = option_label(field, book.get(path))
    elif kind == "checkboxGroup":
        text = selected_labels(field, book.get(path))
    elif kind == "checkbox":
        text = "Yes" if book.get(path) in (True, "true") else ""
    else:
        text = book.text(path)

    yield {"kind": "value", "label": label, "text": text, "blank": text == ""}


def printed_header(definition: dict) -> dict:
    """The official printed header block, exactly as it appears on the form.

    Definitions carry ``metadata.printedHeader`` transcribed from the government
    PDF; it is the authority for the filed document. Falls back to the
    machine-readable legalReference only if a definition lacks it.
    """
    header = (definition.get("metadata") or {}).get("printedHeader") or {}
    if header.get("formTitle"):
        return {
            "formTitle": header.get("formTitle", ""),
            "statute": header.get("statute", ""),
            "subject": header.get("subject", ""),
            "citation": header.get("citation", ""),
        }
    ref = definition.get("legalReference") or {}
    statute = "; ".join(ref.get("act", []) or [])
    rules = ref.get("rules", []) or []
    return {
        "formTitle": "FORM " + str(definition.get("formNumber", "")),
        "statute": (statute + (" and " + rules[0] if rules else "")).strip(),
        "subject": str(definition.get("officialName", "")).upper(),
        "citation": "; ".join(rules[1:]) if len(rules) > 1 else "",
    }
