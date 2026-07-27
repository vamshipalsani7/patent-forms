"""Form 1 extractor — the only extractor in the vertical slice.

Two things are under test: that the three slice fields come out correctly, and
that every value carries complete provenance. The second matters as much as the
first — a suggestion the user cannot trace back to a document and page is an
assertion, and these values end up on signed statutory filings.
"""

from __future__ import annotations

import unittest

import context  # noqa: F401  — sets sys.path

from extractors.form1 import EXTRACTOR_VERSION, SOURCE_TYPE, Form1Extractor
from models.fact import Fact

FORM1_TEXT = """FORM 1
THE PATENTS ACT, 1970
APPLICATION FOR GRANT OF PATENT
See Section 7, 54 and 135 and rule 20(1)

Application No. : 202211012345

3A. APPLICANT(S)
Name in Full
Acme Innovations Private Limited

5. TITLE OF THE INVENTION
A Novel Method for Efficient Solar Panel Cooling

Signature
Name: Rajesh Kumar
"""


def _facts_from(text, document_id="doc_test", pages=None):
    """Run the extractor over synthetic page text.

    The fixture PDF has no AcroForm, so Tier 1 yields nothing and this
    exercises the Tier 2 anchor path deterministically.
    """
    page_texts = pages if pages is not None else [(1, text)]
    return Form1Extractor().extract_from_file(context.FORM1_PDF, document_id, page_texts)


def _by_key(facts):
    return {f.key: f for f in facts}


class TestSliceFieldExtraction(unittest.TestCase):
    """The three fields the vertical slice promises, plus the signatory."""

    def setUp(self):
        self.facts = _by_key(_facts_from(FORM1_TEXT))

    def test_extracts_applicant_name(self):
        self.assertEqual(context.FIXTURE_APPLICANT_NAME, self.facts["applicant.name"].value)

    def test_extracts_application_number(self):
        self.assertEqual(context.FIXTURE_APPLICATION_NUMBER, self.facts["application.number"].value)

    def test_extracts_invention_title(self):
        self.assertEqual(context.FIXTURE_INVENTION_TITLE, self.facts["invention.title"].value)

    def test_extracts_signatory_name(self):
        self.assertEqual(context.FIXTURE_SIGNATORY_NAME, self.facts["signatory.name"].value)

    def test_emits_at_most_one_fact_per_key(self):
        facts = _facts_from(FORM1_TEXT)
        keys = [f.key for f in facts]
        self.assertEqual(sorted(set(keys)), sorted(keys), "duplicate facts for the same key")


class TestProvenanceCompleteness(unittest.TestCase):
    """Every extracted value must answer: which document, page, how, how sure."""

    def setUp(self):
        self.facts = _facts_from(FORM1_TEXT, document_id="doc_abc123")

    def test_every_fact_carries_full_provenance(self):
        self.assertTrue(self.facts, "extractor produced no facts to check")
        for fact in self.facts:
            with self.subTest(key=fact.key):
                self.assertEqual("doc_abc123", fact.document_id, "missing source document")
                self.assertEqual(SOURCE_TYPE, fact.source_type)
                self.assertIsNotNone(fact.page, "missing page number")
                self.assertGreaterEqual(fact.page, 1)
                self.assertIn(fact.method, {"anchor", "acroform", "ocr", "manual"})
                self.assertGreater(fact.confidence, 0.0)
                self.assertLessEqual(fact.confidence, 1.0)
                self.assertEqual(EXTRACTOR_VERSION, fact.extractor_version)
                self.assertTrue(fact.extracted_at, "missing extraction timestamp")

    def test_anchor_extraction_is_labelled_as_such(self):
        for fact in self.facts:
            self.assertEqual("anchor", fact.method)

    def test_confidence_reflects_extraction_certainty(self):
        by_key = _by_key(self.facts)
        self.assertEqual(0.80, by_key["applicant.name"].confidence)
        self.assertEqual(0.80, by_key["application.number"].confidence)
        self.assertEqual(0.80, by_key["invention.title"].confidence)
        # The signatory anchor is looser, and says so.
        self.assertEqual(0.75, by_key["signatory.name"].confidence)

    def test_extractor_version_is_readable_off_the_instance(self):
        """profile_builder reads this via getattr on the instance.

        It was previously only a module-level constant, so DocumentExtract
        recorded 'unknown@0' while the individual facts were correct.
        """
        self.assertEqual(EXTRACTOR_VERSION, getattr(Form1Extractor(), "EXTRACTOR_VERSION", None))


