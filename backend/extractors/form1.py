"""Form 1 anchor extractor — Application for Grant of Patent.

Extracts three vocabulary keys for the vertical slice proof:
  applicant.name       (Section 3A — Name in Full)
  application.number   (FOR OFFICE USE ONLY header)
  invention.title      (Section 5 — Title of the Invention)

Strategy:
  Tier 1 — AcroForm fields  (digitally completed PDF forms have these)
  Tier 2 — Anchor text patterns  (for printed/saved forms with a text layer)

Both tiers produce Facts with full provenance. Confidence differs:
  AcroForm:  0.95  (field label + value are structurally bound)
  Anchor:    0.80  (regex matched a printed label; alignment could drift)

This extractor will never fire for scanned/image-only PDFs — those require
OCR (Tier 4), which is out of scope for the vertical slice.

To add a new Form 1 field, add a pattern tuple to the relevant PATTERNS list.
To add an extractor for a different document type, copy this file, change the
anchor phrases and EXTRACTOR_VERSION, and register it in profile_builder.py.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Union

from models.fact import Fact

EXTRACTOR_VERSION = "form1@1"
SOURCE_TYPE = "form1"


# ---------------------------------------------------------------------------
# Pattern sets for anchor-based extraction.
#
# Each entry is (vocabulary_key, [regex_patterns], confidence).
# Patterns are tried in order; the first match wins.
# A pattern must have a single capture group containing the value.
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, list[str], float]] = [
    (
        "application.number",
        [
            # "Application No. : 202211012345"  or  "Application No: 1234/DEL/2015"
            r"Application\s+No\.?\s*:?\s*([0-9]{1,6}/[A-Za-z]{2,5}/[0-9]{4})",
            r"Application\s+No\.?\s*:?\s*([0-9]{9,12})",
        ],
        0.80,
    ),
    (
        "invention.title",
        [
            # Section 5 header followed by the title on the next line(s)
            r"5\.\s*TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*[\n\r]+([^\n\r]{5,200})",
            r"TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*[\n\r]+([^\n\r]{5,200})",
            # Some PDFs put the title on the same line after a colon
            r"TITLE\s+OF\s+(?:THE\s+)?INVENTION\s*:\s*([^\n\r]{5,200})",
        ],
        0.80,
    ),
    (
        "applicant.name",
        [
            # "Name in Full" label followed by name on the next line
            r"Name\s+in\s+Full\s*[\n\r]+([^\n\r|]{3,100})",
            # Table-cell variant: "Name in Full | <name> |"
            r"Name\s+in\s+Full\s*\|?\s*([^|\n\r]{3,100})",
            # "3A. APPLICANT(S)" section header → next non-empty line
            r"3A\.\s*APPLICANT\(S\)\s*[\n\r]+(?:[^\n\r]*[\n\r]+)?([^\n\r]{3,100})",
        ],
        0.80,
    ),
    (
        "signatory.name",
        [
            # "Name" after "Signature" at the bottom of Form 1
            r"(?:Signature.*?[\n\r]+)Name\s*:?\s*([^\n\r]{3,100})",
            # Simple Name field at the end
            r"Name\s+of\s+(?:the\s+)?(?:applicant|signatory)\s*:?\s*([^\n\r]{3,100})",
        ],
        0.75,
    ),
]


# ---------------------------------------------------------------------------
# AcroForm field name → vocabulary key mapping.
# These are common AcroForm field names found in digitally-completed IPO forms.
# Names vary by form version; include aliases.
# ---------------------------------------------------------------------------

_ACROFORM_MAP: dict[str, tuple[str, float]] = {
    "ApplicationNo":    ("application.number",  0.95),
    "Application No":   ("application.number",  0.95),
    "TitleOfInvention": ("invention.title",      0.95),
    "Title":            ("invention.title",      0.90),
    "ApplicantName":    ("applicant.name",       0.95),
    "NameinFull":       ("applicant.name",       0.95),
    "Name in Full":     ("applicant.name",       0.95),
    "SignatoryName":    ("signatory.name",        0.90),
}


class Form1Extractor:
    """Extracts structured facts from a Form 1 PDF."""

    # Exposed as a class attribute so profile_builder's
    # getattr(extractor, "EXTRACTOR_VERSION", ...) can read it off the instance.
    EXTRACTOR_VERSION = EXTRACTOR_VERSION

    def extract_from_file(
        self,
        file_path: Union[str, Path],
        document_id: str,
        page_texts: list[tuple[int, str]],
    ) -> list[Fact]:
        """Return all facts extractable from this Form 1 PDF.

        Args:
            file_path:   Path to the PDF on disk (needed for AcroForm).
            document_id: The documentStore id from the frontend.
            page_texts:  [(page_number, text), …] from PDFReader.read_pages().
        """
        facts: list[Fact] = []

        # Tier 1: AcroForm fields (digitally completed forms)
        acroform_facts = self._extract_acroform(file_path, document_id)
        facts.extend(acroform_facts)

        # Track which keys AcroForm already found — anchor is a fallback only
        acroform_keys = {f.key for f in acroform_facts}

        # Tier 2: Anchor pattern matching across all pages
        full_text = "\n\n".join(text for _, text in page_texts)
        anchor_facts = self._extract_anchors(full_text, document_id, page_texts)
        for fact in anchor_facts:
            if fact.key not in acroform_keys:
                facts.append(fact)

        return facts

    # ------------------------------------------------------------------ tiers

    def _extract_acroform(
        self, file_path: Union[str, Path], document_id: str
    ) -> list[Fact]:
        """Extract values from AcroForm fields (Tier 1)."""
        try:
            import pdfplumber  # type: ignore
        except ImportError:
            return []

        facts: list[Fact] = []
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                form_data: Optional[dict[str, Any]] = None
                if hasattr(pdf, "doc") and hasattr(pdf.doc, "catalog"):
                    acro = pdf.doc.catalog.get("AcroForm")
                    if acro:
                        form_data = self._read_acroform_fields(acro)
                if not form_data:
                    return []
                for field_name, value in form_data.items():
                    if not value or not str(value).strip():
                        continue
                    for map_key, (vocab_key, confidence) in _ACROFORM_MAP.items():
                        if map_key.lower() in field_name.lower():
                            facts.append(Fact(
                                key=vocab_key,
                                value=str(value).strip(),
                                document_id=document_id,
                                source_type=SOURCE_TYPE,
                                page=1,
                                confidence=confidence,
                                method="acroform",
                                extractor_version=EXTRACTOR_VERSION,
                            ))
                            break
        except Exception:  # noqa: BLE001 — pdfplumber is best-effort
            pass
        return facts

    @staticmethod
    def _read_acroform_fields(acro: Any) -> dict[str, Any]:
        """Walk AcroForm field tree and return {field_name: value}."""
        result: dict[str, Any] = {}
        fields = acro.get("Fields", [])
        for field_ref in fields:
            try:
                field = field_ref.get_object() if hasattr(field_ref, "get_object") else field_ref
                name = field.get("T", "")
                value = field.get("V", "")
                if name:
                    result[str(name)] = value
                kids = field.get("Kids", [])
                for kid_ref in kids:
                    kid = kid_ref.get_object() if hasattr(kid_ref, "get_object") else kid_ref
                    kid_name = kid.get("T", "")
                    kid_value = kid.get("V", "")
                    if kid_name:
                        result[str(kid_name)] = kid_value
            except Exception:  # noqa: BLE001
                continue
        return result

    def _extract_anchors(
        self,
        full_text: str,
        document_id: str,
        page_texts: list[tuple[int, str]],
    ) -> list[Fact]:
        """Run anchor patterns against the full text (Tier 2)."""
        facts: list[Fact] = []
        for vocab_key, patterns, confidence in _PATTERNS:
            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    # Clean up common PDF artefacts
                    value = re.sub(r"\s{2,}", " ", value)
                    value = value.strip(" |,\t")
                    if not value or len(value) < 2:
                        continue
                    # Find which page the match landed on
                    page = self._find_page(match.start(), page_texts)
                    facts.append(Fact(
                        key=vocab_key,
                        value=value,
                        document_id=document_id,
                        source_type=SOURCE_TYPE,
                        page=page,
                        confidence=confidence,
                        method="anchor",
                        extractor_version=EXTRACTOR_VERSION,
                    ))
                    break  # first matching pattern wins for this key
        return facts

    @staticmethod
    def _find_page(char_offset: int, page_texts: list[tuple[int, str]]) -> Optional[int]:
        """Map a character offset in the concatenated text to a page number."""
        running = 0
        for page_num, text in page_texts:
            running += len(text) + 2  # +2 for the "\n\n" separator
            if char_offset < running:
                return page_num
        return None
