"""
Vocabulary linter.

Validates every .definition.json file under docs/specifications/definitions/
against vocabulary/registry.json. Run from any directory — paths are computed
relative to this file's location.

Usage:
    python backend/vocabulary/lint.py           # all definitions
    python backend/vocabulary/lint.py path.json # one file

Exit code: 0 if clean, 1 if any violations found.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# --- paths -------------------------------------------------------------------

_HERE = Path(__file__).parent
_BACKEND_DIR = _HERE.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_REGISTRY_PATH = _HERE / "registry.json"
_DEFINITIONS_DIR = _PROJECT_ROOT / "docs" / "specifications" / "definitions"

# Running this file directly puts backend/vocabulary/ on sys.path, not backend/,
# so `from models...` would fail. Backend modules import each other as top-level
# packages (the way uvicorn runs them), so backend/ has to be the import root.
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def load_registry() -> dict:
    return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))


def find_definition_files(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p).resolve() for p in paths]
    return list(_DEFINITIONS_DIR.rglob("*.definition.json"))


# --- AST walkers -------------------------------------------------------------

def walk_autofill_blocks(obj: object, path: str = "") -> list[tuple[str, dict]]:
    """Yield (field_path, autofill_block) for every autofill block in obj."""
    results = []
    if isinstance(obj, dict):
        if "autofill" in obj and isinstance(obj["autofill"], dict):
            results.append((path, obj["autofill"]))
        for k, v in obj.items():
            child_path = f"{path}.{k}" if path else k
            results.extend(walk_autofill_blocks(v, child_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(walk_autofill_blocks(item, f"{path}[{i}]"))
    return results


# --- lint rules --------------------------------------------------------------

class LintError:
    def __init__(self, definition: str, field_path: str, rule: str, detail: str, fix: str = ""):
        self.definition = definition
        self.field_path = field_path
        self.rule = rule
        self.detail = detail
        self.fix = fix

    def __str__(self) -> str:
        lines = [f"  [{self.rule}] {self.field_path}",
                 f"    {self.detail}"]
        if self.fix:
            lines.append(f"    Fix: {self.fix}")
        return "\n".join(lines)


def lint_file(path: Path, registry: dict) -> list[LintError]:
    try:
        definition = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [LintError(str(path), "(file)", "INVALID_JSON", str(e))]

    valid_source_types = set(registry["sourceTypes"].keys())
    valid_keys = set(registry["keys"].keys())
    deprecated_sources = registry.get("deprecated", {})

    errors: list[LintError] = []
    form_id = definition.get("formId", path.stem)
    blocks = walk_autofill_blocks(definition)

    for field_path, af in blocks:
        sources = af.get("sources", [])
        if af.get("strategy") == "direct" and not sources:
            errors.append(LintError(
                form_id, field_path,
                "MISSING_SOURCES",
                "strategy='direct' requires at least one sources entry.",
                "Add a sources array or change strategy to 'derived'."
            ))

        # Track duplicates within this one sources[] array only.
        # Two different fields referencing the same (sourceType, key) is intentional
        # (e.g. both 'applicant_names' and 'joint_applicants' drawing from form1/applicant.name).
        seen_in_field: set[tuple[str, str]] = set()
        for src in sources:
            source_type = src.get("sourceType", "")
            key = src.get("key", "")

            # Unknown sourceType
            if source_type not in valid_source_types:
                deprecated_hint = f" (deprecated as: {deprecated_sources[source_type]})" \
                    if source_type in deprecated_sources else ""
                errors.append(LintError(
                    form_id, field_path,
                    "UNKNOWN_SOURCE_TYPE",
                    f"sourceType '{source_type}' is not in the registry.{deprecated_hint}",
                    f"Change to one of: {', '.join(sorted(valid_source_types))}"
                ))

            # Unknown key
            if key not in valid_keys:
                deprecated_hint = f" (deprecated as: {deprecated_sources[key]})" \
                    if key in deprecated_sources else ""
                errors.append(LintError(
                    form_id, field_path,
                    "UNKNOWN_KEY",
                    f"key '{key}' is not in the registry.{deprecated_hint}",
                    f"Add to registry.json keys or use an existing key."
                ))

            # Duplicate reference within the SAME field's sources[] array
            ref = (source_type, key)
            if ref in seen_in_field:
                errors.append(LintError(
                    form_id, field_path,
                    "DUPLICATE_SOURCE_REF",
                    f"(sourceType='{source_type}', key='{key}') appears more than once in this field's sources array.",
                    "Remove the duplicate entry."
                ))
            seen_in_field.add(ref)

    return errors


def lint_source_type_coverage(registry: dict) -> list[LintError]:
    """Check registry sourceTypes and DocumentType members agree, both ways.

    This is a whole-vocabulary rule, not a per-definition one, so it runs once
    rather than per file.

    Why both directions matter:
      * registry sourceType with no DocumentType member — UNREACHABLE. The
        classifier can only emit enum members, so every autofill source citing
        that sourceType silently never matches. Nothing else in the codebase
        notices; autofill just quietly returns fewer suggestions.
      * DocumentType member with no registry sourceType — UNSPENDABLE. The
        classifier can produce it and an extractor can stamp it onto
        Fact.source_type, but no definition may legally reference it, so the
        facts are dead on arrival.

    Both failures look identical from the UI: correct-looking extraction, no
    suggestion. That is why they are lint errors rather than runtime warnings.
    """
    from models.patent_profile import DocumentType

    # GENERIC and UNKNOWN describe how a document was processed, not what it is.
    # They are deliberately absent from the registry.
    processing_states = {DocumentType.GENERIC, DocumentType.UNKNOWN}

    registered = set(registry["sourceTypes"])
    classifiable = {m.value for m in DocumentType if m not in processing_states}

    errors: list[LintError] = []

    for source_type in sorted(registered - classifiable):
        errors.append(LintError(
            "(vocabulary)", f"sourceTypes.{source_type}",
            "UNREACHABLE_SOURCE_TYPE",
            f"sourceType '{source_type}' has no DocumentType member, so the "
            f"classifier can never emit it and every autofill source citing it "
            f"is dead.",
            f"Add a DocumentType member with value '{source_type}' in "
            f"models/patent_profile.py, and anchors for it in "
            f"extractor/classifier.py.",
        ))

    for value in sorted(classifiable - registered):
        errors.append(LintError(
            "(vocabulary)", f"DocumentType.{value}",
            "UNSPENDABLE_DOCUMENT_TYPE",
            f"DocumentType '{value}' is not a registry sourceType, so no form "
            f"definition may reference facts extracted from it.",
            f"Add '{value}' to sourceTypes in registry.json, or remove the "
            f"enum member.",
        ))

    return errors


# --- entry point -------------------------------------------------------------

def main(argv: list[str] = sys.argv[1:]) -> int:
    registry = load_registry()
    files = find_definition_files(argv)

    if not files:
        print("No definition files found.")
        return 1

    total_errors = 0

    # Whole-vocabulary rules run once, before the per-definition pass — a
    # coverage gap explains failures the per-file output cannot.
    coverage_errors = lint_source_type_coverage(registry)
    if coverage_errors:
        print("\nFAIL  vocabulary/DocumentType coverage")
        for e in coverage_errors:
            print(e)
        total_errors += len(coverage_errors)
    else:
        print("OK    vocabulary/DocumentType coverage")

    for path in sorted(files):
        errors = lint_file(path, registry)
        if errors:
            print(f"\nFAIL  {path.name}")
            for e in errors:
                print(e)
            total_errors += len(errors)
        else:
            print(f"OK    {path.name}")

    print(f"\n{'='*60}")
    if total_errors:
        print(f"FAIL — {total_errors} violation(s) across {len(files)} file(s).")
        return 1
    else:
        print(f"PASS — {len(files)} file(s) checked, 0 violations.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
