"""Shared anchor-extraction engine.

Every extractor answers the same question — "which vocabulary keys can this
document type yield, and what printed text signals each one?" — so only the
answers differ. A subclass is therefore a declaration, not an implementation::

    class PatentCertificateExtractor(PatternExtractor):
        EXTRACTOR_VERSION = "patent_certificate@1"
        SOURCE_TYPE = "patent_certificate"
        PATTERNS = [("patent.number", [r"Patent\\s+No\\.?\\s*:?\\s*(\\d{4,9})"], 0.85)]

Tiers, highest trust first:
  1. AcroForm fields   0.90–0.95  label and value are structurally bound
  2. Region patterns   authored    anchors scoped to one part of the document
  3. Anchor patterns   authored    anchors matched against the whole document
  4. Aliases           reduced     one key restated as another, e.g. the
                                   patentee on a certificate is also the
                                   applicant of record

Scanned image-only PDFs yield nothing here; OCR remains a deferred Tier 5.

Two rules the engine enforces so subclasses cannot get them wrong:
  * A key found by a higher tier is never overwritten by a lower one.
  * `type: "date"` keys are normalised to ISO-8601, and a date that cannot be
    parsed is dropped rather than emitted raw — see normalize.normalize_date.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from extractors.normalize import clean_value, normalize_date
from models.fact import Fact

# Keys the registry declares as `type: "date"`. Values for these are run through
# normalize_date() before a Fact is built.
DATE_KEYS = frozenset({
    "application.filingDate",
    "patent.grantDate",
    "foreignApplications[].filingDate",
})

# Below this length a captured value is punctuation or a stray table rule.
_MIN_VALUE_LENGTH = 2


class PatternExtractor:
    """Declarative anchor extractor. Subclasses override the class attributes."""

    EXTRACTOR_VERSION = "base@0"
    SOURCE_TYPE = "generic"

    PATTERNS: list[tuple[str, list[str], float]] = []
    """(vocabulary_key, [regex, …], confidence), tried in order, first match wins.
    Each regex needs exactly one capture group holding the value."""

    REGIONS: dict[str, list[str]] = {}
    """region_name -> [anchor regexes]. A region runs from the end of its anchor
    to the start of the next region's anchor (or REGION_MAX_CHARS). Use this
    when the same label appears under several headings — a bare `NATIONALITY:`
    pattern would otherwise read the applicant's nationality as the inventor's."""

    REGION_PATTERNS: dict[str, list[tuple[str, list[str], float]]] = {}
    """region_name -> PATTERNS applied only inside that region."""

    REGION_MAX_CHARS = 1500
    """Cap on an unbounded trailing region, so the last one cannot swallow the
    rest of a 40-page specification."""

    ACROFORM_MAP: dict[str, tuple[str, float]] = {}
    """AcroForm field-name fragment -> (vocabulary_key, confidence). Matched as
    a case-insensitive substring, because field names vary between form versions."""

    MULTI_VALUE_KEYS: frozenset[str] = frozenset()
    """Keys where every match is kept rather than just the first — inventors and
    foreign applications are lists, and dropping all but one loses real data."""

    ALIASES: list[tuple[str, str, float]] = []
    """(source_key, alias_key, confidence). Restates an already-extracted value
    under a second key, and only if that key found nothing on its own. The
    reduced confidence records that this is an inference about the document
    rather than something the document printed."""

    # ------------------------------------------------------------------ public

    def extract_from_file(
        self,
        file_path: Union[str, Path],
        document_id: str,
        page_texts: list[tuple[int, str]],
    ) -> list[Fact]:
        """Return every fact extractable from this document.

        Args:
            file_path:   Path to the PDF on disk (needed for the AcroForm tier).
            document_id: The documentStore id from the frontend.
            page_texts:  [(page_number, text), …] from PDFReader.read_pages().
        """
        facts: list[Fact] = []
        found: set[str] = set()

        # Tier 1 — AcroForm
        for fact in self._extract_acroform(file_path, document_id):
            facts.append(fact)
            found.add(fact.key)

        full_text = "\n\n".join(text for _, text in page_texts)

        # Tier 2 — region-scoped patterns
        for region_name, patterns in self.REGION_PATTERNS.items():
            span = self._region_span(region_name, full_text)
            if span is None:
                continue
            start, end = span
            for fact in self._run_patterns(
                patterns, full_text[start:end], document_id, page_texts, offset=start
            ):
                if fact.key not in found or fact.key in self.MULTI_VALUE_KEYS:
                    facts.append(fact)
                    found.add(fact.key)

        # Tier 3 — whole-document patterns
        for fact in self._run_patterns(
            self.PATTERNS, full_text, document_id, page_texts, offset=0
        ):
            if fact.key not in found or fact.key in self.MULTI_VALUE_KEYS:
                facts.append(fact)
                found.add(fact.key)

        # Tier 4 — aliases
        facts.extend(self._apply_aliases(facts, found, document_id))

        return facts

    # ------------------------------------------------------------------- tiers

    def _extract_acroform(
        self, file_path: Union[str, Path], document_id: str
    ) -> list[Fact]:
        """Read values straight out of AcroForm fields (Tier 1)."""
        if not self.ACROFORM_MAP:
            return []
        try:
            import pdfplumber  # type: ignore
        except ImportError:
            return []

        facts: list[Fact] = []
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                form_data = self._read_acroform_fields(pdf)
                if not form_data:
                    return []
                for field_name, value in form_data.items():
                    if not value or not str(value).strip():
                        continue
                    for fragment, (key, confidence) in self.ACROFORM_MAP.items():
                        if fragment.lower() not in field_name.lower():
                            continue
                        fact = self._build_fact(
                            key, str(value), document_id, 1, confidence, "acroform"
                        )
                        if fact:
                            facts.append(fact)
                        break
        except Exception:  # noqa: BLE001 — pdfplumber is best-effort by design
            pass
        return facts

    @staticmethod
    def _read_acroform_fields(pdf: Any) -> dict[str, Any]:
        """Walk the AcroForm field tree and return {field_name: value}."""
        if not (hasattr(pdf, "doc") and hasattr(pdf.doc, "catalog")):
            return {}
        acro = pdf.doc.catalog.get("AcroForm")
        if not acro:
            return {}

        result: dict[str, Any] = {}
        for field_ref in acro.get("Fields", []):
            try:
                field = _deref(field_ref)
                name, value = field.get("T", ""), field.get("V", "")
                if name:
                    result[str(name)] = value
                for kid_ref in field.get("Kids", []):
                    kid = _deref(kid_ref)
                    kid_name, kid_value = kid.get("T", ""), kid.get("V", "")
                    if kid_name:
                        result[str(kid_name)] = kid_value
            except Exception:  # noqa: BLE001
                continue
        return result

    def _run_patterns(
        self,
        patterns: list[tuple[str, list[str], float]],
        text: str,
        document_id: str,
        page_texts: list[tuple[int, str]],
        offset: int,
    ) -> list[Fact]:
        """Match `patterns` against `text` (Tiers 2 and 3).

        `offset` maps a match back onto the full document so page numbers stay
        correct when the text is a region slice.
        """
        facts: list[Fact] = []
        for key, regexes, confidence in patterns:
            multi = key in self.MULTI_VALUE_KEYS
            seen: set[str] = set()
            for regex in regexes:
                matches = list(re.finditer(regex, text, re.IGNORECASE | re.DOTALL))
                if not matches:
                    continue
                for match in matches if multi else matches[:1]:
                    value = clean_value(match.group(1))
                    if len(value) < _MIN_VALUE_LENGTH or value.lower() in seen:
                        continue
                    page = self._find_page(offset + match.start(), page_texts)
                    fact = self._build_fact(
                        key, value, document_id, page, confidence, "anchor"
                    )
                    if fact:
                        seen.add(value.lower())
                        facts.append(fact)
                # A key is satisfied by the first regex that yields anything;
                # later regexes are fallbacks for other document layouts, not
                # additional sources.
                if seen:
                    break
        return facts

    def _apply_aliases(
        self, facts: list[Fact], found: set[str], document_id: str
    ) -> list[Fact]:
        """Restate values under a second key when that key found nothing (Tier 4)."""
        by_key = {f.key: f for f in facts}
        aliased: list[Fact] = []
        for source_key, alias_key, confidence in self.ALIASES:
            if alias_key in found or source_key not in by_key:
                continue
            origin = by_key[source_key]
            fact = self._build_fact(
                alias_key, str(origin.value), document_id,
                origin.page, confidence, "anchor",
            )
            if fact:
                aliased.append(fact)
                found.add(alias_key)
        return aliased

    # ------------------------------------------------------------------ helpers

    def _build_fact(
        self,
        key: str,
        raw_value: str,
        document_id: str,
        page: Optional[int],
        confidence: float,
        method: str,
    ) -> Optional[Fact]:
        """Build one Fact, or None if the value fails its key's type contract."""
        value = clean_value(raw_value)
        if len(value) < _MIN_VALUE_LENGTH:
            return None

        if key in DATE_KEYS:
            iso = normalize_date(value)
            if iso is None:
                # Better no suggestion than an unparseable date on a filing.
                return None
            value = iso

        return Fact(
            key=key,
            value=value,
            document_id=document_id,
            source_type=self.SOURCE_TYPE,
            page=page,
            confidence=confidence,
            method=method,
            extractor_version=self.EXTRACTOR_VERSION,
        )

    def _region_span(self, region_name: str, text: str) -> Optional[tuple[int, int]]:
        """Return (start, end) of a named region, or None if its anchor is absent."""
        starts = self._region_starts(text)
        if region_name not in starts:
            return None
        start = starts[region_name]
        later = [pos for name, pos in starts.items() if pos > start]
        end = min(later) if later else len(text)
        return start, min(end, start + self.REGION_MAX_CHARS)

    def _region_starts(self, text: str) -> dict[str, int]:
        """First anchor offset for each declared region that appears in the text."""
        starts: dict[str, int] = {}
        for name, anchors in self.REGIONS.items():
            for anchor in anchors:
                match = re.search(anchor, text, re.IGNORECASE)
                if match:
                    starts[name] = match.end()
                    break
        return starts

    @staticmethod
    def _find_page(
        char_offset: int, page_texts: list[tuple[int, str]]
    ) -> Optional[int]:
        """Map a character offset in the concatenated text back to a page number."""
        running = 0
        for page_num, text in page_texts:
            running += len(text) + 2  # +2 for the "\n\n" page separator
            if char_offset < running:
                return page_num
        return None


def _deref(ref: Any) -> Any:
    """Resolve a PDF indirect reference if it is one."""
    return ref.get_object() if hasattr(ref, "get_object") else ref


def iter_extractors() -> Iterable[type[PatternExtractor]]:
    """Every concrete extractor class. Used by tests to check invariants."""
    return tuple(PatternExtractor.__subclasses__())
