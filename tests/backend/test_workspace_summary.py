"""WorkspaceSummary — the consolidated, form-independent view of a matter.

This is what the Patent Workspace screen renders, so the tests pin the four
things that screen promises: facts grouped the way a professional reads them,
every value traceable to its document and page, genuine disagreements surfaced
as conflicts (and normal multiplicity NOT surfaced as one), and only truly
absent core fields reported missing.
"""

from __future__ import annotations

import unittest

import context  # noqa: F401  — sets sys.path

from models.document_extract import DocumentExtract
from models.fact import Fact
from models.patent_profile import PatentProfile
from workspace.summary import (
    CORE_FIELDS,
    build_workspace_summary,
    key_label,
    source_type_label,
)


def _fact(key, value, source_type="form1", confidence=0.85, document_id="d1", page=1):
    return Fact(
        key=key, value=value, document_id=document_id, source_type=source_type,
        page=page, confidence=confidence, method="anchor", extractor_version="x@1",
    )


def _extract(document_id, *facts, source_type="form1", filename=None, page_count=1):
    # Real extractors stamp each fact with the document_id they were given, so
    # fact.document_id always matches its extract. Honour that here — the
    # filename lookup in the summary depends on it.
    owned = [f.model_copy(update={"document_id": document_id}) for f in facts]
    return DocumentExtract(
        document_id=document_id, workspace_id="ws", source_type=source_type,
        original_filename=filename or f"{document_id}.pdf", page_count=page_count,
        facts=owned, extractor_version="x@1",
    )


def _profile(*extracts):
    return PatentProfile(workspace_id="ws", extracts=list(extracts))


def _section(summary, section_id):
    for s in summary["sections"]:
        if s["id"] == section_id:
            return s
    return None


def _field(summary, section_id, key):
    section = _section(summary, section_id)
    if not section:
        return None
    for f in section["fields"]:
        if f["key"] == key:
            return f
    return None


class TestGrouping(unittest.TestCase):
    def setUp(self):
        self.summary = build_workspace_summary(_profile(
            _extract("d1",
                     _fact("invention.title", "A Widget"),
                     _fact("applicant.name", "Acme Ltd"),
                     _fact("inventor.name", "R. Kumar"),
                     _fact("application.number", "202211012345")),
        ))

    def test_facts_land_in_their_professional_sections(self):
        self.assertIsNotNone(_field(self.summary, "title", "invention.title"))
        self.assertIsNotNone(_field(self.summary, "applicants", "applicant.name"))
        self.assertIsNotNone(_field(self.summary, "inventors", "inventor.name"))
        self.assertIsNotNone(_field(self.summary, "application", "application.number"))

    def test_empty_sections_are_omitted(self):
        ids = [s["id"] for s in self.summary["sections"]]
        self.assertNotIn("assignment", ids)
        self.assertNotIn("pct", ids)

    def test_sections_keep_their_reading_order(self):
        ids = [s["id"] for s in self.summary["sections"]]
        self.assertEqual(ids, sorted(ids, key=["title", "applicants", "inventors",
                                               "agent", "application", "patent",
                                               "priority", "pct", "assignment",
                                               "other"].index))

    def test_assignee_and_priority_route_by_their_own_sections(self):
        summary = build_workspace_summary(_profile(
            _extract("deed", _fact("assignee.name", "Globex", source_type="assignment_document"),
                     source_type="assignment_document"),
            _extract("prio", _fact("foreignApplications[].country", "Germany",
                                   source_type="priority_document"),
                     source_type="priority_document"),
        ))
        self.assertIsNotNone(_field(summary, "assignment", "assignee.name"))
        self.assertIsNotNone(_field(summary, "priority", "foreignApplications[].country"))

    def test_pct_sourced_application_facts_route_to_the_pct_section(self):
        """A source-type home takes precedence over the key-namespace home, so a
        PCT document's application number reads under PCT, not Application."""
        summary = build_workspace_summary(_profile(
            _extract("pct", _fact("application.number", "PCT/IN2019/050123",
                                  source_type="pct_document"),
                     source_type="pct_document"),
        ))
        self.assertIsNotNone(_field(summary, "pct", "application.number"))
        self.assertIsNone(_field(summary, "application", "application.number"))


class TestProvenance(unittest.TestCase):
    def test_every_value_carries_document_page_and_confidence(self):
        summary = build_workspace_summary(_profile(
            _extract("cert", _fact("patent.number", "384756", source_type="patent_certificate",
                                   confidence=0.9, page=2),
                     source_type="patent_certificate", filename="certificate.pdf"),
        ))
        row = _field(summary, "patent", "patent.number")["values"][0]
        self.assertEqual("384756", row["value"])
        self.assertEqual(2, row["page"])
        self.assertEqual(0.9, row["confidence"])
        self.assertEqual("certificate.pdf", row["source_document"])
        self.assertEqual("Patent Certificate", row["source_type_label"])

    def test_the_source_document_is_the_filename_not_the_internal_id(self):
        summary = build_workspace_summary(_profile(
            _extract("doc_ms9x_abc", _fact("invention.title", "A Widget"),
                     filename="my_specification.pdf"),
        ))
        row = _field(summary, "title", "invention.title")["values"][0]
        self.assertEqual("my_specification.pdf", row["source_document"])


