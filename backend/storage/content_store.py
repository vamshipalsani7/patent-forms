"""Content store — keeps uploaded PDF bytes and their DocumentExtracts on disk.

Design: every PDF is saved as backend/uploads/<document_id>.pdf (not content-
addressed yet; Phase 1 will add sha256-keying). Its DocumentExtract is saved as
backend/uploads/<document_id>.extract.json so re-extraction never requires a
re-upload.

The in-memory cache (dict) is populated on startup by scanning the uploads dir
and reloaded lazily — safe for a single-user desktop process with one worker.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from models.document_extract import DocumentExtract

_UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


class ContentStore:
    """Manages PDF bytes and DocumentExtract persistence."""

    def __init__(self) -> None:
        _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        # Warm the in-memory extract cache from disk
        self._extracts: dict[str, DocumentExtract] = {}
        for path in _UPLOADS_DIR.glob("*.extract.json"):
            doc_id = path.stem.replace(".extract", "")
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._extracts[doc_id] = DocumentExtract.model_validate(data)
            except Exception:  # noqa: BLE001 — corrupted sidecar, skip it
                pass

    # ---------------------------------------------------------------- write

    def save_pdf(self, document_id: str, data: bytes) -> Path:
        """Write PDF bytes to disk; return the path."""
        path = _UPLOADS_DIR / f"{document_id}.pdf"
        path.write_bytes(data)
        return path

    def save_extract(self, extract: DocumentExtract) -> None:
        """Persist a DocumentExtract as a JSON sidecar and update the cache."""
        path = _UPLOADS_DIR / f"{extract.document_id}.extract.json"
        path.write_text(
            extract.model_dump_json(indent=2), encoding="utf-8"
        )
        self._extracts[extract.document_id] = extract

    # ---------------------------------------------------------------- read

    def get_pdf_path(self, document_id: str) -> Optional[Path]:
        path = _UPLOADS_DIR / f"{document_id}.pdf"
        return path if path.exists() else None

    def get_extract(self, document_id: str) -> Optional[DocumentExtract]:
        return self._extracts.get(document_id)

    def all_extracts(self) -> list[DocumentExtract]:
        return list(self._extracts.values())
