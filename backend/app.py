"""Patent Forms FastAPI backend.

Endpoints:
  GET  /                               health check (unchanged)
  POST /upload                         legacy upload stub (unchanged)
  POST /api/extract                    extract a PDF → DocumentExtract
  GET  /api/suggestions/{form_id}      map stored extracts to form fields
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend/ packages are importable when the process is started from
# the project root (uvicorn backend.app:app) or from inside backend/.
_BACKEND_DIR = Path(__file__).parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from autofill.mapper import AutofillMapper
from extractor.classifier import DocumentClassifier
from extractor.pdf_reader import PDFReader
from extractor.profile_builder import ProfileBuilder
from models.patent_profile import PatentProfile
from storage.content_store import ContentStore

# --------------------------------------------------------------------------
# Process-scoped singletons
# --------------------------------------------------------------------------

_store = ContentStore()
_reader = PDFReader()
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
):
    """Upload a PDF, extract structured Facts, persist a DocumentExtract.

    Args (multipart/form-data):
        file:        The PDF bytes.
        document_id: The documentStore id assigned by the frontend on upload.

    Returns:
        The DocumentExtract as JSON, including all facts and their provenance.
        On failure, returns { error, document_id } with an appropriate status.
    """
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- persist bytes ---
    pdf_path = _store.save_pdf(document_id, data)

    # --- pipeline ---
    try:
        page_texts = _reader.read_pages(pdf_path)
        full_text = "\n\n".join(t for _, t in page_texts)
        doc_type = _classifier.classify(full_text)

        extract = _profile_builder.build(
            file_path=pdf_path,
            document_id=document_id,
            original_filename=file.filename or "unknown.pdf",
            document_type=doc_type,
            page_texts=page_texts,
        )
    except Exception as exc:
        # Return a partial response rather than a 500 — the frontend handles
        # extraction failures gracefully (no suggestions shown, form still usable).
        return {
            "document_id": document_id,
            "source_type": "unknown",
            "facts": [],
            "error": str(exc),
        }

    _store.save_extract(extract)
    return extract.model_dump()


# --------------------------------------------------------------------------
# Suggestions endpoint
# --------------------------------------------------------------------------

@app.get("/api/suggestions/{form_id}")
def get_suggestions(form_id: str):
    """Map all stored DocumentExtracts to the fields of a given form.

    Uses the AutofillMapper, which reads autofill.sources[] from the definition
    in authored preference order — no per-form logic lives in this endpoint.

    Args:
        form_id: e.g. 'form_03'  (matches docs/specifications/definitions/<form_id>.definition.json)

    Returns:
        { form_id, suggestions: { "section_id.field_id": { value, fact } } }
    """
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

    extracts = _store.all_extracts()
    profile = PatentProfile(extracts=extracts)
    suggestions_map = _mapper.get_suggestions(definition, profile)

    return {
        "form_id": form_id,
        "suggestions": {
            path: s.to_dict() for path, s in suggestions_map.items()
        },
    }