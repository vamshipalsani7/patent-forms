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
from fastapi.responses import Response
from pydantic import BaseModel, Field

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
from packaging.package import PARTS as PACKAGE_PARTS, build_package
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
# Shared helpers
# --------------------------------------------------------------------------

def _load_definition(form_id: str) -> dict:
    """Read one form definition, or fail with a clear HTTP error.

    The single place that turns a form id into a definition, so the suggestions
    and packaging endpoints cannot disagree about where definitions live or how
    a missing one is reported.
    """
    definition_path = _DEFINITIONS_DIR / f"{form_id}.definition.json"
    if not definition_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No definition found for '{form_id}' at {definition_path}.",
        )
    try:
        return json.loads(definition_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Definition JSON invalid: {exc}") from exc


def _suggestions_for(definition: dict, workspace_id: str, decisions: dict) -> dict:
    """Mapper suggestions for one workspace, as plain dicts with a source label."""
    extracts = _store.extracts_for_workspace(workspace_id)
    profile = PatentProfile(workspace_id=workspace_id, extracts=extracts)
    suggestions_map = _mapper.get_suggestions(definition, profile, overrides=decisions)

    out: dict = {}
    for path, s in suggestions_map.items():
        payload = s.to_dict()
        payload["source_label"] = source_type_label(s.fact.source_type)
        out[path] = payload
    return out


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

    definition = _load_definition(form_id)
    # The friendly source name the review UI shows ("From Complete
    # Specification") travels with each suggestion, so the interface never has
    # to render a raw sourceType.
    return {
        "form_id": form_id,
        "workspace_id": workspace_id,
        "suggestions": _suggestions_for(definition, workspace_id, decisions),
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


# --------------------------------------------------------------------------
# Filing package endpoint
# --------------------------------------------------------------------------

class FilingPackageRequest(BaseModel):
    """What the review screen knows and the package needs.

    `values` and `visible_paths` come from the renderer, so the filed document
    contains exactly the form the user reviewed. `counts` are the review's own
    numbers, so the filing summary reports what the user saw rather than a second
    opinion computed here.
    """

    workspace_id: str
    values: dict = Field(default_factory=dict)
    visible_paths: list = Field(default_factory=list)
    counts: dict = Field(default_factory=dict)
    overrides: dict = Field(default_factory=dict)


@app.post("/api/package/{form_id}")
def build_filing_package(form_id: str, request: FilingPackageRequest, part: str = "zip"):
    """Prepare the filing package for a completed form and return one part of it.

    The package is always built as a whole — official PDF, editable DOCX, filing
    summary and provenance report — so the user never has to choose what to
    generate. `part` selects which of them (or the ZIP of all four) is returned
    by this request.

    Provenance is derived from the same mapper suggestions the review used, and
    the document list from the same workspace summary, so the paperwork agrees
    with what the user saw on screen.

    Args:
        form_id: e.g. 'form_18'.
        part:    'zip' (default) | 'pdf' | 'docx' | 'summary' | 'provenance'.

    Returns:
        The file, with a professional download filename.
    """
    try:
        validate_identifier(request.workspace_id, "workspace_id")
    except UnsafeIdentifierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if part not in PACKAGE_PARTS + ("zip",):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown package part '{part}'. "
                   f"Expected one of: {', '.join(PACKAGE_PARTS + ('zip',))}.",
        )

    definition = _load_definition(form_id)
    suggestions = _suggestions_for(definition, request.workspace_id, request.overrides)

    extracts = _store.extracts_for_workspace(request.workspace_id)
    profile = PatentProfile(workspace_id=request.workspace_id, extracts=extracts)
    summary = build_workspace_summary(profile)
    # Name the documents the way the workspace named them, and only those that
    # actually contributed something.
    documents = [
        d["document_type"] for d in summary.get("documents", [])
        if d.get("fact_count")
    ]

    package = build_package(
        definition=definition,
        values=request.values,
        visible_paths=request.visible_paths,
        counts=request.counts,
        documents=documents,
        suggestions=suggestions,
    )
    chosen = package[part]
    return Response(
        content=chosen["bytes"],
        media_type=chosen["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{chosen["filename"]}"',
            # The browser must be able to read the filename it should save as.
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )