"""Atomic writes — an interrupted write must never destroy a valid file.

The failure this guards against is not hypothetical. A plain truncate-and-write
opens the destination and empties it *before* the new bytes arrive, so a process
killed midway leaves a file that is neither the old version nor the new one. On
re-extraction that turns a routine refresh into permanent data loss: the good
record is gone, and nothing in the pipeline rebuilds it.

Each test drives a real write and interrupts it at a specific point, then asks
the only question that matters — what does a restart see?

Interruption is simulated by making a step of the write raise, which reproduces
the on-disk state a kill produces at that moment:

  * `os.fsync` raising   -> temp file holds data, replace never ran
  * `os.replace` raising -> temp file complete, destination never swapped

A real SIGKILL cannot be caught mid-write inside a test, but the resulting
filesystem state is what these reproduce, and that state is what the next
startup has to survive.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import context  # noqa: F401  — sets sys.path

import storage.content_store as content_store_module
from models.document_extract import DocumentExtract
from models.fact import Fact
from storage.content_store import ContentStore

WORKSPACE = "patent_a"

ORIGINAL_PDF = b"%PDF-1.4 the original document bytes"
REPLACEMENT_PDF = b"%PDF-1.4 a completely different and much longer replacement document"


def _extract(document_id, applicant, workspace_id=WORKSPACE):
    return DocumentExtract(
        document_id=document_id,
        workspace_id=workspace_id,
        source_type="form1",
        original_filename=f"{document_id}.pdf",
        page_count=1,
        facts=[Fact(
            key="applicant.name", value=applicant, document_id=document_id,
            source_type="form1", page=1, confidence=0.8,
            method="anchor", extractor_version="form1@1",
        )],
        extractor_version="form1@1",
    )


def interrupt_at(step):
    """Make one step of the atomic write fail, as a kill at that moment would."""
    return mock.patch(f"storage.content_store.os.{step}", side_effect=OSError("process killed"))


class AtomicWriteTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_dir = content_store_module._UPLOADS_DIR
        content_store_module._UPLOADS_DIR = Path(self._tmp.name)
        self.uploads = Path(self._tmp.name)
        self.store = ContentStore()

    def tearDown(self):
        content_store_module._UPLOADS_DIR = self._original_dir
        self._tmp.cleanup()

    @property
    def workspace_dir(self):
        return self.uploads / WORKSPACE

    def temp_files(self):
        if not self.workspace_dir.exists():
            return []
        return [p for p in self.workspace_dir.iterdir() if p.name.endswith(".partial")]


# ------------------------------------------------------- PDFs (the only truth)

class TestInterruptedPdfOverwrite(AtomicWriteTestCase):
    """PDFs are the source of truth — everything else rebuilds from them."""

    def setUp(self):
        super().setUp()
        self.path = self.store.save_pdf(WORKSPACE, "doc_1", ORIGINAL_PDF)

    def test_original_survives_an_interruption_before_the_replace(self):
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_pdf(WORKSPACE, "doc_1", REPLACEMENT_PDF)

        self.assertEqual(ORIGINAL_PDF, self.path.read_bytes())

    def test_original_survives_an_interruption_while_the_data_is_being_written(self):
        with interrupt_at("fsync"), self.assertRaises(OSError):
            self.store.save_pdf(WORKSPACE, "doc_1", REPLACEMENT_PDF)

        self.assertEqual(ORIGINAL_PDF, self.path.read_bytes())

    def test_the_file_is_never_left_truncated(self):
        """The specific failure of truncate-and-write: a shorter, broken file."""
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_pdf(WORKSPACE, "doc_1", REPLACEMENT_PDF)

        self.assertEqual(len(ORIGINAL_PDF), self.path.stat().st_size)

    def test_repeated_interruptions_never_erode_the_original(self):
        for _ in range(5):
            with interrupt_at("replace"), self.assertRaises(OSError):
                self.store.save_pdf(WORKSPACE, "doc_1", REPLACEMENT_PDF)

        self.assertEqual(ORIGINAL_PDF, self.path.read_bytes())

    def test_a_successful_write_after_an_interruption_still_works(self):
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_pdf(WORKSPACE, "doc_1", REPLACEMENT_PDF)

        self.store.save_pdf(WORKSPACE, "doc_1", REPLACEMENT_PDF)
        self.assertEqual(REPLACEMENT_PDF, self.path.read_bytes())

    def test_an_interrupted_first_write_leaves_no_file_at_all(self):
        """Better absent than present-and-corrupt: absent is detectable."""
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_pdf(WORKSPACE, "doc_new", REPLACEMENT_PDF)

        self.assertIsNone(self.store.get_pdf_path(WORKSPACE, "doc_new"))


# ------------------------------------------------------------ extract sidecars

class TestInterruptedExtractOverwrite(AtomicWriteTestCase):
    """The re-extraction data-loss window this change exists to close."""

    def setUp(self):
        super().setUp()
        self.store.save_extract(_extract("doc_1", "Acme Innovations Private Limited"))

    def _reopened(self):
        """What the next process start sees."""
        return ContentStore()

    def test_an_interrupted_re_extraction_preserves_the_previous_record(self):
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_extract(_extract("doc_1", "Corrupted Partial Write"))

        record = self._reopened().get_extract(WORKSPACE, "doc_1")
        self.assertIsNotNone(record, "the previously valid record was destroyed")
        self.assertEqual("Acme Innovations Private Limited", record.facts[0].value)

    def test_the_surviving_sidecar_is_still_valid_json(self):
        with interrupt_at("fsync"), self.assertRaises(OSError):
            self.store.save_extract(_extract("doc_1", "Corrupted Partial Write"))

        # Parses without the warm-load's corrupt-file fallback being needed.
        path = self.workspace_dir / f"doc_1{content_store_module._EXTRACT_SUFFIX}"
        DocumentExtract.model_validate_json(path.read_text(encoding="utf-8"))

    def test_the_document_does_not_vanish_from_its_workspace(self):
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_extract(_extract("doc_1", "Corrupted Partial Write"))

        self.assertEqual(
            ["doc_1"],
            [e.document_id for e in self._reopened().extracts_for_workspace(WORKSPACE)],
        )

    def test_suggestions_can_still_be_generated_after_an_interruption(self):
        """The user-visible consequence: the form still pre-fills."""
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_extract(_extract("doc_1", "Corrupted Partial Write"))

        import app as app_module
        original_store = app_module._store
        app_module._store = self._reopened()
        try:
            suggestions = app_module.get_suggestions("form_03", WORKSPACE)["suggestions"]
        finally:
            app_module._store = original_store

        self.assertEqual(
            ["Acme Innovations Private Limited"],
            suggestions["applicant_declaration.applicant_names"]["value"],
        )

    def test_the_in_memory_cache_does_not_diverge_from_disk(self):
        """A failed write must not leave the process claiming facts it never saved."""
        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_extract(_extract("doc_1", "Corrupted Partial Write"))

        cached = self.store.get_extract(WORKSPACE, "doc_1").facts[0].value
        on_disk = self._reopened().get_extract(WORKSPACE, "doc_1").facts[0].value
        self.assertEqual(on_disk, cached)


# ----------------------------------------------------------- temp file hygiene

class TestTemporaryFiles(AtomicWriteTestCase):
    def test_a_successful_write_leaves_no_temp_file(self):
        self.store.save_pdf(WORKSPACE, "doc_1", ORIGINAL_PDF)
        self.store.save_extract(_extract("doc_1", "Acme Ltd"))
        self.assertEqual([], self.temp_files())

    def test_an_interrupted_write_cleans_up_its_own_temp_file(self):
        self.store.save_pdf(WORKSPACE, "doc_1", ORIGINAL_PDF)

        with interrupt_at("replace"), self.assertRaises(OSError):
            self.store.save_pdf(WORKSPACE, "doc_1", REPLACEMENT_PDF)

        self.assertEqual([], self.temp_files())

    def test_a_temp_file_orphaned_by_a_kill_is_swept_on_restart(self):
        """Cleanup cannot run if the process dies outright, so startup does it."""
        self.store.save_pdf(WORKSPACE, "doc_1", ORIGINAL_PDF)
        orphan = self.workspace_dir / ".tmp-doc_1.pdf-abc123.partial"
        orphan.write_bytes(b"half written")

        ContentStore()

        self.assertFalse(orphan.exists(), "an orphaned temp file survived restart")

    def test_sweeping_does_not_touch_real_documents(self):
        self.store.save_pdf(WORKSPACE, "doc_1", ORIGINAL_PDF)
        self.store.save_extract(_extract("doc_1", "Acme Ltd"))
        (self.workspace_dir / ".tmp-doc_1.pdf-abc123.partial").write_bytes(b"half")

        reopened = ContentStore()

        self.assertEqual(ORIGINAL_PDF, reopened.get_pdf_path(WORKSPACE, "doc_1").read_bytes())
        self.assertEqual("Acme Ltd", reopened.get_extract(WORKSPACE, "doc_1").facts[0].value)

    def test_a_temp_file_is_never_loaded_as_a_document(self):
        """Its name must not satisfy the '*.extract.json' startup scan."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        forged = _extract("doc_ghost", "Should Never Appear")
        (self.workspace_dir / ".tmp-doc_ghost.extract.json-abc.partial").write_text(
            forged.model_dump_json(), encoding="utf-8"
        )

        reopened = ContentStore()

        self.assertEqual([], reopened.extracts_for_workspace(WORKSPACE))


