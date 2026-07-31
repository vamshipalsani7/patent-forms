"""Authoring pattern library — the templates must stay valid and registry-clean.

The library (docs/specifications/patterns/patterns.json) is copy-paste guidance,
not runtime code, so nothing executes it. That is exactly why it needs a test:
without one, a snippet could drift into teaching authors vocabulary the linter
rejects, or a shape the schema forbids, and nobody would notice until a real
definition failed.

Two guarantees are asserted, both dependency-free (no jsonschema needed):

  1. Every autofill reference in every snippet uses only vocabulary registered in
     backend/vocabulary/registry.json — checked with the linter's OWN walker, so
     the library and the linter can never disagree.
  2. Every snippet is a structurally valid schema fragment (valid `kind`, plus the
     kind-specific requirements the schema enforces), with `kind` values taken
     live from the schema so this test tracks the schema if it changes.
"""

from __future__ import annotations

import json
import unittest

import context  # noqa: F401  — sets sys.path + PROJECT_ROOT

from vocabulary.lint import load_registry, walk_autofill_blocks

PATTERNS_PATH = context.PROJECT_ROOT / "docs" / "specifications" / "patterns" / "patterns.json"
SCHEMA_PATH = context.PROJECT_ROOT / "docs" / "specifications" / "schema" / "form-definition.schema.json"

# Kind-specific requirements, mirroring the schema's field/cell allOf rules.
_REQUIRES = {
    "radio": "options",
    "dropdown": "options",
    "checkboxGroup": "options",
    "strikeoutChoice": "options",
    "boilerplate": "text",
    "group": "fields",
    "signatureBlock": "fields",
    "table": "columns",
}

# Every requested authoring category must be represented, so the library cannot
# silently lose one. Maps category -> at least one pattern key that covers it.
_REQUIRED_PATTERNS = {
    "document envelope": ["document_skeleton"],
    "inline blanks": ["inline_blank_clause"],
    "applicant details": ["applicant_names", "applicant_particulars_composite", "applicant_block"],
    "address for service": ["address_for_service"],
    "signature block": ["signature_section", "signatory_section", "signature_block_grouped"],
    "date block": ["date_line"],
    "addressee block": ["addressee_section"],
    "strike-out choices": ["iwe_strikeout", "strikeout_choice_template"],
    "common declaration sections": ["truth_declaration"],
}

_VALID_SHAPES = {"document", "section", "fields", "field"}


def _kinded_dicts(obj):
    """Yield every dict carrying a 'kind' (fields and table cells), recursively."""
    if isinstance(obj, dict):
        if "kind" in obj:
            yield obj
        for value in obj.values():
            yield from _kinded_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _kinded_dicts(item)


class PatternLibraryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
        cls.patterns = cls.library["patterns"]
        cls.registry = load_registry()
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.valid_kinds = set(schema["$defs"]["field"]["properties"]["kind"]["enum"])


class TestLibraryStructure(PatternLibraryTestCase):
    def test_catalog_parses_and_is_non_empty(self):
        self.assertIsInstance(self.patterns, dict)
        self.assertGreater(len(self.patterns), 0)

    def test_is_not_named_like_a_form_definition(self):
        # The linter globs *.definition.json; the catalog must not match it.
        self.assertFalse(PATTERNS_PATH.name.endswith(".definition.json"))

    def test_every_pattern_has_required_metadata(self):
        for name, pattern in self.patterns.items():
            with self.subTest(pattern=name):
                for field in ("shape", "category", "appliesTo", "description", "snippet"):
                    self.assertIn(field, pattern, f"pattern '{name}' is missing '{field}'")
                self.assertIn(pattern["shape"], _VALID_SHAPES)

    def test_all_required_categories_are_present(self):
        for category, expected_keys in _REQUIRED_PATTERNS.items():
            for key in expected_keys:
                with self.subTest(category=category, key=key):
                    self.assertIn(key, self.patterns, f"missing required pattern '{key}' for '{category}'")


