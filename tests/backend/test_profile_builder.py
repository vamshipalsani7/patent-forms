"""Profile builder and PatentProfile — extractor dispatch and the merged view.

The builder is the project's extension point: adding a document type means
adding an entry to its registry and nothing else. These tests pin that dispatch
behaviour, and cover the merged PatentProfile projection the mapper queries.
"""

from __future__ import annotations

import unittest

import context  # noqa: F401  — sets sys.path

from extractor.profile_builder import _EXTRACTOR_REGISTRY, ProfileBuilder
from models.document_extract import DocumentExtract
from models.fact import Fact
from models.patent_profile import DocumentType, PatentProfile

FORM1_PAGES = [(1, """FORM 1
APPLICATION FOR GRANT OF PATENT
Application No. : 202211012345

3A. APPLICANT(S)
Name in Full
Acme Innovations Private Limited

5. TITLE OF THE INVENTION
A Novel Method for Efficient Solar Panel Cooling
""")]


def _fact(key, value, source_type="form1", confidence=0.8, document_id="doc_1"):
    return Fact(
        key=key, value=value, document_id=document_id, source_type=source_type,
        page=1, confidence=confidence, method="anchor", extractor_version="form1@1",
    )


def _extract(document_id, *facts, source_type="form1"):
    return DocumentExtract(
        document_id=document_id, source_type=source_type,
        original_filename=f"{document_id}.pdf", page_count=1,
        facts=list(facts), extractor_version="form1@1",
    )


class TestExtractorDispatch(unittest.TestCase):
    def setUp(self):
        self.builder = ProfileBuilder()

    def test_form1_is_routed_to_the_form1_extractor(self):
        extract = self.builder.build(
            file_path=context.FORM1_PDF, document_id="doc_1",
            original_filename="form1.pdf", document_type=DocumentType.FORM1,
            page_texts=FORM1_PAGES,
        )
        self.assertEqual("form1", extract.source_type)
        self.assertTrue(extract.facts, "Form 1 extractor produced no facts")

    def test_records_the_version_of_the_extractor_that_ran(self):
        """Regression: this reported 'unknown@0' while the facts said 'form1@1'."""
        extract = self.builder.build(
            file_path=context.FORM1_PDF, document_id="doc_1",
            original_filename="form1.pdf", document_type=DocumentType.FORM1,
            page_texts=FORM1_PAGES,
        )
        self.assertEqual("form1@1", extract.extractor_version)
        for fact in extract.facts:
            self.assertEqual(extract.extractor_version, fact.extractor_version)

    def test_unregistered_document_type_yields_an_empty_extract(self):
        """Unsupported types degrade quietly — no facts, no exception."""
        extract = self.builder.build(
            file_path=context.FORM1_PDF, document_id="doc_2",
            original_filename="form3.pdf", document_type=DocumentType.FORM3,
            page_texts=FORM1_PAGES,
        )
        self.assertEqual([], extract.facts)
        self.assertEqual("form3", extract.source_type, "classification must still be recorded")
        self.assertEqual("none@0", extract.extractor_version)

    def test_unknown_document_type_yields_an_empty_extract(self):
        extract = self.builder.build(
            file_path=context.NON_FORM_PDF, document_id="doc_3",
            original_filename="invoice.pdf", document_type=DocumentType.UNKNOWN,
            page_texts=[(1, "INVOICE\nTotal Due: 4,500.00")],
        )
        self.assertEqual([], extract.facts)
        self.assertEqual("unknown", extract.source_type)

    def test_page_count_reflects_the_document(self):
        extract = self.builder.build(
            file_path=context.FORM1_PDF, document_id="doc_4",
            original_filename="form1.pdf", document_type=DocumentType.FORM1,
            page_texts=[(1, "FORM 1"), (2, "page two"), (3, "page three")],
        )
        self.assertEqual(3, extract.page_count)

    def test_registered_extractors_are_pinned(self):
        """Registration is the documented extension point, so a surprise
        addition or removal should be visible rather than silent.

        The set is exactly the sourceTypes with enough authored autofill demand
        to justify pattern work. FER, Hearing Notice and Controller Order are
        absent on purpose — no form definition consumes a fact from them.
        """
        self.assertEqual(
            {
                DocumentType.FORM1,
                DocumentType.PATENT_CERTIFICATE,
                DocumentType.FORM26_AUTHORISATION,
                DocumentType.FORM2_SPECIFICATION,
                DocumentType.ASSIGNMENT_DOCUMENT,
                DocumentType.PRIORITY_DOCUMENT,
                DocumentType.FORM5,
                DocumentType.PCT_DOCUMENT,
            },
            set(_EXTRACTOR_REGISTRY),
        )

    def test_every_registered_extractor_declares_its_own_source_type(self):
        """A copy-paste slip here mislabels every fact the extractor produces,
        and the mapper then matches it against the wrong sourceType."""
        for doc_type, extractor in _EXTRACTOR_REGISTRY.items():
            with self.subTest(document_type=doc_type):
                self.assertEqual(doc_type.value, extractor.SOURCE_TYPE)
                self.assertTrue(
                    extractor.EXTRACTOR_VERSION.startswith(doc_type.value + "@"),
                    f"{doc_type.value} extractor version "
                    f"'{extractor.EXTRACTOR_VERSION}' should be '{doc_type.value}@n'",
                )

    def test_every_registered_extractor_exposes_the_expected_interface(self):
        for doc_type, extractor in _EXTRACTOR_REGISTRY.items():
            with self.subTest(document_type=doc_type):
                self.assertTrue(callable(getattr(extractor, "extract_from_file", None)))
                self.assertTrue(getattr(extractor, "EXTRACTOR_VERSION", None))