class TestPageAttribution(unittest.TestCase):
    def test_reports_the_page_the_value_was_found_on(self):
        pages = [
            (1, "FORM 1\nAPPLICATION FOR GRANT OF PATENT\nApplication No. : 202211012345"),
            (2, "5. TITLE OF THE INVENTION\nA Novel Method for Efficient Solar Panel Cooling"),
        ]
        facts = _by_key(_facts_from("", pages=pages))
        self.assertEqual(1, facts["application.number"].page)
        self.assertEqual(2, facts["invention.title"].page)


class TestApplicationNumberFormats(unittest.TestCase):
    def test_reads_plain_numeric_application_number(self):
        facts = _by_key(_facts_from("Application No. : 202211012345"))
        self.assertEqual("202211012345", facts["application.number"].value)

    def test_reads_legacy_slash_delimited_application_number(self):
        facts = _by_key(_facts_from("Application No: 1234/DEL/2015"))
        self.assertEqual("1234/DEL/2015", facts["application.number"].value)


class TestTitleVariants(unittest.TestCase):
    def test_reads_title_on_the_following_line(self):
        facts = _by_key(_facts_from("5. TITLE OF THE INVENTION\nA Better Widget"))
        self.assertEqual("A Better Widget", facts["invention.title"].value)

    def test_reads_title_on_the_same_line_after_a_colon(self):
        facts = _by_key(_facts_from("TITLE OF THE INVENTION: A Better Widget"))
        self.assertEqual("A Better Widget", facts["invention.title"].value)

    def test_collapses_pdf_whitespace_artefacts(self):
        facts = _by_key(_facts_from("5. TITLE OF THE INVENTION\nA    Better     Widget"))
        self.assertEqual("A Better Widget", facts["invention.title"].value)


class TestExtractorRestraint(unittest.TestCase):
    """It records what it finds and nothing else — no invented values."""

    def test_produces_no_facts_for_an_unrelated_document(self):
        facts = _facts_from("INVOICE\nAcme Stationery\nTotal Due: 4,500.00")
        self.assertEqual([], facts)

    def test_produces_no_facts_for_empty_text(self):
        self.assertEqual([], _facts_from(""))

    def test_omits_only_the_keys_it_cannot_find(self):
        """A partial document yields partial facts, not placeholder values."""
        facts = _by_key(_facts_from("Application No. : 202211012345"))
        self.assertIn("application.number", facts)
        self.assertNotIn("invention.title", facts)
        self.assertNotIn("applicant.name", facts)


class TestTierPrecedence(unittest.TestCase):
    """Tier 1 (AcroForm) wins; Tier 2 (anchor) only fills what it missed."""

    def test_anchor_does_not_override_an_acroform_value(self):
        extractor = Form1Extractor()
        acroform_fact = Fact(
            key="application.number",
            value="999999999999",
            document_id="doc_test",
            source_type=SOURCE_TYPE,
            page=1,
            confidence=0.95,
            method="acroform",
            extractor_version=EXTRACTOR_VERSION,
        )
        extractor._extract_acroform = lambda *_args, **_kwargs: [acroform_fact]

        facts = extractor.extract_from_file(context.FORM1_PDF, "doc_test", [(1, FORM1_TEXT)])
        numbers = [f for f in facts if f.key == "application.number"]

        self.assertEqual(1, len(numbers), "anchor tier duplicated an AcroForm key")
        self.assertEqual("acroform", numbers[0].method)
        self.assertEqual("999999999999", numbers[0].value)

    def test_anchor_still_fills_keys_acroform_did_not_find(self):
        extractor = Form1Extractor()
        extractor._extract_acroform = lambda *_args, **_kwargs: []
        facts = _by_key(extractor.extract_from_file(context.FORM1_PDF, "doc_test", [(1, FORM1_TEXT)]))
        self.assertIn("invention.title", facts)


if __name__ == "__main__":
    unittest.main()
