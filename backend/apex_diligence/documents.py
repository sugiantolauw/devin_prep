"""Deterministic text/image extraction from the Board Papers.

Plain-text extraction (docx, pdf text) is fully offline. The scanned Appendix B of the
FY2023 paper is an image, so its *page render* is produced here and handed to Claude vision
in ``narrative.py`` (ADR-0005).
"""

from __future__ import annotations

from pathlib import Path

import fitz  # pymupdf
from docx import Document

from . import BOARD_PAPER_FY2023_PDF, BOARD_PAPER_FY2024_DOCX


def extract_docx_text(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_pdf_text(path: Path = BOARD_PAPER_FY2023_PDF) -> str:
    """Machine-readable text from the FY2023 paper (page 1). Page 2 (Appendix B) is a scan
    and yields no text — that gap is exactly what the vision step fills."""
    doc = fitz.open(str(path))
    return "\n".join(page.get_text() for page in doc)


def render_pdf_page_png(path: Path = BOARD_PAPER_FY2023_PDF, page_index: int = 1) -> bytes:
    """Render one PDF page to PNG bytes (default: page 2 = the scanned Appendix B)."""
    doc = fitz.open(str(path))
    page = doc[page_index]
    pix = page.get_pixmap(dpi=170)
    return pix.tobytes("png")


def fy2024_text() -> str:
    return extract_docx_text(BOARD_PAPER_FY2024_DOCX)


def fy2023_text() -> str:
    return extract_pdf_text(BOARD_PAPER_FY2023_PDF)
