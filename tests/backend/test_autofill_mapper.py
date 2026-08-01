"""Autofill mapper — generic definition→suggestion resolution.

The mapper's defining property is that it contains no per-form logic: it reads
`autofill.sources[]` out of whatever definition it is handed. Most of these
tests therefore run against synthetic definitions the mapper has never seen,
which is the whole point — Form 13 must work the day its definition is authored,
with zero mapping code.
"""

from __future__ import annotations

import unittest

import context  # noqa: F401  — sets sys.path

from autofill.mapper import AutofillMapper, Suggestion
from models.document_extract import DocumentExtract
from models.fact import Fact
from models.patent_profile import PatentProfile


def _fact(key, value, source_type="form1", confidence=0.8, document_id="doc_1"):
    return Fact(
        key=key,
        value=value,
        document_id=document_id,
        source_type=source_type,
        page=1,
        confidence=confidence,
        method="anchor",
        extractor_version="form1@1",
    )


def _profile(*facts, document_id="doc_1", source_type="form1"):
    return PatentProfile(extracts=[
        DocumentExtract(
            document_id=document_id,
            source_type=source_type,
            original_filename="sample.pdf",
            page_count=1,
            facts=list(facts),
            extractor_version="form1@1",
        )
    ])


def _definition(fields, section_id="sec"):
    return {"sections": [{"id": section_id, "fields": fields}]}


def _direct(sources):
    return {"strategy": "direct", "sources": sources}


class TestSourcePreferenceOrder(unittest.TestCase):
    """Resolution order is authored data, not engine policy."""

    def setUp(self):
        self.mapper = AutofillMapper()
        self.definition = _definition([
            {
                "id": "name",
                "kind": "text",
                "autofill": _direct([
                    {"sourceType": "form1", "key": "applicant.name"},
                    {"sourceType": "patent_certificate", "key": "applicant.name"},
                ]),
            }
        ])

    def test_prefers_the_first_authored_source(self):
        profile = PatentProfile(extracts=[
            DocumentExtract(
                document_id="d1", source_type="form1", original_filename="a.pdf",
                facts=[_fact("applicant.name", "From Form 1", source_type="form1")],
                extractor_version="form1@1",
            ),
            DocumentExtract(
                document_id="d2", source_type="patent_certificate", original_filename="b.pdf",
                facts=[_fact("applicant.name", "From Certificate",
                             source_type="patent_certificate", confidence=0.99)],
                extractor_version="cert@1",
            ),
        ])
        result = self.mapper.get_suggestions(self.definition, profile)
        self.assertEqual("From Form 1", result["sec.name"].value)

    def test_authored_order_beats_higher_confidence(self):
        """A later source with better confidence must not jump the queue."""
        profile = PatentProfile(extracts=[
            DocumentExtract(
                document_id="d1", source_type="form1", original_filename="a.pdf",
                facts=[_fact("applicant.name", "Low confidence, first choice",
                             source_type="form1", confidence=0.51)],
                extractor_version="form1@1",
            ),
            DocumentExtract(
                document_id="d2", source_type="patent_certificate", original_filename="b.pdf",
                facts=[_fact("applicant.name", "High confidence, second choice",
                             source_type="patent_certificate", confidence=0.99)],
                extractor_version="cert@1",
            ),
        ])
        result = self.mapper.get_suggestions(self.definition, profile)
        self.assertEqual("Low confidence, first choice", result["sec.name"].value)

    def test_falls_through_to_the_next_source_when_the_first_is_absent(self):
        profile = _profile(
            _fact("applicant.name", "From Certificate", source_type="patent_certificate"),
            source_type="patent_certificate",
        )
        result = self.mapper.get_suggestions(self.definition, profile)
        self.assertEqual("From Certificate", result["sec.name"].value)


