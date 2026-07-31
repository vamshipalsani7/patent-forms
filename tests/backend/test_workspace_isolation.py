"""Workspace isolation — the guarantee that two patents can never merge.

A Form 1 for Patent A combined with a certificate for Patent B yields a
confidently wrong profile. That is worse than an empty one, because nothing
looks broken: the attorney sees a filled field, and the wrong application number
reaches a signed statutory filing.

These tests attack that from every layer that could leak:

  1. the store          — can workspace A's documents be read from workspace B?
  2. the model          — can a profile be assembled from mixed extracts?
  3. the API            — can a suggestion request see another workspace?
  4. the filesystem     — can an id escape its workspace directory?
  5. persistence        — does ownership survive a restart?
  6. the absent API     — is there any unscoped bulk read left to misuse?
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
from pydantic import ValidationError

import app as app_module
from models.document_extract import DocumentExtract
from models.fact import Fact
from models.patent_profile import PatentProfile
from storage.content_store import ContentStore, UnsafeIdentifierError

PATENT_A = "patent_a"
PATENT_B = "patent_b"


def _fact(key, value, source_type="form1", confidence=0.8, document_id="doc_1"):
    return Fact(
        key=key, value=value, document_id=document_id, source_type=source_type,
        page=1, confidence=confidence, method="anchor", extractor_version="form1@1",
    )


def _extract(document_id, workspace_id, *facts, source_type="form1"):
    # Facts are re-stamped with their parent's document_id, exactly as the real
    # extractor does — provenance that disagreed with its own record would make
    # the attribution assertions below meaningless.
    owned = [f.model_copy(update={"document_id": document_id}) for f in facts]
    return DocumentExtract(
        document_id=document_id, workspace_id=workspace_id, source_type=source_type,
        original_filename=f"{document_id}.pdf", page_count=1,
        facts=owned, extractor_version="form1@1",
    )


class WorkspaceTestCase(unittest.TestCase):
    """Redirects the content store at a throwaway directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_dir = content_store_module._UPLOADS_DIR
        content_store_module._UPLOADS_DIR = Path(self._tmp.name)
        self.uploads = Path(self._tmp.name)
        self.store = ContentStore()
        self._original_store = app_module._store
        app_module._store = self.store

    def tearDown(self):
        app_module._store = self._original_store
        content_store_module._UPLOADS_DIR = self._original_dir
        self._tmp.cleanup()

    def upload(self, document_id, workspace_id, pdf_path):
        data = Path(pdf_path).read_bytes()
        upload = UploadFile(
            file=io.BytesIO(data), filename=Path(pdf_path).name,
            headers={"content-type": "application/pdf"},
        )
        return asyncio.run(app_module.extract_document(
            file=upload, document_id=document_id, workspace_id=workspace_id,
        ))


# ---------------------------------------------------------------- 1. the store

class TestStoreIsolation(WorkspaceTestCase):
    def setUp(self):
        super().setUp()
        self.store.save_extract(_extract("doc_a", PATENT_A, _fact("applicant.name", "Company A")))
        self.store.save_extract(_extract("doc_b", PATENT_B, _fact("applicant.name", "Company B")))

    def test_a_workspace_sees_only_its_own_documents(self):
        self.assertEqual(["doc_a"], [e.document_id for e in self.store.extracts_for_workspace(PATENT_A)])
        self.assertEqual(["doc_b"], [e.document_id for e in self.store.extracts_for_workspace(PATENT_B)])

    def test_a_document_cannot_be_fetched_from_the_wrong_workspace(self):
        self.assertIsNotNone(self.store.get_extract(PATENT_A, "doc_a"))
        self.assertIsNone(self.store.get_extract(PATENT_B, "doc_a"),
                          "workspace B could read workspace A's document")

    def test_pdf_bytes_are_not_reachable_from_the_wrong_workspace(self):
        self.store.save_pdf(PATENT_A, "doc_a", b"%PDF-1.4 patent A bytes")
        self.assertIsNotNone(self.store.get_pdf_path(PATENT_A, "doc_a"))
        self.assertIsNone(self.store.get_pdf_path(PATENT_B, "doc_a"))

    def test_an_unknown_workspace_reads_as_empty_not_as_everything(self):
        """The dangerous failure would be treating 'no scope' as 'all documents'."""
        self.assertEqual([], self.store.extracts_for_workspace("ws_never_used"))

    def test_the_same_document_id_in_two_workspaces_stays_two_documents(self):
        """Ids are unique per workspace, so a collision must not overwrite."""
        self.store.save_extract(_extract("shared_id", PATENT_A, _fact("applicant.name", "Company A")))
        self.store.save_extract(_extract("shared_id", PATENT_B, _fact("applicant.name", "Company B")))

        self.assertEqual("Company A", self.store.get_extract(PATENT_A, "shared_id").facts[0].value)
        self.assertEqual("Company B", self.store.get_extract(PATENT_B, "shared_id").facts[0].value)

    def test_re_extraction_replaces_only_within_its_own_workspace(self):
        self.store.save_extract(_extract("shared_id", PATENT_A, _fact("applicant.name", "A original")))
        self.store.save_extract(_extract("shared_id", PATENT_B, _fact("applicant.name", "B original")))
        self.store.save_extract(_extract("shared_id", PATENT_A, _fact("applicant.name", "A revised")))

        self.assertEqual("A revised", self.store.get_extract(PATENT_A, "shared_id").facts[0].value)
        self.assertEqual("B original", self.store.get_extract(PATENT_B, "shared_id").facts[0].value)

    def test_document_counts_are_per_workspace(self):
        self.assertEqual(1, self.store.document_count(PATENT_A))
        self.assertEqual(0, self.store.document_count("ws_never_used"))