class TestDocumentSkeleton(PatternLibraryTestCase):
    """The skeleton must carry the whole envelope, so authors never open Form 3 for it."""

    def setUp(self):
        self.doc = self.patterns["document_skeleton"]["snippet"]

    def test_shape_is_document(self):
        self.assertEqual("document", self.patterns["document_skeleton"]["shape"])

    def test_has_all_required_top_level_keys(self):
        for key in ("schemaVersion", "formId", "formNumber", "officialName", "sections"):
            self.assertIn(key, self.doc, f"skeleton is missing required top-level key '{key}'")

    def test_schema_version_matches_the_schema_constant(self):
        self.assertEqual("1.0", self.doc["schemaVersion"])

    def test_carries_the_conventions_that_previously_needed_form_3(self):
        # layout.columns (two-column assembly) and metadata.printedHeader (centred
        # header) were the two things the old README sent authors to Form 3 for.
        self.assertIn("columns", self.doc.get("layout", {}))
        self.assertIn("printedHeader", self.doc.get("metadata", {}))
        for key in ("formTitle", "statute", "subject", "citation"):
            self.assertIn(key, self.doc["metadata"]["printedHeader"])

    def test_has_at_least_one_section_with_fields(self):
        self.assertTrue(self.doc["sections"])
        for section in self.doc["sections"]:
            self.assertIn("id", section)
            self.assertTrue(section.get("fields"))

    def test_form_id_is_a_valid_identifier(self):
        # Matches the schema's identifier pattern so a real form_nn substitution stays valid.
        import re
        self.assertRegex(self.doc["formId"], r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")


class TestInlineBlankClause(PatternLibraryTestCase):
    """The interleave technique must be shown, not just described in prose."""

    def setUp(self):
        self.pattern = self.patterns["inline_blank_clause"]
        self.fields = self.pattern["snippet"]

    def test_shape_is_fields_and_snippet_is_a_nonempty_list(self):
        self.assertEqual("fields", self.pattern["shape"])
        self.assertIsInstance(self.fields, list)
        self.assertTrue(self.fields)

    def test_interleaves_boilerplate_and_inputs(self):
        kinds = {f["kind"] for f in self.fields}
        self.assertIn("boilerplate", kinds, "clause must include connective boilerplate")
        self.assertTrue(kinds - {"boilerplate"}, "clause must include at least one input field")

    def test_all_fragments_share_one_presentation_group(self):
        # This is the whole point: one printed sentence -> one presentation.group.
        groups = {f.get("presentation", {}).get("group") for f in self.fields}
        self.assertEqual(1, len(groups), f"fragments must share a single group, saw {groups}")
        self.assertNotIn(None, groups, "every fragment needs a presentation.group")


class TestSnippetsAreValidSchemaFragments(PatternLibraryTestCase):
    def test_every_field_kind_is_valid(self):
        for name, pattern in self.patterns.items():
            for node in _kinded_dicts(pattern["snippet"]):
                with self.subTest(pattern=name, kind=node.get("kind")):
                    self.assertIn(node["kind"], self.valid_kinds,
                                  f"pattern '{name}' uses unknown kind '{node['kind']}'")

    def test_kind_specific_requirements_are_met(self):
        for name, pattern in self.patterns.items():
            for node in _kinded_dicts(pattern["snippet"]):
                required = _REQUIRES.get(node["kind"])
                if required:
                    with self.subTest(pattern=name, kind=node["kind"]):
                        self.assertIn(required, node,
                                      f"pattern '{name}' ({node['kind']}) must define '{required}'")

    def test_choice_options_are_well_formed(self):
        for name, pattern in self.patterns.items():
            for node in _kinded_dicts(pattern["snippet"]):
                if node.get("kind") in {"radio", "dropdown", "checkboxGroup", "strikeoutChoice"}:
                    with self.subTest(pattern=name):
                        self.assertTrue(node["options"], f"pattern '{name}' has empty options")
                        for opt in node["options"]:
                            self.assertIn("value", opt, f"pattern '{name}' option missing 'value'")

    def test_section_shaped_patterns_have_id_and_fields(self):
        for name, pattern in self.patterns.items():
            if pattern["shape"] == "section":
                with self.subTest(pattern=name):
                    snippet = pattern["snippet"]
                    self.assertIn("id", snippet)
                    self.assertIsInstance(snippet.get("fields"), list)
                    self.assertTrue(snippet["fields"])


class TestSnippetsAreRegistryClean(PatternLibraryTestCase):
    """The load-bearing guarantee: templates can't teach lint-failing vocabulary."""

    def test_every_autofill_source_type_is_registered(self):
        valid = set(self.registry["sourceTypes"])
        for name, pattern in self.patterns.items():
            for _path, autofill in walk_autofill_blocks(pattern["snippet"]):
                for src in autofill.get("sources", []):
                    st = src.get("sourceType", "")
                    with self.subTest(pattern=name, sourceType=st):
                        self.assertIn(st, valid, f"pattern '{name}' uses unregistered sourceType '{st}'")

    def test_every_autofill_key_is_registered(self):
        valid = set(self.registry["keys"])
        for name, pattern in self.patterns.items():
            for _path, autofill in walk_autofill_blocks(pattern["snippet"]):
                for src in autofill.get("sources", []):
                    key = src.get("key", "")
                    with self.subTest(pattern=name, key=key):
                        self.assertIn(key, valid, f"pattern '{name}' uses unregistered key '{key}'")

    def test_direct_autofill_has_sources_and_derived_does_not_need_them(self):
        for name, pattern in self.patterns.items():
            for _path, autofill in walk_autofill_blocks(pattern["snippet"]):
                strategy = autofill.get("strategy")
                with self.subTest(pattern=name, strategy=strategy):
                    self.assertIn(strategy, {"direct", "derived", "manual"})
                    if strategy == "direct":
                        self.assertTrue(autofill.get("sources"),
                                        f"pattern '{name}' direct autofill has no sources")

    def test_no_duplicate_source_ref_within_a_field(self):
        # Mirrors the linter's per-field DUPLICATE_SOURCE_REF rule.
        for name, pattern in self.patterns.items():
            for _path, autofill in walk_autofill_blocks(pattern["snippet"]):
                seen = set()
                for src in autofill.get("sources", []):
                    ref = (src.get("sourceType"), src.get("key"))
                    with self.subTest(pattern=name, ref=ref):
                        self.assertNotIn(ref, seen, f"pattern '{name}' duplicates source {ref}")
                    seen.add(ref)


if __name__ == "__main__":
    unittest.main()
