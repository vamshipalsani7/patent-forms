"""Service layer for the Patent Forms backend.

Services orchestrate the domain packages (``extractor``, ``extractors``,
``models``) and expose high-level operations to the API layer in ``app.py``.
"""

from __future__ import annotations

from services.extraction_service import ExtractionService

__all__ = ["ExtractionService"]