# ---------------------------------------------------------------- 2. the model

class TestProfileRefusesForeignExtracts(unittest.TestCase):
    """Defence in depth: even a hand-assembled profile cannot mix workspaces."""

    def test_a_scoped_profile_rejects_an_extract_from_elsewhere(self):
        with self.assertRaises(ValidationError):
            PatentProfile(
                workspace_id=PATENT_A,
                extracts=[
                    _extract("doc_a", PATENT_A, _fact("applicant.name", "Company A")),
                    _extract("doc_b", PATENT_B, _fact("applicant.name", "Company B")),
                ],
            )

    def test_the_error_names_the_offending_document(self):
        with self.assertRaises(ValidationError) as caught:
            PatentProfile(workspace_id=PATENT_A, extracts=[_extract("doc_b", PATENT_B)])
        self.assertIn("doc_b", str(caught.exception))

    def test_a_scoped_profile_accepts_its_own_extracts(self):
        profile = PatentProfile(
            workspace_id=PATENT_A,
            extracts=[_extract("doc_a", PATENT_A, _fact("applicant.name", "Company A"))],
        )
        self.assertEqual(["Company A"], [f.value for f in profile.get_facts("applicant.name")])

    def test_add_extract_refuses_a_foreign_document(self):
        profile = PatentProfile(workspace_id=PATENT_A)
        with self.assertRaises(ValueError):
            profile.add_extract(_extract("doc_b", PATENT_B, _fact("applicant.name", "Company B")))
        self.assertEqual([], profile.extracts)

    def test_add_extract_accepts_a_document_from_the_same_workspace(self):
        profile = PatentProfile(workspace_id=PATENT_A)
        profile.add_extract(_extract("doc_a", PATENT_A, _fact("applicant.name", "Company A")))
        self.assertEqual(1, len(profile.extracts))

    def test_two_scoped_profiles_never_share_facts(self):
        profile_a = PatentProfile(
            workspace_id=PATENT_A, extracts=[_extract("doc_a", PATENT_A, _fact("applicant.name", "Company A"))]
        )
        profile_b = PatentProfile(
            workspace_id=PATENT_B, extracts=[_extract("doc_b", PATENT_B, _fact("applicant.name", "Company B"))]
        )
        self.assertEqual(["Company A"], [f.value for f in profile_a.get_facts("applicant.name")])
        self.assertEqual(["Company B"], [f.value for f in profile_b.get_facts("applicant.name")])


# ------------------------------------------------------------------ 3. the API

