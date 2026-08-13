"""Generic autofill mapper — zero per-form logic.

resolve(field, profile) iterates autofill.sources[] in the authored order and
returns the first Fact it finds. It works for Form 13 the day its definition
exists, for the same reason the renderer does: it reads the definition rather
than knowing anything about any specific form.
"""

from __future__ import annotations

from typing import Any, Optional

from models.fact import Fact
from models.patent_profile import PatentProfile


class Suggestion:
    """A single field's suggested value and its provenance."""

    def __init__(self, value: Any, fact: Fact):
        self.value = value
        self.fact = fact

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "fact": self.fact.model_dump(),
        }


class AutofillMapper:
    """Maps a PatentProfile onto a form definition's fields.

    Produces a flat {field_path: Suggestion} dict the frontend can overlay on
    the renderer's initialValues. Contains no knowledge of any specific form.
    """

    def get_suggestions(
        self,
        definition: dict,
        profile: PatentProfile,
    ) -> dict[str, Suggestion]:
        """Walk the definition and produce suggestions for every autofillable field.

        Args:
            definition: Parsed form definition JSON.
            profile:    The workspace's merged PatentProfile.

        Returns:
            {dotted_field_path: Suggestion} — only fields that have a match.
        """
        suggestions: dict[str, Suggestion] = {}
        for section in definition.get("sections", []):
            self._walk_fields(
                section.get("fields", []),
                section["id"],
                profile,
                suggestions,
            )
        return suggestions

    def _walk_fields(
        self,
        fields: list[dict],
        base: str,
        profile: PatentProfile,
        suggestions: dict[str, Suggestion],
    ) -> None:
        for field in fields:
            path = f"{base}.{field['id']}"
            self._resolve_field(field, path, profile, suggestions)

            # Recurse into group/signatureBlock children
            if field.get("fields"):
                self._walk_fields(field["fields"], path, profile, suggestions)

            # Recurse into table column cells
            for col in field.get("columns", []):
                cell = col.get("cell", {})
                if cell.get("autofill"):
                    cell_path = f"{path}[].{col['id']}"
                    self._resolve_cell(cell, cell_path, profile, suggestions)

    def _resolve_field(
        self,
        field: dict,
        path: str,
        profile: PatentProfile,
        suggestions: dict[str, Suggestion],
    ) -> None:
        af = field.get("autofill")
        if not af or af.get("strategy") != "direct":
            return
        suggestion = self._find_first(af.get("sources", []), profile)
        if not suggestion:
            return
        # Repeatable scalar controls (e.g. a repeatable textarea) store their
        # value as an array in the renderer's state, one entry per instance —
        # a bare scalar at that path is invisible to it (form-renderer.js
        # repeatScalar() resets any non-array value to a blank single row).
        # Groups/signatureBlocks handle repetition differently (child paths,
        # not an array at their own path) and are excluded via `fields`.
        if field.get("repeatable") and not field.get("fields"):
            suggestion = Suggestion([suggestion.value], suggestion.fact)
        suggestions[path] = suggestion

    def _resolve_cell(
        self,
        cell: dict,
        path: str,
        profile: PatentProfile,
        suggestions: dict[str, Suggestion],
    ) -> None:
        af = cell.get("autofill")
        if not af or af.get("strategy") != "direct":
            return
        suggestion = self._find_first(af.get("sources", []), profile)
        if suggestion:
            suggestions[path] = suggestion

    @staticmethod
    def _find_first(
        sources: list[dict],
        profile: PatentProfile,
    ) -> Optional[Suggestion]:
        """Iterate sources[] in authored order; return the first match."""
        for src in sources:
            facts = profile.get_facts(
                key=src["key"],
                source_type=src.get("sourceType"),
            )
            if facts:
                return Suggestion(facts[0].value, facts[0])
        return None
