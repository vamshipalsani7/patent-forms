# Form Definitions

Canonical, machine-readable **form-definition** files — the data the form editor, pre-fill,
preview, and export layers consume. Each validates against the approved schema in
[`../schema/form-definition.schema.json`](../schema/form-definition.schema.json).

## Status

| Form | File | Status |
|---|---|---|
| 3 | `form_03.definition.json` | ✅ **Reference implementation** |
| all others (1–31, variants) | — | ⏳ Deferred |

Per the current build plan, **Form 3 is the reference implementation**. The renderer will be built
against Form 3 only. The remaining 33 definitions are generated **after** the renderer + Form 3 are
proven — and only after any schema refinements that implementation reveals are folded in.

`form_03.definition.json` is intended to be **complete enough to drive a renderer without opening
the original PDF**: every printed word is present — interleaved boilerplate connectives, verbatim
declarations/undertaking, exact left-column row labels, the addressee line, and the footer note —
alongside the interactive fields, in printed order.

## Validate

```bash
python -m pip install jsonschema
python - <<'PY'
import json
from jsonschema import Draft202012Validator
schema = json.load(open("../schema/form-definition.schema.json", encoding="utf-8"))
v = Draft202012Validator(schema)
errs = list(v.iter_errors(json.load(open("form_03.definition.json", encoding="utf-8"))))
print("OK" if not errs else [ (list(e.path), e.message) for e in errs ])
PY
```

## Modeling conventions used in Form 3

These conventions should be applied uniformly to the remaining forms once approved:

- **Two-column layout.** Each printed numbered row is one `section`; the exact left-column label
  (including its number, e.g. `"2. Name, address and nationality of the joint applicant."`) is the
  `section.title`. The renderer places the title in the left column and the section's fields in the
  right column. `layout.columns = 2`.
- **Inline blanks as interleaved fields.** Printed sentences with fill-in blanks are represented as
  an ordered sequence of `boilerplate` text + input fields sharing a `presentation.group` (e.g.
  `clause_i`), so the renderer can reconstruct the sentence on one line: *"(i) that I/We who have
  made the application for patent number `[number]` in India, dated `[date]`, `[alone/jointly]` …"*.
- **Verbatim text.** All pre-printed declarations/undertakings are `boilerplate` with
  `export.verbatim = true` so the exported form reproduces them exactly.
- **Strike-out choices.** `I/We`, `alone/jointly with`, `same/substantially the same`, `has/have`
  are `strikeoutChoice` with `export.strikeoutUnselected = true`. The recurring `I/We` is a single
  control (row 1); later literal `I/We` occurrences live inside boilerplate and are struck
  consistently per the global note.
- **Mutually exclusive declarations** (ii)/(iii) → one `radio` (`foreign_status`); the conditional
  foreign-applications `table` is `visibleWhen` (iii) and a `custom` constraint requires ≥1 row.
- **Nothing invented.** No fields were added that are not on the printed form (e.g. no separate
  "rights assigned?" toggle — the assignment line is simply optional and struck when N/A).
- **Header block** is carried in `metadata.printedHeader` (formTitle / statute / subject / citation)
  so the renderer can reproduce the centred header — see the schema-refinement note below.

## Schema-refinement candidates surfaced by Form 3

Authoring the reference implementation exposed these gaps. They are **recorded, not yet acted on** —
the schema is approved and stable; we refine only if the renderer confirms the need (per the plan).

1. **`legalReference.citation` (and statute title).** Every form prints a "(See section … / rule …)"
   line and a statute title; the current `legalReference` only holds `act`/`rules` arrays. Worked
   around by putting the full header in `metadata.printedHeader`. A first-class `citation` field
   would let this render without metadata.
2. **Field-level `printed: false`.** No way to mark an app-only helper field (e.g. a signing
   "capacity" toggle implied by row 4's label) as *not on the printed form*. To keep the preview
   faithful, such helpers were **omitted** from Form 3. A `printed` flag would let helpers exist
   without polluting the official layout.
3. **Shared option sources (`optionsSource`).** Controlled lists with many entries (country, state)
   can't be referenced by name — `options` must be inlined. Worked around by modelling "Name of the
   country" as `text` + `format: "country"` (faithful, since the paper field is free text). A
   `optionsSource: "country"` (making `options` optional) would support controlled lists cleanly.
4. **Strike-outable boilerplate.** An entire optional printed line (the assignment declaration (i))
   is struck out when N/A, but boilerplate has no per-line "strikeoutable" flag; this relies on the
   global note plus the field being optional.
5. **Mirrored field values.** The recurring `I/We` appears many times; there is no field-reference/
   mirror construct, so later occurrences are static boilerplate text resolved by the global rule.

None of these blocked a complete, valid Form 3 — they are ergonomics/fidelity improvements to weigh
after the renderer runs against this file.