class TestSuggestionsAreWorkspaceScoped(WorkspaceTestCase):
    """The headline guarantee: suggestions use only the requested workspace."""

    def setUp(self):
        super().setUp()
        self.store.save_extract(_extract(
            "doc_a", PATENT_A,
            _fact("applicant.name", "Company A"),
            _fact("application.number", "111111111111"),
        ))
        self.store.save_extract(_extract(
            "doc_b", PATENT_B,
            _fact("applicant.name", "Company B"),
            _fact("application.number", "222222222222"),
        ))

    def _suggestions(self, workspace_id):
        return app_module.get_suggestions("form_03", workspace_id)["suggestions"]

    def test_workspace_a_sees_only_its_own_applicant(self):
        value = self._suggestions(PATENT_A)["applicant_declaration.applicant_names"]["value"]
        self.assertEqual(["Company A"], value)

    def test_workspace_b_sees_only_its_own_applicant(self):
        value = self._suggestions(PATENT_B)["applicant_declaration.applicant_names"]["value"]
        self.assertEqual(["Company B"], value)

    def test_no_suggestion_is_ever_attributed_to_a_foreign_document(self):
        for workspace, own_document in ((PATENT_A, "doc_a"), (PATENT_B, "doc_b")):
            for path, entry in self._suggestions(workspace).items():
                with self.subTest(workspace=workspace, field=path):
                    self.assertEqual(own_document, entry["fact"]["document_id"])

    def test_the_other_workspaces_values_appear_nowhere_in_the_response(self):
        """Belt and braces: scan the whole payload, not just the fields we expect."""
        payload = str(app_module.get_suggestions("form_03", PATENT_A))
        self.assertNotIn("Company B", payload)
        self.assertNotIn("222222222222", payload)

    def test_the_response_states_which_workspace_it_answered_for(self):
        self.assertEqual(PATENT_A, app_module.get_suggestions("form_03", PATENT_A)["workspace_id"])

    def test_an_empty_workspace_yields_no_suggestions_despite_other_data_existing(self):
        """The critical negative: other workspaces hold data; this one must not borrow it."""
        self.assertEqual({}, self._suggestions("patent_c_empty"))

    def test_deleting_one_workspaces_documents_does_not_affect_another(self):
        for path in (self.uploads / PATENT_A).glob("*"):
            path.unlink()
        reopened = ContentStore()

        self.assertEqual([], reopened.extracts_for_workspace(PATENT_A))
        self.assertEqual(1, len(reopened.extracts_for_workspace(PATENT_B)))


class TestUploadIsWorkspaceScoped(WorkspaceTestCase):
    def test_an_uploaded_document_records_the_workspace_it_was_sent_to(self):
        result = self.upload("doc_a", PATENT_A, context.FORM1_PDF)
        self.assertEqual(PATENT_A, result["workspace_id"])

    def test_the_same_pdf_uploaded_to_two_workspaces_stays_separate(self):
        self.upload("doc_a", PATENT_A, context.FORM1_PDF)
        self.upload("doc_b", PATENT_B, context.FORM1_PDF)

        a = app_module.get_suggestions("form_03", PATENT_A)["suggestions"]
        b = app_module.get_suggestions("form_03", PATENT_B)["suggestions"]

        self.assertEqual("doc_a", a["applicant_declaration.applicant_names"]["fact"]["document_id"])
        self.assertEqual("doc_b", b["applicant_declaration.applicant_names"]["fact"]["document_id"])

    def test_an_upload_to_one_workspace_is_invisible_to_another(self):
        self.upload("doc_a", PATENT_A, context.FORM1_PDF)
        self.assertEqual({}, app_module.get_suggestions("form_03", PATENT_B)["suggestions"])

    def test_a_failed_extraction_still_reports_its_workspace(self):
        upload = UploadFile(
            file=io.BytesIO(b"%PDF-1.4 not really a pdf"), filename="broken.pdf",
            headers={"content-type": "application/pdf"},
        )
        result = asyncio.run(app_module.extract_document(
            file=upload, document_id="d_broken", workspace_id=PATENT_A,
        ))
        self.assertEqual(PATENT_A, result["workspace_id"])


# ----------------------------------------------------------- 4. the filesystem