class TestConflicts(unittest.TestCase):
    def test_disagreement_on_a_singular_field_is_flagged(self):
        summary = build_workspace_summary(_profile(
            _extract("spec", _fact("invention.title", "A Widget", source_type="form2_specification"),
                     source_type="form2_specification"),
            _extract("cert", _fact("invention.title", "A Gadget", source_type="patent_certificate"),
                     source_type="patent_certificate"),
        ))
        field = _field(summary, "title", "invention.title")
        self.assertTrue(field["conflict"])
        self.assertEqual(2, len(field["values"]))
        self.assertEqual(1, summary["stats"]["conflict_count"])

    def test_agreement_on_a_singular_field_is_not_a_conflict(self):
        summary = build_workspace_summary(_profile(
            _extract("spec", _fact("invention.title", "A Widget", source_type="form2_specification"),
                     source_type="form2_specification"),
            _extract("cert", _fact("invention.title", "A Widget", source_type="patent_certificate"),
                     source_type="patent_certificate"),
        ))
        field = _field(summary, "title", "invention.title")
        self.assertFalse(field["conflict"])
        self.assertEqual(1, len(field["values"]), "identical values collapse to one row")

    def test_multiple_inventors_are_not_a_conflict(self):
        """Repeatable fields legitimately hold several values; flagging that as
        a conflict would cry wolf on every joint application."""
        summary = build_workspace_summary(_profile(
            _extract("spec",
                     _fact("inventor.name", "R. Kumar"),
                     _fact("inventor.name", "P. Sharma")),
        ))
        field = _field(summary, "inventors", "inventor.name")
        self.assertFalse(field["conflict"])
        self.assertEqual(2, len(field["values"]))
        self.assertEqual(0, summary["stats"]["conflict_count"])

    def test_agreeing_documents_keep_the_higher_confidence(self):
        summary = build_workspace_summary(_profile(
            _extract("a", _fact("application.number", "202211012345", confidence=0.8)),
            _extract("b", _fact("application.number", "202211012345", confidence=0.95)),
        ))
        row = _field(summary, "application", "application.number")["values"][0]
        self.assertEqual(0.95, row["confidence"])


class TestMissingInformation(unittest.TestCase):
    def test_absent_core_fields_are_reported(self):
        summary = build_workspace_summary(_profile(
            _extract("d1", _fact("invention.title", "A Widget")),
        ))
        missing_keys = {m["key"] for m in summary["missing"]}
        self.assertIn("applicant.name", missing_keys)
        self.assertIn("application.number", missing_keys)

    def test_present_fields_are_never_reported_missing(self):
        summary = build_workspace_summary(_profile(
            _extract("d1", _fact("invention.title", "A Widget")),
        ))
        missing_keys = {m["key"] for m in summary["missing"]}
        self.assertNotIn("invention.title", missing_keys)

    def test_only_core_fields_are_ever_missing(self):
        summary = build_workspace_summary(_profile())
        self.assertEqual({m["key"] for m in summary["missing"]}, set(CORE_FIELDS))

    def test_missing_entries_carry_a_human_label(self):
        summary = build_workspace_summary(_profile())
        self.assertTrue(all(m["label"] for m in summary["missing"]))
        self.assertIn(
            "Applicant Nationality",
            [m["label"] for m in summary["missing"]],
        )


class TestDocuments(unittest.TestCase):
    def test_each_document_reports_type_and_status(self):
        summary = build_workspace_summary(_profile(
            _extract("cert", _fact("patent.number", "384756", source_type="patent_certificate"),
                     source_type="patent_certificate", filename="cert.pdf", page_count=1),
        ))
        doc = summary["documents"][0]
        self.assertEqual("cert.pdf", doc["filename"])
        self.assertEqual("Patent Certificate", doc["document_type"])
        self.assertEqual("extracted", doc["status"])
        self.assertEqual(1, doc["fact_count"])

    def test_a_recognised_document_with_no_facts_reads_as_no_information(self):
        summary = build_workspace_summary(_profile(
            _extract("f3", source_type="form3", filename="form3.pdf"),
        ))
        self.assertEqual("no_information", summary["documents"][0]["status"])

    def test_an_unreadable_document_reads_as_unrecognised(self):
        summary = build_workspace_summary(_profile(
            _extract("scan", source_type="unknown", filename="scan.pdf", page_count=4),
        ))
        self.assertEqual("unrecognised", summary["documents"][0]["status"])


class TestNoInternalNamesLeak(unittest.TestCase):
    """UX rule: the interface never exposes vocabulary keys or sourceTypes as
    labels. The summary is where raw names must become human language."""

    def test_source_types_have_human_labels(self):
        self.assertEqual("Patent Certificate", source_type_label("patent_certificate"))
        self.assertEqual("Form 1 (Application for Grant)", source_type_label("form1"))

    def test_keys_have_human_labels(self):
        self.assertEqual("Title of the Invention", key_label("invention.title"))
        self.assertEqual("Agent Registration No. (IN/PA)", key_label("agent.inpaNumber"))

    def test_empty_workspace_is_well_formed(self):
        summary = build_workspace_summary(_profile())
        self.assertEqual([], summary["documents"])
        self.assertEqual([], summary["sections"])
        self.assertEqual(0, summary["stats"]["fact_count"])


if __name__ == "__main__":
    unittest.main()
