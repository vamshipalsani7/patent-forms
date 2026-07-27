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

    def test_resolves_table_column_cells_with_row_path_notation(self):
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
        self.assertEqual("Germany", result["sec.foreign_apps[].country"].value)
        self.assertNotIn("sec.foreign_apps[].untouched", result)


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


if __name__ == "__main__":
    unittest.main()