class TestIdentifiersCannotEscapeTheirWorkspace(WorkspaceTestCase):
    """Ids become path segments, so traversal would be a cross-workspace read."""

    TRAVERSALS = ["../patent_b", "..", "a/b", "a\\b", "/etc/passwd", "", ".", "a.b"]

    def test_traversing_workspace_ids_are_rejected_by_the_store(self):
        for candidate in self.TRAVERSALS:
            with self.subTest(workspace_id=candidate):
                with self.assertRaises(UnsafeIdentifierError):
                    self.store.extracts_for_workspace(candidate)

    def test_traversing_document_ids_are_rejected_by_the_store(self):
        for candidate in self.TRAVERSALS:
            with self.subTest(document_id=candidate):
                with self.assertRaises(UnsafeIdentifierError):
                    self.store.get_extract(PATENT_A, candidate)

    def test_the_suggestions_endpoint_rejects_a_traversing_workspace_id(self):
        with self.assertRaises(HTTPException) as caught:
            app_module.get_suggestions("form_03", "../patent_b")
        self.assertEqual(400, caught.exception.status_code)

    def test_the_extract_endpoint_rejects_a_traversing_workspace_id(self):
        upload = UploadFile(
            file=io.BytesIO(b"%PDF-1.4"), filename="x.pdf",
            headers={"content-type": "application/pdf"},
        )
        with self.assertRaises(HTTPException) as caught:
            asyncio.run(app_module.extract_document(
                file=upload, document_id="d1", workspace_id="../patent_b",
            ))
        self.assertEqual(400, caught.exception.status_code)

    def test_no_file_is_written_outside_the_uploads_directory(self):
        upload = UploadFile(
            file=io.BytesIO(b"%PDF-1.4"), filename="x.pdf",
            headers={"content-type": "application/pdf"},
        )
        with self.assertRaises(HTTPException):
            asyncio.run(app_module.extract_document(
                file=upload, document_id="../escaped", workspace_id=PATENT_A,
            ))
        self.assertEqual([], list(self.uploads.parent.glob("escaped*")))

    def test_each_workspace_owns_a_directory(self):
        self.store.save_pdf(PATENT_A, "doc_a", b"%PDF-1.4")
        self.store.save_extract(_extract("doc_a", PATENT_A))

        for path in (self.uploads / PATENT_A).iterdir():
            self.assertTrue(path.name.startswith("doc_a"))
        self.assertFalse((self.uploads / PATENT_B).exists())


# ---------------------------------------------------------------- 5. restart

class TestOwnershipSurvivesRestart(WorkspaceTestCase):
    def test_workspaces_are_reloaded_separately(self):
        self.store.save_extract(_extract("doc_a", PATENT_A, _fact("applicant.name", "Company A")))
        self.store.save_extract(_extract("doc_b", PATENT_B, _fact("applicant.name", "Company B")))

        reopened = ContentStore()

        self.assertEqual(["doc_a"], [e.document_id for e in reopened.extracts_for_workspace(PATENT_A)])
        self.assertEqual(["doc_b"], [e.document_id for e in reopened.extracts_for_workspace(PATENT_B)])
        self.assertEqual([PATENT_A, PATENT_B], reopened.workspace_ids())

    def test_a_sidecar_that_lies_about_its_workspace_is_not_loaded(self):
        """The directory is the authority; a mismatched sidecar is corrupt."""
        (self.uploads / PATENT_A).mkdir(parents=True, exist_ok=True)
        forged = _extract("doc_forged", PATENT_B, _fact("applicant.name", "Company B"))
        (self.uploads / PATENT_A / "doc_forged.extract.json").write_text(
            forged.model_dump_json(indent=2), encoding="utf-8"
        )

        reopened = ContentStore()

        self.assertEqual([], reopened.extracts_for_workspace(PATENT_A))
        self.assertEqual([], reopened.extracts_for_workspace(PATENT_B))

    def test_unowned_legacy_files_are_not_adopted_into_any_workspace(self):
        """Pre-workspace sidecars have no recorded owner, so guessing is unsafe."""
        legacy = _extract("doc_legacy", "default", _fact("applicant.name", "Legacy Co"))
        (self.uploads / "doc_legacy.extract.json").write_text(
            legacy.model_dump_json(indent=2), encoding="utf-8"
        )

        reopened = ContentStore()
        self.assertEqual([], reopened.workspace_ids())


# ------------------------------------------------------- 6. the absent API

class TestNoUnscopedReadExists(unittest.TestCase):
    """Isolation by construction: there is no bulk read to misuse.

    The previous leak was not a bad check — it was an unscoped accessor that
    made pooling the path of least resistance. This asserts the accessor is
    gone, so the leak cannot be reintroduced by simply calling it again.
    """

    def test_the_store_exposes_no_cross_workspace_bulk_read(self):
        for name in ("all_extracts", "all_documents", "everything"):
            self.assertFalse(
                hasattr(ContentStore, name),
                f"ContentStore.{name}() would allow cross-workspace reads",
            )

    def test_every_public_read_requires_a_workspace(self):
        import inspect

        scoped_reads = ["extracts_for_workspace", "get_extract", "get_pdf_path",
                        "save_pdf", "document_count"]
        for name in scoped_reads:
            with self.subTest(method=name):
                params = list(inspect.signature(getattr(ContentStore, name)).parameters)
                self.assertIn("workspace_id", params,
                              f"ContentStore.{name}() does not name a workspace")

    def test_save_extract_derives_the_workspace_from_the_document_itself(self):
        """No separate argument means no way to file a document elsewhere."""
        import inspect

        params = list(inspect.signature(ContentStore.save_extract).parameters)
        self.assertEqual(["self", "extract"], params)


if __name__ == "__main__":
    unittest.main()
