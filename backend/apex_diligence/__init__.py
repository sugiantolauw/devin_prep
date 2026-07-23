"""Apex financial due-diligence engine.

Python owns every number (ADR-0002). The package is organised as a pipeline:
ingest -> metrics -> anomalies/normalisation -> evidence pack -> LLM reconciliation
under a numeric guardrail.
"""

from pathlib import Path

# Repo-root-relative data directory (backend/../data).
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
INCOME_STATEMENT_CSV = DATA_DIR / "income_statement.csv"
BOARD_PAPER_FY2023_PDF = DATA_DIR / "ApexElectronics_FY2023_BoardPaper.pdf"
BOARD_PAPER_FY2024_DOCX = DATA_DIR / "ApexElectronics_FY2024_BoardPaper.docx"

__all__ = [
    "DATA_DIR",
    "INCOME_STATEMENT_CSV",
    "BOARD_PAPER_FY2023_PDF",
    "BOARD_PAPER_FY2024_DOCX",
]
