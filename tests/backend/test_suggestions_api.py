"""Suggestion generation and the content store.

These call the endpoint functions directly rather than over HTTP: the project
has no httpx installed (which FastAPI's TestClient requires), and the routing
layer is thin enough that the value is in the pipeline behind it. Every test
redirects the content store at a temp directory so the real backend/uploads/
is never touched.
"""

from __future__ import annotations

import asyncio
import io
import tempfile
import unittest
from pathlib import Path

import context  # noqa: F401  — sets sys.path

import storage.content_store as content_store_module
from fastapi import HTTPException, UploadFile

import app as app_module
from models.document_extract import DocumentExtract
from models.fact import Fact


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


class IsolatedStoreTestCase(unittest.TestCase):
    """Points the module-level content store at a throwaway directory."""

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

    def upload(self, document_id, pdf_path, filename=None, content_type="application/pdf"):
        data = Path(pdf_path).read_bytes()
        upload = UploadFile(
            file=io.BytesIO(data),
            filename=filename or Path(pdf_path).name,
            headers={"content-type": content_type},
        )
        return asyncio.run(app_module.extract_document(file=upload, document_id=document_id))


class TestSuggestionGeneration(IsolatedStoreTestCase):
    def test_returns_the_documented_response_shape(self):
        self.store.save_extract(_extract("d1", _fact("applicant.name", "Acme Ltd")))
        response = app_module.get_suggestions("form_03")

        self.assertEqual("form_03", response["form_id"])
        self.assertIsInstance(response["suggestions"], dict)

    def test_each_suggestion_carries_value_and_provenance(self):
        self.store.save_extract(_extract("d1", _fact("applicant.name", "Acme Ltd")))
        suggestions = app_module.get_suggestions("form_03")["suggestions"]

        self.assertIn("applicant_declaration.applicant_names", suggestions)
        entry = suggestions["applicant_declaration.applicant_names"]
        self.assertIn("value", entry)
        for field in ("document_id", "source_type", "page", "confidence",
                      "method", "extractor_version"):
            self.assertIn(field, entry["fact"], f"provenance is missing '{field}'")

    def test_no_documents_means_no_suggestions(self):
        response = app_module.get_suggestions("form_03")
        self.assertEqual({}, response["suggestions"])

    def test_a_document_with_no_facts_produces_no_suggestions(self):
        self.store.save_extract(_extract("d1", source_type="unknown"))
        self.assertEqual({}, app_module.get_suggestions("form_03")["suggestions"])

    def test_unknown_form_id_raises_404(self):
        with self.assertRaises(HTTPException) as caught:
            app_module.get_suggestions("form_99_does_not_exist")
        self.assertEqual(404, caught.exception.status_code)

    def test_form_id_is_not_used_to_traverse_the_filesystem(self):
        with self.assertRaises(HTTPException) as caught:
            app_module.get_suggestions("../../../etc/passwd")
        self.assertEqual(404, caught.exception.status_code)


class TestContentStore(IsolatedStoreTestCase):
    def test_saves_and_returns_the_pdf_path(self):
        path = self.store.save_pdf("d1", b"%PDF-1.4 fake bytes")
        self.assertTrue(path.exists())
        self.assertEqual(path, self.store.get_pdf_path("d1"))

    def test_returns_none_for_an_unknown_pdf(self):
        self.assertIsNone(self.store.get_pdf_path("never_uploaded"))

    def test_round_trips_an_extract(self):
        self.store.save_extract(_extract("d1", _fact("applicant.name", "Acme Ltd")))
        loaded = self.store.get_extract("d1")

        self.assertIsNotNone(loaded)
        self.assertEqual("Acme Ltd", loaded.facts[0].value)
        self.assertEqual("form1", loaded.source_type)

    def test_re_extraction_replaces_the_previous_record(self):
        self.store.save_extract(_extract("d1", _fact("applicant.name", "Old Name")))
        self.store.save_extract(_extract("d1", _fact("applicant.name", "New Name")))

        self.assertEqual(1, len(self.store.all_extracts()))
        self.assertEqual("New Name", self.store.get_extract("d1").facts[0].value)

    def test_extracts_survive_a_restart(self):
        """Extracts are rebuildable, but must not be lost on process restart."""
        self.store.save_extract(_extract("d1", _fact("applicant.name", "Acme Ltd")))
        reopened = content_store_module.ContentStore()

        self.assertEqual(1, len(reopened.all_extracts()))
        self.assertEqual("Acme Ltd", reopened.get_extract("d1").facts[0].value)

    def test_a_corrupt_sidecar_is_skipped_rather_than_fatal(self):
        self.store.save_extract(_extract("d1", _fact("applicant.name", "Acme Ltd")))
        (Path(self._tmp.name) / "d2.extract.json").write_text("{ corrupt", encoding="utf-8")

        reopened = content_store_module.ContentStore()
        self.assertEqual(["d1"], [e.document_id for e in reopened.all_extracts()])


