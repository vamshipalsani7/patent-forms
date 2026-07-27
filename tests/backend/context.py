"""Shared test context: puts backend/ on sys.path and locates fixtures.

Backend modules import each other as top-level packages (`from models.fact
import Fact`), which means backend/ itself must be the import root — the same
way uvicorn runs it. Importing this module from any test file establishes that.
"""

from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = TESTS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FIXTURES_DIR = TESTS_DIR / "fixtures"

DEFINITIONS_DIR = PROJECT_ROOT / "docs" / "specifications" / "definitions"
FORM1_PDF = FIXTURES_DIR / "form1_sample.pdf"
NON_FORM_PDF = FIXTURES_DIR / "not_a_patent_form.pdf"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# --- Expected values encoded in tests/fixtures/form1_sample.pdf --------------
# Kept here so a fixture change fails in one obvious place rather than in a
# dozen scattered assertions.
FIXTURE_APPLICANT_NAME = "Acme Innovations Private Limited"
FIXTURE_APPLICATION_NUMBER = "202211012345"
FIXTURE_INVENTION_TITLE = "A Novel Method for Efficient Solar Panel Cooling"
FIXTURE_SIGNATORY_NAME = "Rajesh Kumar"
