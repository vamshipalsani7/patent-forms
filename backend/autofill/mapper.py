"""Generic autofill mapper — zero per-form logic.

resolve() iterates `autofill.sources[]` in the authored order and returns the
facts it finds. It works for Form 13 the day its definition exists, for the same
reason the renderer does: it reads the definition rather than knowing anything
about any specific form.

THE SHAPE OF A SUGGESTION IS THE RENDERER'S STATE SHAPE
-------------------------------------------------------
There is no translation layer between this module and the form renderer.
`mainArea.flattenSuggestions()` copies `suggestion.value` directly into the
renderer's `initialValues` at `suggestion`'s key, so a path emitted here must be
exactly the path form-renderer.js reads, and the value exactly the shape it
expects. A near-miss is silent: the value lands in renderer state, nothing ever
reads it, and the field renders blank with no error anywhere.

The four shapes, taken from form-renderer.js:

  scalar field         state[path] = "value"
  repeatable scalar    state[path] = ["v1", "v2"]           (repeatScalar)
  table                state[path] = [{col: v}, {col: v}]   (tableControl)
  repeatable group     state[path + "#count"] = 2, and children at
                       state[path + ".0." + childId], state[path + ".1." + …]
                                                            (groupControl)

Non-repeatable groups nest their children at `path.childId` with no index.

CORRELATION ACROSS KEYS IS POSITIONAL
-------------------------------------
Row *i* of a table, and instance *i* of a repeatable group, are assembled by
taking the *i*-th fact of each contributing key. Facts carry no row identity —
`Fact` records which document and page a value came from, not which inventor it
belonged to — so nothing stronger than position is available. See
`_zip_by_position` for what that assumption does and does not guarantee.
"""

from __future__ import annotations

from typing import Any, Optional

from models.fact import Fact
from models.patent_profile import PatentProfile


class Suggestion:
    """A single field's suggested value and its provenance.

    `fact` is the primary provenance record and stays the first contributing
    fact, so existing readers (the provenance banner, the wire format) are
    unaffected. `facts` carries every contributing fact, which is what a
    repeatable field needs: five inventor names pre-filled from one document
    still have five separate page references behind them.
    """

    def __init__(
        self,
        value: Any,
        fact: Fact,
        facts: Optional[list[Fact]] = None,
        structural: bool = False,
    ):
        self.value = value
        self.fact = fact
        self.facts = list(facts) if facts else [fact]
        self.structural = structural
        """True for renderer bookkeeping rather than an extracted value — the
        instance count of a repeatable group. It has to travel on this channel
        because that is how state reaches the renderer, but it is not a
        suggestion the user should see listed as an auto-filled field."""

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "fact": self.fact.model_dump(),
            "facts": [f.model_dump() for f in self.facts],
            "structural": self.structural,
        }


