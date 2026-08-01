"""Specialised, per-document-type field extractors.

Each extractor consumes an uploaded PDF and produces a list of
:class:`models.fact.Fact` — the extracted values, each carrying full provenance
— which :class:`extractor.profile_builder.ProfileBuilder` wraps in a
DocumentExtract. Extractors are selected by the document type detected by
:class:`extractor.classifier.DocumentClassifier`.

The contract is :class:`extractors.base.PatternExtractor`. Subclasses declare
patterns; they do not implement extraction. The shared engine handles the
AcroForm tier, region scoping, page attribution, date normalisation and tier
precedence — see base.py.

To add support for a new document type:
    1. Add a value to :class:`models.patent_profile.DocumentType`, and a
       matching sourceType in vocabulary/registry.json. The linter's
       UNREACHABLE_SOURCE_TYPE / UNSPENDABLE_DOCUMENT_TYPE rules enforce that
       these two stay in step; skipping either makes the extractor unreachable.
    2. Add classifier anchors for it in extractor/classifier.py. Anchor ORDER
       matters — read the note at the top of that file first.
    3. Subclass PatternExtractor here, declaring PATTERNS (and REGIONS, if the
       document repeats the same labels under several headings).
    4. Register it in profile_builder._EXTRACTOR_REGISTRY.

Before starting, check the demand: an extractor is justified by the number of
`autofill.sources[]` entries across docs/specifications/definitions/ that cite
its sourceType. A source no definition references feeds no field, however well
it extracts. See docs/backlog.md for the types deferred on exactly that basis.
"""

from __future__ import annotations

from extractors.base import PatternExtractor

__all__ = ["PatternExtractor"]
