"""Content store — uploaded PDF bytes and their DocumentExtracts, per workspace.

Every document belongs to exactly one workspace, and that ownership is
structural rather than advisory:

  * On disk, a workspace owns a directory: ``uploads/<workspace_id>/``. A
    document's bytes and its extract sidecar live inside it and nowhere else.
  * In memory, the cache is keyed workspace-first, so a lookup that does not
    name a workspace cannot be expressed.
  * There is deliberately **no** method returning extracts across workspaces.
    Suggestion generation therefore cannot pool two patents into one profile —
    the API to do so does not exist.

Identifiers are validated before they reach the filesystem, so a workspace or
document id can never escape the uploads directory.

Every write is atomic. A file is built in full under a temporary name in its
final directory, flushed to disk, and only then moved into place with
``os.replace()``. Readers therefore observe either the complete previous file or
the complete new one — never a half-written one. This matters most on
re-extraction: a plain truncate-and-write would destroy a perfectly good record
if the process were killed midway, turning an interrupted refresh into data loss.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from models.document_extract import DocumentExtract

_UPLOADS_DIR = Path(__file__).parent.parent / "uploads"

# Workspace and document ids become path segments, so they are restricted to
# characters that cannot traverse ('.', '/' and '\\' are all excluded).
# Frontend ids look like 'doc_ms3d46fw_bfxavr'; workspace ids like 'default'.
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

_EXTRACT_SUFFIX = ".extract.json"

# In-progress writes. The suffix deliberately does not end in '.extract.json',
# so a temp file can never be mistaken for a document by the startup scan.
_TEMP_PREFIX = ".tmp-"
_TEMP_SUFFIX = ".partial"


class UnsafeIdentifierError(ValueError):
    """Raised when a workspace or document id is not usable as a path segment."""


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write `data` to `path` so that `path` is never seen partially written.

    The temporary file is created in the destination directory, not the system
    temp directory: ``os.replace()`` is only atomic within a single filesystem,
    and a cross-device move would silently degrade to a copy.

    If anything fails before the replace, the temporary file is removed and the
    destination is left exactly as it was.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    handle_fd, temp_name = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f"{_TEMP_PREFIX}{path.name}-",
        suffix=_TEMP_SUFFIX,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle_fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            # Get the bytes onto the device before the rename, so a power loss
            # cannot leave the new name pointing at unwritten blocks.
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except BaseException:
        # BaseException, not Exception: a KeyboardInterrupt or SystemExit here
        # must not leave a stray partial file behind either.
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise


def validate_identifier(value: str, label: str) -> str:
    """Return `value` if it is a safe path segment, else raise.

    The single choke point protecting the uploads directory: every public
    method runs its arguments through it before touching the disk.
    """
    if not isinstance(value, str) or not _SAFE_IDENTIFIER.match(value):
        raise UnsafeIdentifierError(
            f"{label} must be 1-128 characters of letters, digits, '_' or '-'; got {value!r}"
        )
    return value


class ContentStore:
    """Workspace-scoped persistence for PDF bytes and DocumentExtracts."""

    def __init__(self) -> None:
        _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        # workspace_id -> { document_id -> DocumentExtract }
        self._extracts: dict[str, dict[str, DocumentExtract]] = {}
        self._sweep_interrupted_writes()
        self._warm_cache_from_disk()

    def _sweep_interrupted_writes(self) -> None:
        """Delete temp files left by a write that never reached its replace.

        Such a file is by definition incomplete and unreferenced — the real
        document is either the untouched previous version or was never created.
        Without this, every interrupted write would leak a file forever, which
        would just trade one kind of debris for another.
        """
        for path in _UPLOADS_DIR.glob(f"*/{_TEMP_PREFIX}*{_TEMP_SUFFIX}"):
            try:
                path.unlink()
            except OSError:  # still held open, or a permissions quirk — harmless
                pass

    # --------------------------------------------------------------- startup

    def _warm_cache_from_disk(self) -> None:
        """Reload every workspace's extracts from their sidecar files.

        Only ``uploads/<workspace>/<doc>.extract.json`` is scanned. Files
        directly under uploads/ are ignored: they predate workspace scoping and
        have no recorded owner, so adopting them into a workspace would be a
        guess — and guessing wrong is exactly the cross-matter contamination
        this store exists to prevent.
        """
        for path in _UPLOADS_DIR.glob(f"*/*{_EXTRACT_SUFFIX}"):
            workspace_id = path.parent.name
            if not _SAFE_IDENTIFIER.match(workspace_id):
                continue
            try:
                extract = DocumentExtract.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001 — corrupted sidecar, skip it
                continue
            # The directory is the authority on ownership. A sidecar claiming a
            # different workspace is corrupt and is not trusted into the cache.
            if extract.workspace_id != workspace_id:
                continue
            self._extracts.setdefault(workspace_id, {})[extract.document_id] = extract

    # ----------------------------------------------------------------- paths

    def _workspace_dir(self, workspace_id: str) -> Path:
        validate_identifier(workspace_id, "workspace_id")
        # _UPLOADS_DIR is read at call time so tests can redirect it.
        return _UPLOADS_DIR / workspace_id

    def _document_path(self, workspace_id: str, document_id: str, suffix: str) -> Path:
        validate_identifier(document_id, "document_id")
        return self._workspace_dir(workspace_id) / f"{document_id}{suffix}"

    # ----------------------------------------------------------------- write

    def save_pdf(self, workspace_id: str, document_id: str, data: bytes) -> Path:
        """Write PDF bytes into the workspace's directory; return the path.

        Atomic: re-uploading over an existing document either fully succeeds or
        leaves the previous bytes intact. The PDFs are the only true source in
        this architecture — everything else is rebuildable from them — so a
        half-overwritten PDF is the one loss that could not be recovered.
        """
        path = self._document_path(workspace_id, document_id, ".pdf")
        _atomic_write_bytes(path, data)
        return path

    def save_extract(self, extract: DocumentExtract) -> None:
        """Persist a DocumentExtract into the workspace it declares.

        The extract's own `workspace_id` decides where it lands, so there is no
        way to file a document under a workspace it does not belong to.

        Atomic: an interrupted re-extraction leaves the previous record whole.
        The in-memory cache is updated only after the file is safely in place,
        so a failed write cannot leave the process claiming facts that are not
        on disk.
        """
        path = self._document_path(extract.workspace_id, extract.document_id, _EXTRACT_SUFFIX)
        _atomic_write_bytes(path, extract.model_dump_json(indent=2).encode("utf-8"))
        self._extracts.setdefault(extract.workspace_id, {})[extract.document_id] = extract

    # ------------------------------------------------------------------ read

    def get_pdf_path(self, workspace_id: str, document_id: str) -> Optional[Path]:
        """Path to a document's PDF, or None if that workspace has no such document."""
        path = self._document_path(workspace_id, document_id, ".pdf")
        return path if path.exists() else None

    def get_extract(self, workspace_id: str, document_id: str) -> Optional[DocumentExtract]:
        """One document's extract, or None if it is not in this workspace."""
        validate_identifier(workspace_id, "workspace_id")
        validate_identifier(document_id, "document_id")
        return self._extracts.get(workspace_id, {}).get(document_id)

    def extracts_for_workspace(self, workspace_id: str) -> list[DocumentExtract]:
        """Every extract in one workspace — the only bulk read that exists.

        There is deliberately no cross-workspace equivalent: suggestion
        generation must name the workspace it is answering for.
        """
        validate_identifier(workspace_id, "workspace_id")
        return list(self._extracts.get(workspace_id, {}).values())

    def workspace_ids(self) -> list[str]:
        """Known workspace ids. Returns identifiers only, never document data."""
        return sorted(self._extracts.keys())

    def document_count(self, workspace_id: str) -> int:
        """How many documents a workspace holds."""
        validate_identifier(workspace_id, "workspace_id")
        return len(self._extracts.get(workspace_id, {}))
