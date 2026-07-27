"""PDF reading stage of the extraction pipeline.

Turns a PDF file into raw text (per-page) and a total page count.
Uses pdfplumber for the text layer. OCR is a future Tier 4 fallback —
the architecture doc explicitly defers it to after the deterministic path works.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


class PDFReader:
    """Reads raw text from a PDF file using pdfplumber (text-layer only)."""

    def read(self, file_path: Union[str, Path]) -> str:
        """Return full raw text of the PDF, pages joined by newlines."""
        pages = self.read_pages(file_path)
        return "\n\n".join(text for _, text in pages if text)

    def read_pages(self, file_path: Union[str, Path]) -> list[tuple[int, str]]:
        """Return [(page_number_1indexed, page_text), …] for each page.

        Empty pages are included (as empty strings) so page numbers in the
        returned tuples match the physical PDF page numbers exactly.
        """
        try:
            import pdfplumber  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "pdfplumber is required for PDF text extraction. "
                "Install it with: pip install pdfplumber"
            ) from exc

        results: list[tuple[int, str]] = []
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                results.append((i, text))
        return results
