"""Integration — the complete vertical slice, end to end.

Upload PDF → Workspace → Classifier → Form 1 Extractor → Facts → Patent Profile
→ Autofill Mapper → Suggestions.

The unit tests above each stub their neighbours; these run the real chain over
real PDF bytes so that a break in the seams between stages is caught. They stop
short of the browser: the renderer-facing half of the slice is covered by
tests/frontend/main_area_separation.test.mjs.
"""

from __future__ import annotations

import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path

import context  # noqa: F401  — sets sys.path

import storage.content_store as content_store_module
from fastapi import UploadFile

import app as app_module

WORKSPACE = "default"


class VerticalSliceTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_dir = content_store_module._UPLOADS_DIR
        content_store_module._UPLOADS_DIR = Path(self._tmp.name)
        self.store = content_store_module.ContentStore()
        self._original_store = app_module._store
        app_module._store = self.store

    def tearDown(self):
        app_module._store = self._original_store
        content_store_module._UPLOADS_DIR = self._original_dir
        self._tmp.cleanup()

    def upload(self, document_id, pdf_path, workspace_id=WORKSPACE):
        data = Path(pdf_path).read_bytes()
        upload = UploadFile(
            file=io.BytesIO(data),
            filename=Path(pdf_path).name,
            headers={"content-type": "application/pdf"},
        )
        return asyncio.run(app_module.extract_document(
            file=upload, document_id=document_id, workspace_id=workspace_id,
        ))


class TestFormOneToFormThree(VerticalSliceTestCase):
    """The headline demonstration: a Form 1 PDF pre-fills Form 3."""

    def setUp(self):
        super().setUp()
        self.extract = self.upload("doc_slice", context.FORM1_PDF)
        self.suggestions = app_module.get_suggestions("form_03", WORKSPACE)["suggestions"]

    # --- the upload/extract half ---

    def test_the_pdf_is_classified_as_form1(self):
        self.assertEqual("form1", self.extract["source_type"])

    def test_extraction_produced_facts(self):
        self.assertTrue(self.extract["facts"], "no facts extracted from the Form 1 fixture")

    def test_the_pdf_bytes_are_persisted_for_re_extraction(self):
        """Stored bytes are what make re-extraction possible without re-upload."""
        self.assertIsNotNone(self.store.get_pdf_path(WORKSPACE, "doc_slice"))

    def test_the_extract_is_persisted(self):
        self.assertIsNotNone(self.store.get_extract(WORKSPACE, "doc_slice"))

    # --- the autofill half ---

    def test_applicant_name_reaches_the_form3_field(self):
        self.assertEqual(
            [context.FIXTURE_APPLICANT_NAME],
            self.suggestions["applicant_declaration.applicant_names"]["value"],
        )

    def test_application_number_reaches_the_form3_field(self):
        self.assertEqual(
            context.FIXTURE_APPLICATION_NUMBER,
            self.suggestions["foreign_filings.indian_application_number"]["value"],
        )

    def test_signatory_name_reaches_the_form3_field(self):
        self.assertEqual(
            context.FIXTURE_SIGNATORY_NAME,
            self.suggestions["signatory.signatory_name"]["value"],
        )

    def test_invention_title_is_extracted_even_though_form3_has_no_field_for_it(self):
        """Extraction is demand-driven per document, not per target form."""
        keys = {f["key"] for f in self.extract["facts"]}
        self.assertIn("invention.title", keys)

    # --- provenance survives the whole chain ---

    def test_every_suggestion_can_be_traced_to_a_document_and_page(self):
        self.assertTrue(self.suggestions, "no suggestions to trace")
        for path, entry in self.suggestions.items():
            with self.subTest(field=path):
                fact = entry["fact"]
                self.assertEqual("doc_slice", fact["document_id"])
                self.assertEqual("form1", fact["source_type"])
                self.assertEqual(1, fact["page"])
                self.assertEqual("anchor", fact["method"])
                self.assertEqual("form1@1", fact["extractor_version"])
                self.assertGreater(fact["confidence"], 0.0)


class TestUnsupportedDocument(VerticalSliceTestCase):
    """An unrelated PDF must degrade quietly, never guess."""

    def setUp(self):
        super().setUp()
        self.extract = self.upload("doc_invoice", context.NON_FORM_PDF)

    def test_is_classified_unknown(self):
        self.assertEqual("unknown", self.extract["source_type"])

    def test_yields_no_facts(self):
        self.assertEqual([], self.extract["facts"])

    def test_yields_no_suggestions(self):
        self.assertEqual({}, app_module.get_suggestions("form_03", WORKSPACE)["suggestions"])


class TestReExtraction(VerticalSliceTestCase):
    """An improved extractor must be able to refresh a document in place."""

    def test_re_uploading_the_same_document_id_replaces_its_facts(self):
        self.upload("doc_x", context.FORM1_PDF)
        first = app_module.get_suggestions("form_03", WORKSPACE)["suggestions"]
        self.assertIn("foreign_filings.indian_application_number", first)

        # Same document id, different document content.
        self.upload("doc_x", context.NON_FORM_PDF)
        second = app_module.get_suggestions("form_03", WORKSPACE)["suggestions"]

        self.assertEqual(1, len(self.store.extracts_for_workspace(WORKSPACE)), "re-extraction duplicated the document")
        self.assertEqual({}, second, "stale facts survived re-extraction")


class TestMultipleDocuments(VerticalSliceTestCase):
    def test_facts_from_several_documents_merge_into_one_profile(self):
        self.upload("doc_1", context.FORM1_PDF)
        self.upload("doc_2", context.NON_FORM_PDF)

        self.assertEqual(2, len(self.store.extracts_for_workspace(WORKSPACE)))
        suggestions = app_module.get_suggestions("form_03", WORKSPACE)["suggestions"]
        self.assertEqual(
            "doc_1",
            suggestions["applicant_declaration.applicant_names"]["fact"]["document_id"],
            "the suggestion should be attributed to the document it came from",
        )


class TestSuggestionsMatchTheShippedDefinition(VerticalSliceTestCase):
    """Every suggested path must exist in the definition the renderer will mount.

    A path the renderer has no field for is a silent no-op: the value is
    computed, sent, and then dropped on the floor.
    """

    def test_every_suggested_path_maps_to_a_real_field(self):
        self.upload("doc_slice", context.FORM1_PDF)
        suggestions = app_module.get_suggestions("form_03", WORKSPACE)["suggestions"]

        definition = json.loads(
            (context.DEFINITIONS_DIR / "form_03.definition.json").read_text(encoding="utf-8")
        )

        valid_paths = set()

        def walk(fields, base):
            for field in fields:
                path = f"{base}.{field['id']}"
                valid_paths.add(path)
                if field.get("fields"):
                    walk(field["fields"], path)
                for column in field.get("columns", []):
                    valid_paths.add(f"{path}[].{column['id']}")

        for section in definition["sections"]:
            walk(section.get("fields", []), section["id"])

        self.assertTrue(suggestions, "no suggestions produced")
        for path in suggestions:
            self.assertIn(path, valid_paths, f"suggestion '{path}' has no field in the definition")


if __name__ == "__main__":
    unittest.main()