class AutofillMapper:
    """Maps a PatentProfile onto a form definition's fields.

    Produces a flat {field_path: Suggestion} dict the frontend overlays on the
    renderer's initialValues. Contains no knowledge of any specific form.
    """

    def get_suggestions(
        self,
        definition: dict,
        profile: PatentProfile,
        overrides: Optional[dict[str, Any]] = None,
    ) -> dict[str, Suggestion]:
        """Walk the definition and produce suggestions for every autofillable field.

        Args:
            definition: Parsed form definition JSON.
            profile:    The workspace's merged PatentProfile.
            overrides:  The user's own decisions from the Patent Workspace, keyed
                        by vocabulary key: the chosen side of a conflict, or a
                        value typed for a field no document supplied. A decision
                        outranks the raw first-fact pick, so the form pre-fills
                        with what the user actually reviewed and settled on — not
                        a value they may have already rejected. When None or
                        empty, behaviour is exactly as before: facts only.

        Returns:
            {renderer_state_path: Suggestion} — only paths that have a match.
        """
        suggestions: dict[str, Suggestion] = {}
        for section in definition.get("sections", []):
            self._walk_fields(
                section.get("fields", []),
                section["id"],
                profile,
                suggestions,
                overrides or {},
            )
        return suggestions

    # ----------------------------------------------------------------- walking

    def _walk_fields(
        self,
        fields: list[dict],
        base: str,
        profile: PatentProfile,
        suggestions: dict[str, Suggestion],
        overrides: dict[str, Any],
    ) -> None:
        for field in fields:
            path = f"{base}.{field['id']}"

            # A table's data lives in its columns, not in `fields`, and its whole
            # value is one array at the table's own path.
            if field.get("kind") == "table":
                self._resolve_table(field, path, profile, suggestions)
                continue

            self._resolve_field(field, path, profile, suggestions, overrides)

            children = field.get("fields")
            if not children:
                continue

            if field.get("repeatable"):
                # Children are indexed per instance: path.0.child, path.1.child.
                self._resolve_repeatable_group(field, path, profile, suggestions, overrides)
            else:
                self._walk_fields(children, path, profile, suggestions, overrides)

    # --------------------------------------------------------------- resolving

    def _resolve_field(
        self,
        field: dict,
        path: str,
        profile: PatentProfile,
        suggestions: dict[str, Suggestion],
        overrides: dict[str, Any],
    ) -> None:
        af = field.get("autofill")
        if not af or af.get("strategy") != "direct":
            return

        repeatable_scalar = bool(field.get("repeatable")) and not field.get("fields")

        if repeatable_scalar:
            # Every matching fact becomes a row. The renderer holds an array at
            # this path and resets any non-array value to a single blank row, so
            # even a lone value must be wrapped. Overrides are single scalar
            # decisions with no row identity, so they do not apply here.
            facts = self._find_all(af.get("sources", []), profile)
            if not facts:
                return
            suggestions[path] = Suggestion(
                [f.value for f in facts], facts[0], facts=facts
            )
            return

        # Scalars, and repeatable groups' own autofill block: first fact only.
        # A group holds no value of its own in renderer state — this entry is
        # inert there — but it is preserved because it predates indexed group
        # resolution and something may read the provenance.
        facts = self._resolve_sources(af.get("sources", []), profile, overrides)
        if facts:
            suggestions[path] = Suggestion(facts[0].value, facts[0])

    def _resolve_repeatable_group(
        self,
        field: dict,
        path: str,
        profile: PatentProfile,
        suggestions: dict[str, Suggestion],
        overrides: dict[str, Any],
    ) -> None:
        """Fill every instance of a repeatable group, and set its instance count.

        Emits `path.i.childId` for each instance, plus a structural `path#count`
        so the renderer draws that many blocks. Without the count the renderer
        draws one block and instances 2..n sit unread in state.
        """
        per_child = self._collect_child_facts(field.get("fields", []), "", profile, overrides)
        if not per_child:
            return

        count = max(len(facts) for facts in per_child.values())

        for index in range(count):
            for relative_path, facts in per_child.items():
                if index < len(facts):
                    fact = facts[index]
                    suggestions[f"{path}.{index}.{relative_path}"] = Suggestion(
                        fact.value, fact
                    )

        anchor = next(iter(per_child.values()))[0]
        suggestions[f"{path}#count"] = Suggestion(count, anchor, structural=True)

    def _collect_child_facts(
        self,
        fields: list[dict],
        prefix: str,
        profile: PatentProfile,
        overrides: dict[str, Any],
    ) -> dict[str, list[Fact]]:
        """{relative child path: [Fact]} for one instance of a repeatable group.

        Descends through nested non-repeatable groups so a child at
        `applicant.address.line1` keeps its full relative path.

        A repeatable group nested inside another repeatable group is skipped: it
        would need two-dimensional indexing (path.i.child.j.leaf) and no
        definition in the library has one. `test_autofill_mapper` guards that
        assumption, so this becomes a visible failure rather than silent data
        loss if a definition ever introduces the shape.
        """
        collected: dict[str, list[Fact]] = {}
        for field in fields:
            relative = f"{prefix}{field['id']}"

            if field.get("kind") == "table":
                continue

            af = field.get("autofill")
            if af and af.get("strategy") == "direct" and not field.get("fields"):
                # A user's typed value for a child key (e.g. an applicant
                # nationality no document supplied) fills that leaf of the first
                # instance, alongside whatever facts fill its siblings.
                facts = self._resolve_sources(af.get("sources", []), profile, overrides)
                if facts:
                    collected[relative] = facts

            children = field.get("fields")
            if children and not field.get("repeatable"):
                collected.update(
                    self._collect_child_facts(children, f"{relative}.", profile, overrides)
                )
        return collected

    def _resolve_table(
        self,
        field: dict,
        path: str,
        profile: PatentProfile,
        suggestions: dict[str, Suggestion],
    ) -> None:
        """Build the table's whole row array as a single value at its own path.

        The renderer holds `[{colId: value}, …]` here and reads each cell out of
        the row object. It has no notion of a per-cell state path, so cells are
        never addressed individually.
        """
        per_column: dict[str, list[Fact]] = {}
        for column in field.get("columns", []):
            cell = column.get("cell", {})
            af = cell.get("autofill")
            if not af or af.get("strategy") != "direct":
                continue
            facts = self._find_all(af.get("sources", []), profile)
            if facts:
                per_column[column["id"]] = facts

        if not per_column:
            return

        rows, contributing = self._zip_by_position(per_column)
        suggestions[path] = Suggestion(rows, contributing[0], facts=contributing)

    @staticmethod
    def _zip_by_position(
        per_column: dict[str, list[Fact]],
    ) -> tuple[list[dict[str, Any]], list[Fact]]:
        """Assemble rows by taking the i-th fact of every column.

        This is the correlation assumption, stated plainly: the i-th country and
        the i-th application number are assumed to describe the same foreign
        application. Facts carry no row identity, so position is the only
        available join.

        It holds when the values came from one document in document order, which
        is how the extractors emit them. It does NOT hold when two columns were
        filled from different documents that happen to list their entries in
        different orders. Nothing here can detect that; every cell keeps its own
        provenance so a user reviewing the row can see the values came from
        different places.

        Columns of unequal length produce short rows rather than padded ones —
        a genuinely unknown cell stays blank instead of borrowing a neighbour's.
        """
        count = max(len(facts) for facts in per_column.values())
        rows: list[dict[str, Any]] = []
        contributing: list[Fact] = []
        for index in range(count):
            row: dict[str, Any] = {}
            for column_id, facts in per_column.items():
                if index < len(facts):
                    row[column_id] = facts[index].value
                    contributing.append(facts[index])
            rows.append(row)
        return rows, contributing

    # ------------------------------------------------------------------ lookup

    def _resolve_sources(
        self,
        sources: list[dict],
        profile: PatentProfile,
        overrides: dict[str, Any],
    ) -> list[Fact]:
        """Like `_find_all`, but a user decision on a cited key wins.

        Walks the sources in authored order (the same preference order
        `_find_all` respects) and, for each source, resolves it one of two ways:

          * If the user has decided the source's key in the Patent Workspace,
            that decision is used. When the decided value is one a document
            actually supplied — a resolved conflict — the real Fact is returned
            so its provenance survives; when it is a value the user typed for a
            field no document had, a `method="manual"` Fact stands in.
          * Otherwise the source falls back to its extracted facts.

        The first source that yields anything wins, so an override at a more-
        preferred source outranks facts at a less-preferred one, exactly as a
        fact there would have. With no overrides this reduces to `_find_all`.
        """
        if not overrides:
            return self._find_all(sources, profile)

        for source in sources:
            key = source.get("key")
            if key in overrides:
                value = overrides[key]
                for fact in profile.get_facts(key=key):
                    if str(fact.value) == str(value):
                        return [fact]
                return [self._user_fact(key, value)]
            facts = self._find_all([source], profile)
            if facts:
                return facts
        return []

    @staticmethod
    def _user_fact(key: str, value: Any) -> Fact:
        """A Fact standing for a value the user entered themselves.

        `method='manual'` and `source_type='user'` are how the rest of the
        system tells a user's own value apart from an extracted one — the form's
        provenance banner reads it as "Entered by you" rather than naming a
        document. Full confidence: it is not a guess, it is the user's answer.
        """
        return Fact(
            key=key,
            value=value,
            document_id="user",
            source_type="user",
            page=None,
            confidence=1.0,
            method="manual",
            extractor_version="user@1",
        )

    @staticmethod
    def _find_all(
        sources: list[dict],
        profile: PatentProfile,
    ) -> list[Fact]:
        """Every fact from the FIRST source in authored order that yields any.

        Results are not concatenated across sources. Authored order expresses
        preference between documents, so a specification that lists two
        inventors must not be merged with a Form 5 that lists three — that would
        produce five inventors, none of them wrong individually and the set
        entirely wrong.

        Ordering within the chosen source is whatever `get_facts()` returns:
        confidence descending, and stable, so facts extracted at equal
        confidence keep document order. Multi-value keys are emitted at one
        confidence by every extractor in the library, so in practice repeated
        values arrive in the order the document printed them. That is a property
        of the current extractors, not a guarantee of the model.

        Exact duplicate values within a source are collapsed, keeping the
        highest-confidence occurrence. Two uploads of the same Form 1 otherwise
        yield the same applicant twice.
        """
        for source in sources:
            facts = profile.get_facts(
                key=source["key"],
                source_type=source.get("sourceType"),
            )
            if not facts:
                continue
            unique: list[Fact] = []
            seen: set[str] = set()
            for fact in facts:
                marker = str(fact.value)
                if marker in seen:
                    continue
                seen.add(marker)
                unique.append(fact)
            return unique
        return []

    @classmethod
    def _find_first(
        cls,
        sources: list[dict],
        profile: PatentProfile,
    ) -> Optional[Suggestion]:
        """First matching fact as a Suggestion. Retained for callers outside
        this module; the resolvers above use _find_all directly."""
        facts = cls._find_all(sources, profile)
        return Suggestion(facts[0].value, facts[0]) if facts else None
