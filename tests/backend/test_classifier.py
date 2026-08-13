"""Document classifier — anchor-based routing to an extractor.

Misclassification is a silent failure: the wrong extractor runs, finds nothing,
and the user simply sees no suggestions. These tests pin the anchors that matter
for the vertical slice and the deliberate UNKNOWN fallback.
"""

from __future__ import annotations

import unittest

import context  # noqa: F401  — sets sys.path

from extractor.classifier import DocumentClassifier
from extractor.pdf_reader import PDFReader
from models.patent_profile import DocumentType


class TestFormOneClassification(unittest.TestCase):
    def setUp(self):
        self.classifier = DocumentClassifier()

    def test_classifies_by_official_title_anchor(self):
        text = "THE PATENTS ACT, 1970\nAPPLICATION FOR GRANT OF PATENT\n"
        self.assertEqual(DocumentType.FORM1, self.classifier.classify(text))

    def test_classifies_by_form_number_anchor(self):
        self.assertEqual(DocumentType.FORM1, self.classifier.classify("FORM 1\nsome body text"))

    def test_classifies_by_statutory_reference_anchor(self):
        text = "See Section 7, 54 and 135 and rule 20(1)"
        self.assertEqual(DocumentType.FORM1, self.classifier.classify(text))

    def test_is_case_insensitive(self):
        self.assertEqual(
            DocumentType.FORM1,
            self.classifier.classify("application for grant of patent"),
        )

    def test_tolerates_irregular_whitespace_from_pdf_text_layer(self):
        self.assertEqual(
            DocumentType.FORM1,
            self.classifier.classify("APPLICATION   FOR\nGRANT  OF   PATENT"),
        )

    def test_form_number_anchor_does_not_over_match_longer_numbers(self):
        """'FORM 18' must not be read as 'FORM 1' — \\b guards the boundary."""
        self.assertNotEqual(
            DocumentType.FORM1,
            self.classifier.classify("FORM 18\nRequest for Examination"),
        )


class TestOtherDocumentTypes(unittest.TestCase):
    def setUp(self):
        self.classifier = DocumentClassifier()

    def test_recognises_the_document_types_it_claims_to(self):
        cases = [
            ("STATEMENT AND UNDERTAKING UNDER SECTION 8", DocumentType.FORM3),
            ("COMPLETE SPECIFICATION", DocumentType.FORM2_SPECIFICATION),
            ("DECLARATION AS TO INVENTORSHIP", DocumentType.FORM5),
            ("PATENT CERTIFICATE", DocumentType.PATENT_CERTIFICATE),
            ("PRIORITY DOCUMENT", DocumentType.PRIORITY_DOCUMENT),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(expected, self.classifier.classify(text))


class TestUnknownFallback(unittest.TestCase):
    def setUp(self):
        self.classifier = DocumentClassifier()

    def test_unrelated_document_is_unknown_not_generic(self):
        """UNKNOWN is a classification outcome; GENERIC is a processing mode."""
        text = "INVOICE\nAcme Stationery Supplies\nTotal Due: 4,500.00"
        self.assertEqual(DocumentType.UNKNOWN, self.classifier.classify(text))

    def test_empty_text_is_unknown(self):
        self.assertEqual(DocumentType.UNKNOWN, self.classifier.classify(""))

    def test_anchor_beyond_the_scanned_head_is_not_matched(self):
        """Only the first 3000 chars are scanned — a deliberate speed tradeoff."""
        buried = ("x" * 3200) + "\nAPPLICATION FOR GRANT OF PATENT"
        self.assertEqual(DocumentType.UNKNOWN, self.classifier.classify(buried))


class TestClassifierOnRealPdfs(unittest.TestCase):
    """End of the read→classify seam, using the committed PDF fixtures."""

    def setUp(self):
        self.classifier = DocumentClassifier()
        self.reader = PDFReader()

    def test_form1_fixture_pdf_classifies_as_form1(self):
        text = self.reader.read(context.FORM1_PDF)
        self.assertEqual(DocumentType.FORM1, self.classifier.classify(text))

    def test_non_form_fixture_pdf_classifies_as_unknown(self):
        text = self.reader.read(context.NON_FORM_PDF)
        self.assertEqual(DocumentType.UNKNOWN, self.classifier.classify(text))


class TestPdfReader(unittest.TestCase):
    def setUp(self):
        self.reader = PDFReader()

    def test_read_pages_returns_one_indexed_page_numbers(self):
        pages = self.reader.read_pages(context.FORM1_PDF)
        self.assertGreaterEqual(len(pages), 1)
        self.assertEqual([1], [n for n, _ in pages][:1])

    def test_read_joins_all_page_text(self):
        text = self.reader.read(context.FORM1_PDF)
        self.assertIn("APPLICATION FOR GRANT OF PATENT", text)
        self.assertIn(context.FIXTURE_APPLICANT_NAME, text)


if __name__ == "__main__":
    unittest.main()