class TestExtractEndpointGuards(IsolatedStoreTestCase):
    def test_rejects_a_non_pdf_content_type(self):
        upload = UploadFile(
            file=io.BytesIO(b"plain text"), filename="notes.txt",
            headers={"content-type": "text/plain"},
        )
        with self.assertRaises(HTTPException) as caught:
            asyncio.run(app_module.extract_document(file=upload, document_id="d1"))
        self.assertEqual(400, caught.exception.status_code)

    def test_rejects_an_empty_upload(self):
        upload = UploadFile(
            file=io.BytesIO(b""), filename="empty.pdf",
            headers={"content-type": "application/pdf"},
        )
        with self.assertRaises(HTTPException) as caught:
            asyncio.run(app_module.extract_document(file=upload, document_id="d1"))
        self.assertEqual(400, caught.exception.status_code)

    def test_an_unreadable_pdf_degrades_instead_of_raising_500(self):
        """The form must stay usable when extraction fails."""
        upload = UploadFile(
            file=io.BytesIO(b"%PDF-1.4 this is not really a pdf"),
            filename="broken.pdf", headers={"content-type": "application/pdf"},
        )
        result = asyncio.run(app_module.extract_document(file=upload, document_id="d_broken"))

        self.assertIn("error", result)
        self.assertEqual([], result["facts"])
        self.assertEqual("d_broken", result["document_id"])


class TestWorkspaceScopingBoundary(IsolatedStoreTestCase):
    """Where cross-matter isolation is (and is not) enforced today.

    Merging a Form 1 for Patent A with a certificate for Patent B produces a
    confidently wrong profile — the worst failure mode, because it looks fine.
    In this slice that isolation lives in the frontend documentStore
    (`workspaceId`, covered by tests/frontend/document_store.test.mjs). The
    backend content store is deliberately still a flat pool; this test records
    that boundary so a future workspace-scoped store has a failing test to fix
    rather than an unstated assumption to discover.
    """

    def test_backend_store_currently_pools_all_documents(self):
        self.store.save_extract(_extract("patent_a", _fact("applicant.name", "Company A")))
        self.store.save_extract(_extract("patent_b", _fact("applicant.name", "Company B")))

        self.assertEqual(2, len(self.store.all_extracts()))

    def test_a_profile_only_ever_sees_the_extracts_it_is_given(self):
        """The isolation primitive: scoping is a matter of what you pass in."""
        from models.patent_profile import PatentProfile

        extract_a = _extract("patent_a", _fact("applicant.name", "Company A"))
        extract_b = _extract("patent_b", _fact("applicant.name", "Company B"))

        profile_a = PatentProfile(extracts=[extract_a])
        profile_b = PatentProfile(extracts=[extract_b])

        self.assertEqual(["Company A"], [f.value for f in profile_a.get_facts("applicant.name")])
        self.assertEqual(["Company B"], [f.value for f in profile_b.get_facts("applicant.name")])


if __name__ == "__main__":
    unittest.main()