class TestProfileQueryInterface(unittest.TestCase):
    """get_facts() is the only interface the mapper uses."""

    def test_returns_facts_matching_a_key(self):
        profile = PatentProfile(extracts=[_extract("d1", _fact("applicant.name", "Acme"))])
        self.assertEqual(["Acme"], [f.value for f in profile.get_facts("applicant.name")])

    def test_returns_empty_list_for_an_unknown_key(self):
        profile = PatentProfile(extracts=[_extract("d1", _fact("applicant.name", "Acme"))])
        self.assertEqual([], profile.get_facts("patent.number"))

    def test_filters_by_source_type(self):
        profile = PatentProfile(extracts=[
            _extract("d1", _fact("applicant.name", "From Form 1", source_type="form1")),
            _extract("d2", _fact("applicant.name", "From Certificate",
                                 source_type="patent_certificate"),
                     source_type="patent_certificate"),
        ])
        self.assertEqual(
            ["From Certificate"],
            [f.value for f in profile.get_facts("applicant.name", source_type="patent_certificate")],
        )

    def test_orders_candidates_by_confidence_descending(self):
        profile = PatentProfile(extracts=[
            _extract("d1", _fact("applicant.name", "less sure", confidence=0.60)),
            _extract("d2", _fact("applicant.name", "more sure", confidence=0.95)),
        ])
        self.assertEqual(
            ["more sure", "less sure"],
            [f.value for f in profile.get_facts("applicant.name")],
        )

    def test_keeps_every_competing_candidate(self):
        """Conflicts are the normal case; losing candidates are never discarded."""
        profile = PatentProfile(extracts=[
            _extract("d1", _fact("applicant.name", "Acme Ltd")),
            _extract("d2", _fact("applicant.name", "Acme Limited")),
        ])
        self.assertEqual(2, len(profile.get_facts("applicant.name")))


class TestProfileMutation(unittest.TestCase):
    def test_add_extract_appends(self):
        profile = PatentProfile()
        profile.add_extract(_extract("d1", _fact("applicant.name", "Acme")))
        self.assertEqual(1, len(profile.extracts))

    def test_re_extraction_replaces_rather_than_duplicates(self):
        """Same document_id means the same document was extracted again."""
        profile = PatentProfile()
        profile.add_extract(_extract("d1", _fact("applicant.name", "Old Name")))
        profile.add_extract(_extract("d1", _fact("applicant.name", "New Name")))

        self.assertEqual(1, len(profile.extracts))
        self.assertEqual(["New Name"], [f.value for f in profile.get_facts("applicant.name")])

    def test_different_documents_accumulate(self):
        profile = PatentProfile()
        profile.add_extract(_extract("d1", _fact("applicant.name", "Acme")))
        profile.add_extract(_extract("d2", _fact("application.number", "202211012345")))
        self.assertEqual(2, len(profile.extracts))


class TestBackwardCompatibleFieldsView(unittest.TestCase):
    def test_fields_exposes_a_flat_key_value_projection(self):
        profile = PatentProfile(extracts=[
            _extract("d1", _fact("applicant.name", "Acme"), _fact("application.number", "202211012345"))
        ])
        self.assertEqual(
            {"applicant.name": "Acme", "application.number": "202211012345"},
            profile.fields,
        )

    def test_fields_is_empty_for_an_empty_profile(self):
        self.assertEqual({}, PatentProfile().fields)


if __name__ == "__main__":
    unittest.main()
