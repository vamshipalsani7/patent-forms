"""Patent Forms FastAPI backend.

Endpoints:
  GET  /                               health check (unchanged)
  POST /upload                         legacy upload stub (unchanged)
  POST /api/extract                    extract a PDF → DocumentExtract
  GET  /api/suggestions/{form_id}      map a workspace's extracts to form fields

Both /api endpoints require an explicit `workspace_id`. Documents for different
patents must never merge into one profile, so there is no implicit or default
workspace at the API boundary — a caller that does not say which patent it is
working on gets a 422 rather than a guess.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend/ packages are importable when the process is started from
# the project root (uvicorn backend.app:app) or from inside backend/.
_BACKEND_DIR = Path(__file__).parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from autofill.mapper import AutofillMapper
from extractor.classifier import DocumentClassifier
from extractor.document_reader import (
    SUPPORTED_EXTENSIONS,
    DocumentReader,
    UnsupportedDocumentError,
)
from extractor.profile_builder import ProfileBuilder
from models.patent_profile import PatentProfile
from storage.content_store import ContentStore, UnsafeIdentifierError, validate_identifier
from workspace.summary import build_workspace_summary, source_type_label

# --------------------------------------------------------------------------
# Process-scoped singletons
# --------------------------------------------------------------------------

_store = ContentStore()
_reader = DocumentReader()
_classifier = DocumentClassifier()
_profile_builder = ProfileBuilder()
_mapper = AutofillMapper()

_DEFINITIONS_DIR = _BACKEND_DIR.parent / "docs" / "specifications" / "definitions"

# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------

app = FastAPI(title="Patent Forms API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Existing endpoints (unchanged)
# --------------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "Patent Forms Backend Running"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    return {"filename": file.filename, "message": "PDF received successfully"}


# --------------------------------------------------------------------------
# Extraction endpoint
# --------------------------------------------------------------------------

@app.post("/api/extract")
async def extract_document(
    file: UploadFile = File(...),
    document_id: str = Form(...),
    workspace_id: str = Form(...),
):
    """Upload a source document into one workspace, extract Facts, persist it.

    Accepts the formats patent professionals actually hold — PDF, DOCX, DOC and
    TXT — not only PDF. The file type changes exactly one thing: how the bytes
    become text (DocumentReader). Classification and extraction are format-blind
    and run identically whatever was uploaded.

    Document type is detected from the document's CONTENT, never its filename:
    the classifier reads the extracted text. A specification named
    "final_v3.docx" is recognised as a specification the same way its PDF would be.

    Args (multipart/form-data):
        file:         The document bytes (PDF/DOCX/DOC/TXT).
        document_id:  The documentStore id assigned by the frontend on upload.
        workspace_id: The workspace (patent matter) this document belongs to.
                      Required — the document is filed here and nowhere else.

    Returns:
        The DocumentExtract as JSON, including all facts and their provenance.
        On a document that cannot be read (an unreadable .doc, an image-only
        scan), returns a valid extract with no facts and a `warning` — never a
        500 — so the workspace stays usable.
    """
    try:
        validate_identifier(workspace_id, "workspace_id")
        validate_identifier(document_id, "document_id")
    except UnsafeIdentifierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix or file.filename}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
            ),
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- persist bytes inside the workspace, keyed by their true type ---
    stored_path = _store.save_document(workspace_id, document_id, data, suffix)

    # --- pipeline: read (format-specific) → classify → extract (format-blind) ---
    try:
        page_texts = _reader.read_pages(stored_path, filename=file.filename)
        full_text = "\n\n".join(t for _, t in page_texts)

        # An empty read means the document could not be turned into text — an
        # unreadable legacy .doc, or an image-only scan with no text layer.
        # Persist an honest, factless extract so the UI can say so per document.
        if not full_text.strip():
            extract = _empty_extract(
                document_id, workspace_id, file.filename, len(page_texts)
            )
            _store.save_extract(extract)
            payload = extract.model_dump()
            payload["source_type_label"] = source_type_label(extract.source_type)
            payload["warning"] = (
                "No text could be read from this document. If it is a scan or a "
                "legacy .doc file, try uploading a PDF or DOCX version."
            )
            return payload

        doc_type = _classifier.classify(full_text)
        extract = _profile_builder.build(
            file_path=stored_path,
            document_id=document_id,
            original_filename=file.filename or f"unknown{suffix}",
            document_type=doc_type,
            page_texts=page_texts,
        )
    except Exception as exc:
        # Return a partial response rather than a 500 — the frontend handles
        # extraction failures gracefully (document shown, marked not-extracted).
        return {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "source_type": "unknown",
            "original_filename": file.filename,
            "facts": [],
            "error": str(exc),
        }

    # The builder is workspace-agnostic by design; ownership is stamped here,
    # at the boundary that actually knows which workspace the request named.
    extract.workspace_id = workspace_id

    _store.save_extract(extract)
    payload = extract.model_dump()
    # Friendly type name, from the same map the workspace summary uses, so the
    # document list can show "Patent Certificate" without a second label table
    # (and without ever exposing the raw sourceType to the interface).
    payload["source_type_label"] = source_type_label(extract.source_type)
    return payload


def _empty_extract(document_id, workspace_id, filename, page_count):
    """A valid, factless DocumentExtract for an unreadable document."""
    from models.document_extract import DocumentExtract

    return DocumentExtract(
        document_id=document_id,
        workspace_id=workspace_id,
        source_type="unknown",
        original_filename=filename or "unknown",
        page_count=page_count,
        facts=[],
        extractor_version="none@0",
    )


# --------------------------------------------------------------------------
# Suggestions endpoint
# --------------------------------------------------------------------------

@app.get("/api/suggestions/{form_id}")
def get_suggestions(form_id: str, workspace_id: str, overrides: Optional[str] = None):
    """Map ONE workspace's DocumentExtracts to the fields of a given form.

    Uses the AutofillMapper, which reads autofill.sources[] from the definition
    in authored preference order — no per-form logic lives in this endpoint.

    Only documents belonging to `workspace_id` are consulted. The profile is
    additionally constructed with that workspace id, so if a foreign extract
    ever reached this point the model would reject it rather than suggest from
    another patent.

    Args:
        form_id:      e.g. 'form_03' (matches docs/specifications/definitions/).
        workspace_id: Required query parameter naming the patent matter.
        overrides:    Optional JSON object, {vocabKey: value}, carrying the
                      user's Patent Workspace decisions (resolved conflicts and
                      typed-in missing values). The form pre-fills with what the
                      user reviewed and settled on, not just the raw extractions.
                      Malformed JSON is ignored rather than failing the form.

    Returns:
        { form_id, workspace_id, suggestions: { "section_id.field_id": {value, fact} } }
    """
    try:
        validate_identifier(workspace_id, "workspace_id")
    except UnsafeIdentifierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    decisions: dict = {}
    if overrides:
        try:
            parsed = json.loads(overrides)
            if isinstance(parsed, dict):
                decisions = parsed
        except (json.JSONDecodeError, TypeError):
            # A garbled overrides param must never take the form down with it —
            # fall back to extractions only.
            decisions = {}

    definition_path = _DEFINITIONS_DIR / f"{form_id}.definition.json"
    if not definition_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No definition found for '{form_id}' at {definition_path}.",
        )

    try:
        definition = json.loads(definition_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Definition JSON invalid: {exc}") from exc

    extracts = _store.extracts_for_workspace(workspace_id)
    profile = PatentProfile(workspace_id=workspace_id, extracts=extracts)
    suggestions_map = _mapper.get_suggestions(definition, profile, overrides=decisions)

    return {
        "form_id": form_id,
        "workspace_id": workspace_id,
        "suggestions": {
            path: s.to_dict() for path, s in suggestions_map.items()
        },
    }


# --------------------------------------------------------------------------
# Patent Workspace endpoint
# --------------------------------------------------------------------------

@app.get("/api/workspace/{workspace_id}")
def get_workspace(workspace_id: str):
    """Consolidated view of one patent matter: documents + merged facts.

    This is the Patent Workspace's data source — form-independent, unlike
    /api/suggestions. It reports every uploaded document with its detected type
    and extraction status, the extracted facts grouped into the sections a
    patent professional reads (Title, Applicants, Inventors, …) with full
    provenance, the core information still missing, and any values the documents
    disagree on.

    Only this workspace's documents are consulted; the profile is built scoped
    to it, so a foreign extract could never leak into the summary.

    Args:
        workspace_id: The patent matter to summarise.

    Returns:
        The workspace summary (see workspace.summary.build_workspace_summary).
    """
    try:
        validate_identifier(workspace_id, "workspace_id")
    except UnsafeIdentifierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    extracts = _store.extracts_for_workspace(workspace_id)
    profile = PatentProfile(workspace_id=workspace_id, extracts=extracts)
    return build_workspace_summary(profile)