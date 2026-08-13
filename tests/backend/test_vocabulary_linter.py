"""Vocabulary linter — the guard against silent autofill drift.

A typo'd sourceType or key does not raise an error at runtime: the field simply
never auto-fills. The linter converts that silent failure into a loud one, so
these tests verify it actually catches each defect class — and, just as
importantly, that it does NOT flag the legitimate patterns.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import context  # noqa: F401  — sets sys.path

from vocabulary.lint import lint_file, load_registry, main, walk_autofill_blocks


def _definition(fields):
    """Minimal well-formed definition wrapping the given field list."""
    return {
        "formId": "form_test",
        "formNumber": "TEST",
        "officialName": "Synthetic definition for linter tests",
        "sections": [{"id": "s1", "title": "Section 1", "fields": fields}],
    }


def _direct(sources):
    return {"strategy": "direct", "sources": sources}


class _TempDefinition:
    """Writes a definition dict to a temp .definition.json and yields its Path."""

    def __init__(self, payload, raw: str = None):
        self._payload = payload
        self._raw = raw

    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        path = Path(self._dir.name) / "form_test.definition.json"
        if self._raw is not None:
            path.write_text(self._raw, encoding="utf-8")
        else:
            path.write_text(json.dumps(self._payload), encoding="utf-8")
        return path

    def __exit__(self, *exc):
        self._dir.cleanup()


class TestAutofillWalker(unittest.TestCase):
    def test_finds_autofill_blocks_at_any_nesting_depth(self):
        definition = _definition([
            {"id": "top", "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])},
            {
                "id": "group",
                "fields": [
                    {"id": "nested", "autofill": _direct([{"sourceType": "form1", "key": "signatory.name"}])}
                ],
            },
        ])
        blocks = walk_autofill_blocks(definition)
        self.assertEqual(2, len(blocks), "walker must reach nested fields")

    def test_returns_empty_for_definition_with_no_autofill(self):
        self.assertEqual([], walk_autofill_blocks(_definition([{"id": "plain", "kind": "text"}])))


class TestLintRules(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry()

    def _rules_for(self, fields):
        with _TempDefinition(_definition(fields)) as path:
            return [e.rule for e in lint_file(path, self.registry)]

    def test_flags_unknown_source_type(self):
        rules = self._rules_for([
            {"id": "f", "autofill": _direct([{"sourceType": "form_nope", "key": "applicant.name"}])}
        ])
        self.assertIn("UNKNOWN_SOURCE_TYPE", rules)

    def test_flags_unknown_key(self):
        rules = self._rules_for([
            {"id": "f", "autofill": _direct([{"sourceType": "form1", "key": "applicant.nope"}])}
        ])
        self.assertIn("UNKNOWN_KEY", rules)

    def test_deprecated_source_type_is_flagged_with_migration_hint(self):
        """Finding F1: 'form16' was the real bug this linter was built to catch."""
        with _TempDefinition(_definition([
            {"id": "f", "autofill": _direct([{"sourceType": "form16", "key": "assignee.address"}])}
        ])) as path:
            errors = lint_file(path, self.registry)

        matching = [e for e in errors if e.rule == "UNKNOWN_SOURCE_TYPE"]
        self.assertEqual(1, len(matching))
        self.assertIn("deprecated", matching[0].detail.lower())
        self.assertIn("form16_registration", matching[0].detail)

    def test_deprecated_key_is_flagged_with_migration_hint(self):
        """Finding F2: composite 'patentee.details' split into atomic keys."""
        with _TempDefinition(_definition([
            {"id": "f", "autofill": _direct([{"sourceType": "patent_certificate", "key": "patentee.details"}])}
        ])) as path:
            errors = lint_file(path, self.registry)

        matching = [e for e in errors if e.rule == "UNKNOWN_KEY"]
        self.assertEqual(1, len(matching))
        self.assertIn("deprecated", matching[0].detail.lower())

    def test_flags_duplicate_source_ref_within_one_field(self):
        rules = self._rules_for([
            {
                "id": "f",
                "autofill": _direct([
                    {"sourceType": "form1", "key": "applicant.name"},
                    {"sourceType": "form1", "key": "applicant.name"},
                ]),
            }
        ])
        self.assertIn("DUPLICATE_SOURCE_REF", rules)

    def test_does_not_flag_same_ref_used_by_two_different_fields(self):
        """Regression guard for a real false positive.

        Two fields drawing on the same (sourceType, key) is intentional — in
        form_03 both 'applicant_names' and 'joint_applicants' read
        form1/applicant.name. An earlier linter used a definition-wide 'seen'
        set and wrongly flagged it.
        """
        rules = self._rules_for([
            {"id": "a", "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])},
            {"id": "b", "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])},
        ])
        self.assertNotIn("DUPLICATE_SOURCE_REF", rules)

    def test_flags_direct_strategy_with_no_sources(self):
        rules = self._rules_for([{"id": "f", "autofill": {"strategy": "direct", "sources": []}}])
        self.assertIn("MISSING_SOURCES", rules)

    def test_does_not_flag_derived_strategy_without_sources(self):
        rules = self._rules_for([{"id": "f", "autofill": {"strategy": "derived", "rule": "prose"}}])
        self.assertEqual([], rules)

    def test_reports_invalid_json_instead_of_raising(self):
        with _TempDefinition(None, raw="{ not valid json ,,, }") as path:
            errors = lint_file(path, self.registry)
        self.assertEqual(["INVALID_JSON"], [e.rule for e in errors])

    def test_clean_definition_produces_no_errors(self):
        rules = self._rules_for([
            {
                "id": "f",
                "autofill": _direct([
                    {"sourceType": "form1", "key": "applicant.name"},
                    {"sourceType": "form2_specification", "key": "applicant.name"},
                ]),
            }
        ])
        self.assertEqual([], rules)


class TestLinterAgainstRealDefinitions(unittest.TestCase):
    def test_all_shipped_definitions_pass(self):
        registry = load_registry()
        failures = {}
        for path in context.DEFINITIONS_DIR.rglob("*.definition.json"):
            errors = lint_file(path, registry)
            if errors:
                failures[path.name] = [f"{e.rule} at {e.field_path}" for e in errors]
        self.assertEqual({}, failures, f"shipped definitions have lint violations: {failures}")

    def test_form_03_no_longer_references_the_deprecated_form16(self):
        """Locks in the F1 fix so it cannot silently regress."""
        raw = (context.DEFINITIONS_DIR / "form_03.definition.json").read_text(encoding="utf-8")
        definition = json.loads(raw)
        source_types = {
            src.get("sourceType")
            for _p, af in walk_autofill_blocks(definition)
            for src in af.get("sources", [])
        }
        self.assertNotIn("form16", source_types)
        self.assertIn("form16_registration", source_types)


class TestLinterExitCode(unittest.TestCase):
    """The linter is meant to gate CI, so its exit code is part of its contract."""

    def _run_main(self, path):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main([str(path)])
        return code, buffer.getvalue()

    def test_exit_zero_and_reports_pass_for_clean_file(self):
        with _TempDefinition(_definition([
            {"id": "f", "autofill": _direct([{"sourceType": "form1", "key": "applicant.name"}])}
        ])) as path:
            code, output = self._run_main(path)
        self.assertEqual(0, code)
        self.assertIn("PASS", output)

    def test_exit_one_and_reports_fail_for_dirty_file(self):
        with _TempDefinition(_definition([
            {"id": "f", "autofill": _direct([{"sourceType": "totally_made_up", "key": "applicant.name"}])}
        ])) as path:
            code, output = self._run_main(path)
        self.assertEqual(1, code)
        self.assertIn("FAIL", output)

    def test_full_repository_scan_passes(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main([])
        self.assertEqual(0, code, f"repo-wide lint failed:\n{buffer.getvalue()}")


if __name__ == "__main__":
    unittest.main()
