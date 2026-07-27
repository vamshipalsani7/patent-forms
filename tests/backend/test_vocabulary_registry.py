"""Vocabulary registry — structural integrity and the demand-driven invariant.

The registry is the single source of truth for autofill vocabulary. These tests
guard the two properties that make it trustworthy:

  1. It is well-formed (so the linter can rely on its shape).
  2. Everything the definitions actually reference exists in it (so a typo can
     never fail silently — the failure mode the registry exists to prevent).
"""

from __future__ import annotations

import json
import unittest

import context  # noqa: F401  — sets sys.path

from vocabulary.lint import load_registry, walk_autofill_blocks


def _used_vocabulary():
    """Return (sourceTypes, keys) actually referenced by every definition."""
    source_types, keys = set(), set()
    for path in context.DEFINITIONS_DIR.rglob("*.definition.json"):
        definition = json.loads(path.read_text(encoding="utf-8"))
        for _field_path, autofill in walk_autofill_blocks(definition):
            for source in autofill.get("sources", []):
                source_types.add(source.get("sourceType", ""))
                keys.add(source.get("key", ""))
    return source_types, keys


class TestRegistryStructure(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry()

    def test_has_required_top_level_sections(self):
        for section in ("version", "sourceTypes", "keys", "deprecated"):
            self.assertIn(section, self.registry, f"registry.json missing '{section}'")

    def test_every_source_type_has_a_description(self):
        for name, meta in self.registry["sourceTypes"].items():
            self.assertIsInstance(meta, dict, f"sourceType '{name}' must map to an object")
            self.assertTrue(
                str(meta.get("description", "")).strip(),
                f"sourceType '{name}' has no description",
            )

    def test_every_key_has_a_type_and_description(self):
        allowed_types = {"string", "date", "number", "boolean"}
        for name, meta in self.registry["keys"].items():
            self.assertIsInstance(meta, dict, f"key '{name}' must map to an object")
            self.assertIn(
                meta.get("type"),
                allowed_types,
                f"key '{name}' has unsupported type {meta.get('type')!r}",
            )
            self.assertTrue(
                str(meta.get("description", "")).strip(),
                f"key '{name}' has no description",
            )

    def test_keys_are_atomic_not_composite(self):
        """Finding F2: composite blobs cannot be conflict-resolved or validated.

        'patentee.details' was split into atomic keys; the word 'details' is the
        marker for that anti-pattern.
        """
        for name in self.registry["keys"]:
            self.assertFalse(
                name.endswith(".details"),
                f"key '{name}' looks composite — split it into atomic keys",
            )

    def test_deprecated_entries_are_not_also_live(self):
        live = set(self.registry["sourceTypes"]) | set(self.registry["keys"])
        for name in self.registry["deprecated"]:
            self.assertNotIn(
                name,
                live,
                f"'{name}' is listed as deprecated but is still a live entry",
            )

    def test_known_bad_vocabulary_is_recorded_as_deprecated(self):
        """The two defects the registry was introduced to catch (F1, F2)."""
        self.assertIn("form16", self.registry["deprecated"])
        self.assertIn("patentee.details", self.registry["deprecated"])


class TestDemandDrivenInvariant(unittest.TestCase):
    """The rule from the architecture: vocabulary is derived from demand."""

    def setUp(self):
        self.registry = load_registry()
        self.used_source_types, self.used_keys = _used_vocabulary()

    def test_every_referenced_source_type_is_registered(self):
        unknown = self.used_source_types - set(self.registry["sourceTypes"])
        self.assertEqual(
            set(), unknown, f"definitions reference unregistered sourceTypes: {sorted(unknown)}"
        )

    def test_every_referenced_key_is_registered(self):
        unknown = self.used_keys - set(self.registry["keys"])
        self.assertEqual(
            set(), unknown, f"definitions reference unregistered keys: {sorted(unknown)}"
        )

    def test_registry_does_not_grow_speculatively(self):
        """Guards the reverse direction of the demand-driven rule.

        Only 1 of 35 form definitions is authored, so the registry legitimately
        contains entries no definition references yet. That set is pinned here:
        it may SHRINK freely (as definitions get written), but any NEW unused
        entry fails this test and has to be justified — which is exactly the
        "model everything about a patent" drift the registry exists to prevent.
        """
        pending_source_types = {
            "form28", "form3", "form5", "pct_document", "publication_record",
        }
        pending_keys = {
            "agent.inpaNumber", "applicant.address", "applicant.country",
            "applicant.nationality", "assignee.name", "invention.title",
            "patent.grantDate", "patent.number", "patentee.address",
            "patentee.name", "patentee.nationality",
        }

        unused_source_types = set(self.registry["sourceTypes"]) - self.used_source_types
        unused_keys = set(self.registry["keys"]) - self.used_keys

        self.assertEqual(
            set(),
            unused_source_types - pending_source_types,
            "new sourceType(s) added to the registry that no definition references",
        )
        self.assertEqual(
            set(),
            unused_keys - pending_keys,
            "new key(s) added to the registry that no definition references",
        )


class TestRegistryMatchesDocumentTypeEnum(unittest.TestCase):
    """DocumentType members must be spendable as registry sourceTypes.

    The classifier's output feeds Fact.source_type, which the mapper matches
    against `autofill.sources[].sourceType`. A drift here breaks autofill
    silently — the classification succeeds but nothing ever matches.
    """

    def test_every_classifiable_document_type_is_a_registered_source_type(self):
        from models.patent_profile import DocumentType

        registry = load_registry()
        # GENERIC/UNKNOWN are processing outcomes, not document classifications.
        processing_states = {DocumentType.GENERIC, DocumentType.UNKNOWN}

        for member in DocumentType:
            if member in processing_states:
                continue
            self.assertIn(
                member.value,
                registry["sourceTypes"],
                f"DocumentType.{member.name} ('{member.value}') is not a registry sourceType",
            )


if __name__ == "__main__":
    unittest.main()