# ------------------------------------------------------- atomicity preconditions

class TestAtomicityPreconditions(AtomicWriteTestCase):
    """os.replace() is only atomic under conditions this asserts hold."""

    def test_the_temp_file_is_created_beside_its_destination(self):
        """A cross-filesystem move degrades to a non-atomic copy."""
        seen = {}
        real_mkstemp = content_store_module.tempfile.mkstemp

        def spy(*args, **kwargs):
            seen["dir"] = kwargs.get("dir")
            return real_mkstemp(*args, **kwargs)

        with mock.patch.object(content_store_module.tempfile, "mkstemp", spy):
            self.store.save_pdf(WORKSPACE, "doc_1", ORIGINAL_PDF)

        self.assertEqual(str(self.workspace_dir), seen["dir"],
                         "temp file must share a filesystem with its destination")

    def test_the_write_is_flushed_before_the_replace(self):
        """Ordering: rename must not publish a name pointing at unwritten blocks."""
        calls = []
        with mock.patch.object(content_store_module.os, "fsync",
                               side_effect=lambda fd: calls.append("fsync")), \
             mock.patch.object(content_store_module.os, "replace",
                               side_effect=lambda a, b: calls.append("replace")):
            self.store.save_pdf(WORKSPACE, "doc_1", ORIGINAL_PDF)

        self.assertEqual(["fsync", "replace"], calls)

    def test_both_write_paths_go_through_the_atomic_helper(self):
        """Neither save_pdf nor save_extract may write in place."""
        import inspect

        for method in (ContentStore.save_pdf, ContentStore.save_extract):
            with self.subTest(method=method.__name__):
                body = inspect.getsource(method)
                self.assertIn("_atomic_write_bytes", body)
                self.assertNotIn("write_bytes(", body.replace("_atomic_write_bytes", ""))
                self.assertNotIn("write_text(", body)


if __name__ == "__main__":
    unittest.main()
