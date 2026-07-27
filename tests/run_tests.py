#!/usr/bin/env python3
"""Run the whole test suite — backend (Python) and frontend (Node) — in one go.

    python tests/run_tests.py

Deliberately depends on nothing that is not already installed: the backend tests
use the stdlib `unittest` (not pytest) and the frontend tests use Node's built-in
`node:test` runner. There is nothing to `pip install` or `npm install` first.

Options:
    -v, --verbose     per-test output instead of a summary
    --backend-only    skip the Node suite
    --frontend-only   skip the Python suite
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_TESTS = TESTS_DIR / "backend"
FRONTEND_TESTS = TESTS_DIR / "frontend"


def _rule(title: str) -> None:
    # unittest writes to stderr; flush stdout so headers stay in order, and
    # keep the text ASCII so it renders on a default Windows console codepage.
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}", flush=True)


def run_backend(verbose: bool) -> tuple[bool, str]:
    """Discover and run the Python suite. Returns (passed, summary)."""
    _rule("BACKEND  (Python / unittest)")

    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(BACKEND_TESTS),
        pattern="test_*.py",
        top_level_dir=str(BACKEND_TESTS),
    )
    result = unittest.TextTestRunner(verbosity=2 if verbose else 1).run(suite)

    broken = len(result.failures) + len(result.errors)
    summary = f"{result.testsRun} tests, {broken} failed"
    return broken == 0, summary


def run_frontend(verbose: bool) -> tuple[bool | None, str]:
    """Run the Node suite. Returns (passed | None if unavailable, summary)."""
    _rule("FRONTEND  (Node / node:test)")

    node = shutil.which("node")
    if node is None:
        print("Node.js was not found on PATH - skipping the frontend suite.")
        print("The app-shell tests (draft persistence, workspace isolation,")
        print("suggested-vs-user-edited separation) did NOT run.")
        return None, "skipped - node not installed"

    test_files = sorted(FRONTEND_TESTS.glob("*.test.mjs"))
    if not test_files:
        print("No *.test.mjs files found.")
        return False, "no test files found"

    # Node's --test does not reliably accept a directory on Windows, so the
    # files are enumerated explicitly.
    command = [node, "--test"]
    if not verbose:
        command.append("--test-reporter=dot")
    command += [str(path) for path in test_files]

    completed = subprocess.run(command, cwd=str(TESTS_DIR.parent))
    passed = completed.returncode == 0
    return passed, f"{len(test_files)} file(s), exit {completed.returncode}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--backend-only", action="store_true")
    parser.add_argument("--frontend-only", action="store_true")
    args = parser.parse_args(argv)

    results: list[tuple[str, bool | None, str]] = []

    if not args.frontend_only:
        passed, summary = run_backend(args.verbose)
        results.append(("backend", passed, summary))

    if not args.backend_only:
        passed, summary = run_frontend(args.verbose)
        results.append(("frontend", passed, summary))

    _rule("SUMMARY")
    for name, passed, summary in results:
        label = {True: "PASS", False: "FAIL", None: "SKIP"}[passed]
        print(f"  {label}  {name:<10} {summary}")

    failed = [name for name, passed, _ in results if passed is False]
    skipped = [name for name, passed, _ in results if passed is None]

    print()
    if failed:
        print(f"FAILED - {', '.join(failed)}")
        return 1
    if skipped:
        print(f"PASSED, but {', '.join(skipped)} did not run - coverage is incomplete.")
        return 0
    print("PASSED - all suites green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
