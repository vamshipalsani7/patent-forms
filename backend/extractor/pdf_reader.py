"""PDF reading stage of the extraction pipeline.

Responsible only for turning a PDF file into raw text (and, in future,
positional/layout metadata). It performs no interpretation or classification
of the content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


class PDFReader:
    """Reads raw text from a PDF file.

    Extraction logic is intentionally not implemented yet. Concrete PDF parsing
    (e.g. via ``pypdf``, ``pdfplumber`` or an OCR fallback) will be added here.
    """

    def read(self, file_path: Union[str, Path]) -> str:
        """Return the raw text content of the given PDF.

        Args:
            file_path: Path to the PDF file on disk.

        Returns:
            The extracted raw text of the document.

        Raises:
            NotImplementedError: Always, until extraction is implemented.
        """
        raise NotImplementedError("PDF text extraction is not implemented yet.")