class TestNoMatchBehaviour(unittest.TestCase):
    def setUp(self):
        self.mapper = AutofillMapper()

    def test_field_is_absent_when_no_source_matches(self):
        definition = _definition([
            {"id": "name", "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])}
        ])
        result = self.mapper.get_suggestions(definition, _profile())
        self.assertNotIn("sec.name", result, "mapper invented a suggestion with no backing fact")

    def test_fields_without_autofill_are_ignored(self):
        definition = _definition([{"id": "manual_only", "kind": "text"}])
        self.assertEqual({}, self.mapper.get_suggestions(definition, _profile(
            _fact("applicant.name", "Acme")
        )))

    def test_derived_strategy_is_not_resolved(self):
        """Derived rules are natural language; v1 deliberately leaves them empty."""
        definition = _definition([
            {"id": "pronoun", "autofill": {"strategy": "derived",
                                           "rule": "Choose 'I' for one applicant, 'We' for many."}}
        ])
        result = self.mapper.get_suggestions(definition, _profile(_fact("applicant.name", "Acme")))
        self.assertEqual({}, result)

    def test_empty_profile_yields_no_suggestions(self):
        definition = _definition([
            {"id": "name", "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])}
        ])
        self.assertEqual({}, self.mapper.get_suggestions(definition, PatentProfile()))


class TestRepeatableFields(unittest.TestCase):
    """Repeatable scalars hold an array in renderer state, one entry per row.

    A bare scalar at that path is invisible to the renderer — form-renderer.js
    resets any non-array value to a single blank row — so the mapper wraps it.
    """

    def setUp(self):
        self.mapper = AutofillMapper()

    def test_repeatable_scalar_value_is_wrapped_in_a_list(self):
        definition = _definition([
            {
                "id": "applicants",
                "kind": "textarea",
                "repeatable": {"min": 1, "max": None, "itemLabel": "Applicant"},
                "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}]),
            }
        ])
        result = self.mapper.get_suggestions(definition, _profile(_fact("applicant.name", "Acme Ltd")))
        self.assertEqual(["Acme Ltd"], result["sec.applicants"].value)

    def test_non_repeatable_scalar_value_is_left_bare(self):
        definition = _definition([
            {"id": "number", "kind": "text",
             "autofill": _direct([{"sourceType": "form1", "key": "application.number"}])}
        ])
        result = self.mapper.get_suggestions(definition, _profile(_fact("application.number", "2022110")))
        self.assertEqual("2022110", result["sec.number"].value)

    def test_repeatable_group_is_not_wrapped(self):
        """Groups repeat via child paths, not an array at their own path."""
        definition = _definition([
            {
                "id": "block",
                "kind": "group",
                "repeatable": {"min": 1, "max": None, "itemLabel": "Block"},
                "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}]),
                "fields": [{"id": "child", "kind": "text"}],
            }
        ])
        result = self.mapper.get_suggestions(definition, _profile(_fact("applicant.name", "Acme Ltd")))
        self.assertEqual("Acme Ltd", result["sec.block"].value)

    def test_preserves_provenance_through_the_wrapping(self):
        definition = _definition([
            {"id": "applicants", "repeatable": {"min": 1},
             "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])}
        ])
        result = self.mapper.get_suggestions(definition, _profile(_fact("applicant.name", "Acme Ltd")))
        self.assertEqual("Acme Ltd", result["sec.applicants"].fact.value,
                         "the underlying Fact must keep the unwrapped value")


class TestNestedAndTabularFields(unittest.TestCase):
    def setUp(self):
        self.mapper = AutofillMapper()

    def test_resolves_fields_nested_inside_a_group(self):
        definition = _definition([
            {
                "id": "signature_block",
                "kind": "signatureBlock",
                "fields": [
                    {"id": "who", "autofill": _direct([{"sourceType": "form1", "key": "signatory.name"}])}
                ],
            }
        ])
        result = self.mapper.get_suggestions(definition, _profile(_fact("signatory.name", "R. Kumar")))
        self.assertEqual("R. Kumar", result["sec.signature_block.who"].value)

    def test_resolves_a_table_to_a_row_array_at_the_table_path(self):
        """The renderer holds `[{colId: value}, …]` at the table's own path.

        This previously emitted one suggestion per column at `path[].colId`.
        form-renderer.js `tableControl` has no per-cell state path — it reads
        each cell out of a row object — so those suggestions landed in renderer
        state, were never read, and every table rendered blank.
        """
        definition = _definition([
            {
                "id": "foreign_apps",
                "kind": "table",
                "columns": [
                    {"id": "country",
                     "cell": {"autofill": _direct([
                         {"sourceType": "priority_document", "key": "foreignApplications[].country"}])}},
                    {"id": "untouched", "cell": {}},
                ],
            }
        ])
        profile = _profile(
            _fact("foreignApplications[].country", "Germany", source_type="priority_document"),
            source_type="priority_document",
        )
        result = self.mapper.get_suggestions(definition, profile)

        self.assertEqual([{"country": "Germany"}], result["sec.foreign_apps"].value)
        self.assertNotIn("sec.foreign_apps[].country", result,
                         "the dead per-cell path must no longer be emitted")

    def test_a_column_with_no_autofill_stays_out_of_the_row(self):
        definition = _definition([
            {
                "id": "foreign_apps",
                "kind": "table",
                "columns": [
                    {"id": "country",
                     "cell": {"autofill": _direct([
                         {"sourceType": "priority_document", "key": "foreignApplications[].country"}])}},
                    {"id": "untouched", "cell": {}},
                ],
            }
        ])
        profile = _profile(
            _fact("foreignApplications[].country", "Germany", source_type="priority_document"),
            source_type="priority_document",
        )
        row = self.mapper.get_suggestions(definition, profile)["sec.foreign_apps"].value[0]
        self.assertNotIn("untouched", row)

    def test_a_table_with_no_matching_facts_yields_no_suggestion(self):
        definition = _definition([
            {"id": "foreign_apps", "kind": "table",
             "columns": [{"id": "country", "cell": {"autofill": _direct([
                 {"sourceType": "priority_document", "key": "foreignApplications[].country"}])}}]}
        ])
        self.assertEqual({}, self.mapper.get_suggestions(definition, _profile()))


def _repeatable_group(child_ids_to_keys, group_id="inventor"):
    """A repeatable group whose children autofill from the given keys."""
    return {
        "id": group_id,
        "kind": "group",
        "repeatable": {"min": 1, "max": None, "itemLabel": "Inventor"},
        "fields": [
            {"id": child_id, "kind": "text",
             "autofill": _direct([{"sourceType": "form1", "key": key}])}
            for child_id, key in child_ids_to_keys.items()
        ],
    }


class TestRepeatableGroupInstances(unittest.TestCase):
    """Repeatable groups index their children per instance: `path.i.childId`.

    Before this, the mapper emitted the un-indexed `path.childId`, which
    form-renderer.js `groupControl` never reads — it renders instance i at
    `path + "." + i`. Every repeatable group therefore rendered blank, not
    "first row only". Verified directly against the real renderer.
    """

    def setUp(self):
        self.mapper = AutofillMapper()
        self.definition = _definition([
            _repeatable_group({"name": "inventor.name", "nationality": "inventor.nationality"})
        ])

    def test_each_instance_gets_its_own_indexed_path(self):
        result = self.mapper.get_suggestions(self.definition, _profile(
            _fact("inventor.name", "RAJESH KUMAR"),
            _fact("inventor.name", "PRIYA SHARMA"),
        ))
        self.assertEqual("RAJESH KUMAR", result["sec.inventor.0.name"].value)
        self.assertEqual("PRIYA SHARMA", result["sec.inventor.1.name"].value)

    def test_the_unindexed_child_path_is_no_longer_emitted(self):
        result = self.mapper.get_suggestions(self.definition, _profile(
            _fact("inventor.name", "RAJESH KUMAR"),
        ))
        self.assertNotIn("sec.inventor.name", result,
                         "un-indexed child paths are invisible to the renderer")

    def test_instance_count_is_published_so_the_renderer_draws_every_block(self):
        """Without `#count` the renderer draws one block and instances 2..n sit
        unread in state — the values are present but the user cannot see them."""
        result = self.mapper.get_suggestions(self.definition, _profile(
            _fact("inventor.name", "RAJESH KUMAR"),
            _fact("inventor.name", "PRIYA SHARMA"),
            _fact("inventor.name", "AMIT PATEL"),
        ))
        self.assertEqual(3, result["sec.inventor#count"].value)

    def test_the_instance_count_is_marked_structural(self):
        """It is renderer bookkeeping, not an extracted value, and must not be
        listed to the user as an auto-filled field."""
        result = self.mapper.get_suggestions(self.definition, _profile(
            _fact("inventor.name", "RAJESH KUMAR"),
        ))
        self.assertTrue(result["sec.inventor#count"].structural)
        self.assertFalse(result["sec.inventor.0.name"].structural)

    def test_count_follows_the_longest_child_not_the_shortest(self):
        result = self.mapper.get_suggestions(self.definition, _profile(
            _fact("inventor.name", "RAJESH KUMAR"),
            _fact("inventor.name", "PRIYA SHARMA"),
            _fact("inventor.nationality", "Indian"),
        ))
        self.assertEqual(2, result["sec.inventor#count"].value)

    def test_a_child_with_fewer_facts_leaves_later_instances_blank(self):
        """Instance 2's nationality is genuinely unknown. It must stay empty
        rather than borrow instance 1's."""
        result = self.mapper.get_suggestions(self.definition, _profile(
            _fact("inventor.name", "RAJESH KUMAR"),
            _fact("inventor.name", "PRIYA SHARMA"),
            _fact("inventor.nationality", "Indian"),
        ))
        self.assertEqual("Indian", result["sec.inventor.0.nationality"].value)
        self.assertNotIn("sec.inventor.1.nationality", result)

    def test_a_group_with_no_matching_facts_yields_nothing_at_all(self):
        result = self.mapper.get_suggestions(self.definition, _profile())
        self.assertEqual({}, result)

    def test_children_of_a_nested_plain_group_keep_their_relative_path(self):
        definition = _definition([{
            "id": "applicant", "kind": "group",
            "repeatable": {"min": 1, "itemLabel": "Applicant"},
            "fields": [{
                "id": "address", "kind": "group",
                "fields": [{"id": "line1", "kind": "text",
                            "autofill": _direct([{"sourceType": "form1",
                                                  "key": "applicant.address"}])}],
            }],
        }])
        result = self.mapper.get_suggestions(definition, _profile(
            _fact("applicant.address", "12 MG Road"),
        ))
        self.assertEqual("12 MG Road", result["sec.applicant.0.address.line1"].value)

    def test_a_non_repeatable_group_still_nests_without_an_index(self):
        """Unchanged behaviour — the renderer uses `path.childId` for these."""
        definition = _definition([{
            "id": "block", "kind": "signatureBlock",
            "fields": [{"id": "who", "autofill": _direct([
                {"sourceType": "form1", "key": "signatory.name"}])}],
        }])
        result = self.mapper.get_suggestions(definition, _profile(
            _fact("signatory.name", "R. Kumar")))
        self.assertEqual("R. Kumar", result["sec.block.who"].value)


class TestTableRows(unittest.TestCase):
    def setUp(self):
        self.mapper = AutofillMapper()
        self.definition = _definition([{
            "id": "apps", "kind": "table",
            "columns": [
                {"id": "country", "cell": {"autofill": _direct([
                    {"sourceType": "priority_document", "key": "foreignApplications[].country"}])}},
                {"id": "number", "cell": {"autofill": _direct([
                    {"sourceType": "priority_document", "key": "foreignApplications[].number"}])}},
            ],
        }])

    def _profile_with(self, *facts):
        return _profile(*facts, source_type="priority_document")

    def test_builds_one_row_per_fact(self):
        result = self.mapper.get_suggestions(self.definition, self._profile_with(
            _fact("foreignApplications[].country", "Germany", source_type="priority_document"),
            _fact("foreignApplications[].country", "Japan", source_type="priority_document"),
            _fact("foreignApplications[].number", "DE123", source_type="priority_document"),
            _fact("foreignApplications[].number", "JP999", source_type="priority_document"),
        ))
        self.assertEqual(
            [{"country": "Germany", "number": "DE123"},
             {"country": "Japan", "number": "JP999"}],
            result["sec.apps"].value,
        )

    def test_a_short_column_leaves_that_cell_absent_rather_than_padded(self):
        result = self.mapper.get_suggestions(self.definition, self._profile_with(
            _fact("foreignApplications[].country", "Germany", source_type="priority_document"),
            _fact("foreignApplications[].country", "Japan", source_type="priority_document"),
            _fact("foreignApplications[].number", "DE123", source_type="priority_document"),
        ))
        rows = result["sec.apps"].value
        self.assertEqual({"country": "Germany", "number": "DE123"}, rows[0])
        self.assertEqual({"country": "Japan"}, rows[1])

    def test_every_contributing_cell_keeps_its_provenance(self):
        result = self.mapper.get_suggestions(self.definition, self._profile_with(
            _fact("foreignApplications[].country", "Germany", source_type="priority_document"),
            _fact("foreignApplications[].number", "DE123", source_type="priority_document"),
        ))
        facts = result["sec.apps"].facts
        self.assertEqual(2, len(facts))
        self.assertEqual({"Germany", "DE123"}, {f.value for f in facts})


class TestProvenanceForRepeatedValues(unittest.TestCase):
    """Every repeated value keeps its own Fact. A five-inventor pre-fill has
    five page references behind it, not one."""

    def setUp(self):
        self.mapper = AutofillMapper()

    def test_a_repeatable_scalar_carries_one_fact_per_value(self):
        definition = _definition([{
            "id": "names", "kind": "text",
            "repeatable": {"min": 1, "itemLabel": "Applicant"},
            "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}]),
        }])
        result = self.mapper.get_suggestions(definition, _profile(
            _fact("applicant.name", "Acme Ltd"),
            _fact("applicant.name", "Globex Corp"),
        ))
        suggestion = result["sec.names"]
        self.assertEqual(["Acme Ltd", "Globex Corp"], suggestion.value)
        self.assertEqual(["Acme Ltd", "Globex Corp"], [f.value for f in suggestion.facts])

    def test_the_primary_fact_stays_the_first_contributing_fact(self):
        """Backwards compatibility: readers of `.fact` predate `.facts`."""
        definition = _definition([{
            "id": "names", "repeatable": {"min": 1},
            "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}]),
        }])
        result = self.mapper.get_suggestions(definition, _profile(
            _fact("applicant.name", "Acme Ltd"),
            _fact("applicant.name", "Globex Corp"),
        ))
        self.assertEqual("Acme Ltd", result["sec.names"].fact.value)

    def test_each_group_instance_carries_the_fact_it_came_from(self):
        definition = _definition([_repeatable_group({"name": "inventor.name"})])
        result = self.mapper.get_suggestions(definition, _profile(
            _fact("inventor.name", "RAJESH KUMAR", confidence=0.9),
            _fact("inventor.name", "PRIYA SHARMA", confidence=0.9),
        ))
        self.assertEqual("RAJESH KUMAR", result["sec.inventor.0.name"].fact.value)
        self.assertEqual("PRIYA SHARMA", result["sec.inventor.1.name"].fact.value)


class TestSourceSelectionForRepeatedValues(unittest.TestCase):
    def setUp(self):
        self.mapper = AutofillMapper()
        self.definition = _definition([{
            "id": "names", "repeatable": {"min": 1},
            "autofill": _direct([
                {"sourceType": "form2_specification", "key": "inventor.name"},
                {"sourceType": "form5", "key": "inventor.name"},
            ]),
        }])

    def test_facts_are_not_concatenated_across_sources(self):
        """A spec listing two inventors and a Form 5 listing three must not
        produce five. Authored order picks one document, not a union."""
        profile = PatentProfile(extracts=[
            DocumentExtract(
                document_id="d1", source_type="form2_specification", original_filename="spec.pdf",
                facts=[_fact("inventor.name", "A", source_type="form2_specification"),
                       _fact("inventor.name", "B", source_type="form2_specification")],
                extractor_version="spec@1",
            ),
            DocumentExtract(
                document_id="d2", source_type="form5", original_filename="f5.pdf",
                facts=[_fact("inventor.name", "C", source_type="form5"),
                       _fact("inventor.name", "D", source_type="form5"),
                       _fact("inventor.name", "E", source_type="form5")],
                extractor_version="form5@1",
            ),
        ])
        self.assertEqual(["A", "B"], self.mapper.get_suggestions(self.definition, profile)["sec.names"].value)

    def test_falls_through_to_the_next_source_and_takes_all_of_it(self):
        profile = _profile(
            _fact("inventor.name", "C", source_type="form5"),
            _fact("inventor.name", "D", source_type="form5"),
            source_type="form5",
        )
        self.assertEqual(["C", "D"], self.mapper.get_suggestions(self.definition, profile)["sec.names"].value)

    def test_exact_duplicates_within_a_source_are_collapsed(self):
        """Two uploads of the same Form 1 otherwise list the applicant twice."""
        profile = _profile(
            _fact("inventor.name", "A", source_type="form2_specification", confidence=0.9),
            _fact("inventor.name", "A", source_type="form2_specification", confidence=0.7),
            _fact("inventor.name", "B", source_type="form2_specification"),
            source_type="form2_specification",
        )
        self.assertEqual(["A", "B"], self.mapper.get_suggestions(self.definition, profile)["sec.names"].value)

    def test_equal_confidence_values_keep_document_order(self):
        """Inventor order is legally meaningful; it must survive resolution."""
        profile = _profile(
            _fact("inventor.name", "FIRST", source_type="form2_specification", confidence=0.85),
            _fact("inventor.name", "SECOND", source_type="form2_specification", confidence=0.85),
            _fact("inventor.name", "THIRD", source_type="form2_specification", confidence=0.85),
            source_type="form2_specification",
        )
        self.assertEqual(["FIRST", "SECOND", "THIRD"],
                         self.mapper.get_suggestions(self.definition, profile)["sec.names"].value)


class TestDefinitionLibraryAssumptions(unittest.TestCase):
    """Guards the structural assumption the group resolver is built on."""

    def test_no_definition_nests_a_repeatable_inside_a_repeatable(self):
        """Two-dimensional indexing (path.i.child.j.leaf) is not implemented;
        `_collect_child_facts` skips such a child. No definition has one today,
        and this makes it a loud failure rather than silent data loss."""
        import json

        offenders = []
        for path in context.DEFINITIONS_DIR.rglob("*.definition.json"):
            definition = json.loads(path.read_text(encoding="utf-8"))

            def visit(fields, base, inside_repeatable):
                for field in fields:
                    here = f"{base}.{field['id']}"
                    repeatable = bool(field.get("repeatable"))
                    if repeatable and inside_repeatable:
                        offenders.append(f"{path.name}:{here}")
                    if field.get("fields"):
                        visit(field["fields"], here, inside_repeatable or repeatable)

            for section in definition.get("sections", []):
                visit(section.get("fields", []), section["id"], False)

        self.assertEqual([], offenders)


class TestGenericity(unittest.TestCase):
    """No per-form branching: an unseen definition resolves on its own terms."""

    def test_resolves_a_definition_the_mapper_has_never_seen(self):
        definition = {
            "formId": "form_99_invented",
            "sections": [
                {"id": "alpha", "fields": [
                    {"id": "one", "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])}
                ]},
                {"id": "beta", "fields": [
                    {"id": "two", "autofill": _direct([{"sourceType": "form1", "key": "application.number"}])}
                ]},
            ],
        }
        profile = _profile(
            _fact("applicant.name", "Acme Ltd"),
            _fact("application.number", "202211012345"),
        )
        result = AutofillMapper().get_suggestions(definition, profile)
        self.assertEqual("Acme Ltd", result["alpha.one"].value)
        self.assertEqual("202211012345", result["beta.two"].value)

    def test_handles_a_definition_with_no_sections(self):
        self.assertEqual({}, AutofillMapper().get_suggestions({}, _profile(_fact("applicant.name", "x"))))


class TestSuggestionSerialisation(unittest.TestCase):
    """to_dict() is the wire format the frontend consumes."""

    def test_carries_value_and_full_fact_provenance(self):
        payload = Suggestion("Acme Ltd", _fact("applicant.name", "Acme Ltd")).to_dict()

        self.assertEqual("Acme Ltd", payload["value"])
        fact = payload["fact"]
        for field in ("key", "value", "document_id", "source_type", "page",
                      "confidence", "method", "extractor_version", "extracted_at"):
            self.assertIn(field, fact, f"serialised fact is missing '{field}'")

    def test_a_single_fact_suggestion_still_reports_one_fact_in_the_list(self):
        payload = Suggestion("Acme Ltd", _fact("applicant.name", "Acme Ltd")).to_dict()
        self.assertEqual(1, len(payload["facts"]))
        self.assertEqual(payload["fact"], payload["facts"][0])

    def test_serialises_every_contributing_fact_for_a_repeated_value(self):
        facts = [_fact("inventor.name", "A"), _fact("inventor.name", "B")]
        payload = Suggestion(["A", "B"], facts[0], facts=facts).to_dict()

        self.assertEqual(["A", "B"], payload["value"])
        self.assertEqual(["A", "B"], [f["value"] for f in payload["facts"]])
        self.assertEqual("A", payload["fact"]["value"], "primary fact must stay the first")

    def test_the_wire_format_keeps_the_fields_the_frontend_already_reads(self):
        """mainArea.js reads `.value` and `.fact`; both must survive the
        addition of `.facts` and `.structural`."""
        payload = Suggestion("Acme Ltd", _fact("applicant.name", "Acme Ltd")).to_dict()
        self.assertIn("value", payload)
        self.assertIn("fact", payload)
        self.assertFalse(payload["structural"])


class TestMapperAgainstRealFormThree(unittest.TestCase):
    """The real definition, exercising the actual autofill blocks it ships with."""

    def setUp(self):
        import json
        self.definition = json.loads(
            (context.DEFINITIONS_DIR / "form_03.definition.json").read_text(encoding="utf-8")
        )
        self.profile = _profile(
            _fact("applicant.name", context.FIXTURE_APPLICANT_NAME),
            _fact("application.number", context.FIXTURE_APPLICATION_NUMBER),
            _fact("signatory.name", context.FIXTURE_SIGNATORY_NAME, confidence=0.75),
        )
        self.result = AutofillMapper().get_suggestions(self.definition, self.profile)

    def test_fills_the_applicant_name_field(self):
        self.assertEqual(
            [context.FIXTURE_APPLICANT_NAME],
            self.result["applicant_declaration.applicant_names"].value,
        )

    def test_fills_the_indian_application_number_field(self):
        self.assertEqual(
            context.FIXTURE_APPLICATION_NUMBER,
            self.result["foreign_filings.indian_application_number"].value,
        )

    def test_fills_the_signatory_name_field(self):
        self.assertEqual(
            context.FIXTURE_SIGNATORY_NAME,
            self.result["signatory.signatory_name"].value,
        )

    def test_leaves_fields_with_no_matching_fact_empty(self):
        self.assertNotIn("foreign_filings.indian_filing_date", self.result)


class TestAgainstRealRepeatableForms(unittest.TestCase):
    """The real definitions, filled from the real extractors.

    The paths asserted here were verified against form-renderer.js by mounting
    it and reading back which input each value landed in. They are the
    renderer's state contract, not this module's preference — an assertion that
    passes here but drifts from the renderer is the exact silent failure this
    class exists to catch.
    """

    @classmethod
    def setUpClass(cls):
        import json

        import test_extractors as samples
        from extractors.form2_specification import Form2SpecificationExtractor
        from extractors.form5 import Form5Extractor
        from extractors.patent_certificate import PatentCertificateExtractor
        from extractors.priority_document import PriorityDocumentExtractor

        documents = [
            ("spec", Form2SpecificationExtractor(), samples.SPECIFICATION),
            ("f5", Form5Extractor(), samples.FORM5),
            ("cert", PatentCertificateExtractor(), samples.CERTIFICATE),
            ("prio", PriorityDocumentExtractor(), samples.PRIORITY),
        ]
        profile = PatentProfile(workspace_id="ws")
        for document_id, extractor, text in documents:
            profile.add_extract(DocumentExtract(
                document_id=document_id, workspace_id="ws",
                source_type=extractor.SOURCE_TYPE,
                original_filename=f"{document_id}.pdf", page_count=1,
                facts=extractor.extract_from_file("/x.pdf", document_id, [(1, text)]),
                extractor_version=extractor.EXTRACTOR_VERSION,
            ))

        mapper = AutofillMapper()
        cls.results = {}
        for form_id in ("form_01", "form_03", "form_05", "form_27"):
            definition = json.loads(
                (context.DEFINITIONS_DIR / f"{form_id}.definition.json").read_text(encoding="utf-8")
            )
            cls.results[form_id] = mapper.get_suggestions(definition, profile)

    # The two sample documents name two inventors: Rajesh Kumar, Priya Sharma.

    def test_form5_fills_both_inventor_blocks(self):
        result = self.results["form_05"]
        self.assertEqual("RAJESH KUMAR", result["inventors.inventor.0.name"].value)
        self.assertEqual("PRIYA SHARMA", result["inventors.inventor.1.name"].value)

    def test_form5_asks_the_renderer_for_two_inventor_blocks(self):
        self.assertEqual(2, self.results["form_05"]["inventors.inventor#count"].value)

    def test_form5_fills_the_particulars_it_has_for_the_first_inventor(self):
        result = self.results["form_05"]
        self.assertEqual("Indian", result["inventors.inventor.0.nationality"].value)
        self.assertIn("Residency Road", result["inventors.inventor.0.address"].value)

    def test_form5_leaves_the_second_inventors_address_blank(self):
        """The specification prints an address for the first inventor only."""
        self.assertNotIn("inventors.inventor.1.address", self.results["form_05"])

    def test_form1_fills_the_convention_table_as_row_objects(self):
        rows = self.results["form_01"]["convention_particulars.convention_applications"].value
        self.assertIsInstance(rows, list)
        self.assertEqual("UNITED STATES", rows[0]["country"])
        self.assertEqual("16/123,456", rows[0]["application_number"])
        self.assertEqual("2018-03-12", rows[0]["filing_date"])

    def test_form1_fills_both_inventor_signature_blocks(self):
        result = self.results["form_01"]
        self.assertEqual("RAJESH KUMAR", result["declaration_inventors.inventor_signature.0.name"].value)
        self.assertEqual("PRIYA SHARMA", result["declaration_inventors.inventor_signature.1.name"].value)

    def test_form1_fills_the_repeatable_applicant_group(self):
        result = self.results["form_01"]
        self.assertEqual(
            "ACME INNOVATIONS PRIVATE LIMITED",
            result["applicants.applicant.0.name"].value,
        )
        self.assertEqual("Indian", result["applicants.applicant.0.nationality"].value)

    def test_form27_fills_its_repeatable_patentee_scalars(self):
        result = self.results["form_27"]
        self.assertEqual(["ACME INNOVATIONS PRIVATE LIMITED"],
                         result["patentee.patentee_particulars"].value)
        self.assertEqual(["384756"], result["patentee.patent_number"].value)

    def test_form3_fills_its_foreign_application_table(self):
        rows = self.results["form_03"]["foreign_filings.foreign_applications_table"].value
        self.assertEqual("UNITED STATES", rows[0]["country"])
        self.assertEqual("16/123,456", rows[0]["application_no"])

    def test_no_dead_bracket_paths_survive_anywhere(self):
        for form_id, result in self.results.items():
            for path in result:
                with self.subTest(form=form_id, path=path):
                    self.assertNotIn("[]", path,
                                     "per-cell table paths are invisible to the renderer")

    def test_every_repeated_value_keeps_its_own_provenance(self):
        for form_id, result in self.results.items():
            for path, suggestion in result.items():
                with self.subTest(form=form_id, path=path):
                    self.assertTrue(suggestion.facts, "suggestion carries no facts")
                    if isinstance(suggestion.value, list) and suggestion.value:
                        first = suggestion.value[0]
                        if not isinstance(first, dict):
                            self.assertEqual(
                                len(suggestion.value), len(suggestion.facts),
                                "one fact per repeated value",
                            )

    def test_structural_entries_are_only_ever_instance_counts(self):
        for form_id, result in self.results.items():
            for path, suggestion in result.items():
                if suggestion.structural:
                    with self.subTest(form=form_id, path=path):
                        self.assertTrue(path.endswith("#count"))
                        self.assertIsInstance(suggestion.value, int)


class TestWorkspaceDecisionOverrides(unittest.TestCase):
    """The Workspace→Form bridge: a user's decisions outrank the raw facts.

    Overrides are keyed by vocabulary key. A resolved conflict is a value a
    document supplied; a typed-in value is one none did. Both must reach the
    generated form, and each must read for what it is.
    """

    def setUp(self):
        self.mapper = AutofillMapper()

    def _scalar_def(self, field_id="title", key="invention.title"):
        return _definition([
            {"id": field_id, "autofill": _direct([{"key": key}])},
        ])

    def test_no_overrides_is_unchanged(self):
        definition = self._scalar_def()
        profile = _profile(_fact("invention.title", "From The Document"))
        without = self.mapper.get_suggestions(definition, profile)
        empty = self.mapper.get_suggestions(definition, profile, overrides={})
        self.assertEqual(without["sec.title"].value, "From The Document")
        self.assertEqual(empty["sec.title"].value, "From The Document")

    def test_a_resolved_conflict_value_wins(self):
        definition = self._scalar_def()
        profile = _profile(
            _fact("invention.title", "The Spec Title", source_type="form2_specification"),
            _fact("invention.title", "The Certificate Title", source_type="patent_certificate"),
        )
        result = self.mapper.get_suggestions(
            definition, profile, overrides={"invention.title": "The Certificate Title"}
        )
        self.assertEqual(result["sec.title"].value, "The Certificate Title")

    def test_a_resolved_conflict_keeps_the_document_provenance(self):
        """The chosen value came from a document; its Fact must survive so the
        form can still say where it came from."""
        definition = self._scalar_def()
        profile = _profile(
            _fact("invention.title", "The Certificate Title", source_type="patent_certificate"),
        )
        result = self.mapper.get_suggestions(
            definition, profile, overrides={"invention.title": "The Certificate Title"}
        )
        self.assertEqual("patent_certificate", result["sec.title"].fact.source_type)
        self.assertNotEqual("user", result["sec.title"].fact.source_type)

    def test_a_typed_value_fills_a_field_no_document_supplied(self):
        definition = self._scalar_def(field_id="nationality", key="applicant.nationality")
        profile = _profile(_fact("invention.title", "unrelated"))  # nothing for nationality
        result = self.mapper.get_suggestions(
            definition, profile, overrides={"applicant.nationality": "Indian"}
        )
        self.assertIn("sec.nationality", result)
        self.assertEqual("Indian", result["sec.nationality"].value)

    def test_a_typed_value_reads_as_user_provided(self):
        definition = self._scalar_def(field_id="nationality", key="applicant.nationality")
        profile = _profile(_fact("invention.title", "unrelated"))
        result = self.mapper.get_suggestions(
            definition, profile, overrides={"applicant.nationality": "Indian"}
        )
        fact = result["sec.nationality"].fact
        self.assertEqual("user", fact.source_type)
        self.assertEqual("manual", fact.method)
        self.assertEqual(1.0, fact.confidence)

    def test_an_override_respects_authored_source_order(self):
        """An override at a more-preferred source outranks facts at a less-
        preferred one — exactly as a fact there would have."""
        definition = _definition([
            {"id": "f", "autofill": _direct([
                {"key": "preferred.key"},
                {"key": "fallback.key"},
            ])},
        ])
        profile = _profile(_fact("fallback.key", "from fallback fact"))
        result = self.mapper.get_suggestions(
            definition, profile, overrides={"preferred.key": "user decided"}
        )
        self.assertEqual("user decided", result["sec.f"].value)

    def test_an_override_fills_a_repeatable_group_child(self):
        definition = _definition([
            {"id": "applicant", "repeatable": True, "fields": [
                {"id": "name", "autofill": _direct([{"key": "applicant.name"}])},
                {"id": "nationality", "autofill": _direct([{"key": "applicant.nationality"}])},
            ]},
        ])
        profile = _profile(_fact("applicant.name", "Acme Ltd"))  # no nationality anywhere
        result = self.mapper.get_suggestions(
            definition, profile, overrides={"applicant.nationality": "Indian"}
        )
        self.assertEqual("Acme Ltd", result["sec.applicant.0.name"].value)
        self.assertEqual("Indian", result["sec.applicant.0.nationality"].value)
        self.assertEqual("user", result["sec.applicant.0.nationality"].fact.source_type)

    def test_an_unrelated_override_changes_nothing(self):
        definition = self._scalar_def()
        profile = _profile(_fact("invention.title", "From The Document"))
        result = self.mapper.get_suggestions(
            definition, profile, overrides={"some.other.key": "irrelevant"}
        )
        self.assertEqual("From The Document", result["sec.title"].value)


if __name__ == "__main__":
    unittest.main()
