# Form Definition Schema

A single, form-agnostic **JSON Schema** that every IPO form-definition file validates against.
One definition document fully describes a form's structure — sections, fields, tables, choices,
conditional logic, validation, signature blocks, repeatable rows, and auto-fill hints — with **no
UI, rendering, or backend code**. It is the data contract the form editor, pre-fill, preview, and
export layers will all read.

> Derived from the 35 form specifications in `docs/specifications/`. The schema was shaped by the
> real recurring patterns catalogued there (strike-out `I/We` choices, the foreign-applications
> table, office-use blocks, OTP/Aadhaar sensitivity, conditional Convention/PCT sections, the
> ubiquitous addressee + signatory), so it can represent **every** form without special-casing.

## Files

| File | What it is |
|---|---|
| `form-definition.schema.json` | The meta-schema. Every `*.definition.json` validates against this. |
| `examples/form_27.definition.json` | Worked example — checkbox group, table with checkbox columns, conditional required fields, repeatable rows, "No Fee". |
| `../definitions/form_03.definition.json` | **Reference implementation** — the production, renderer-complete Form 3 definition (the renderer is built against this first). |

The example and the reference implementation are validated in CI-style below (see **Validation**).

---

## Governing principle

**The software suggests; the user decides.** Auto-fill hints describe *opportunity only*. A value
is never locked and every field is always editable — the schema has **no** "locked"/"readonly"
concept for user data (the only read-only construct is `officeUseOnly`, for blocks the Patent
Office fills, not the applicant).

---

## Top-level shape

```jsonc
{
  "schemaVersion": "1.0",
  "formId": "form_03",          // matches the spec file stem
  "formNumber": "3",            // string, to allow "7A", "18A"
  "officialName": "...",        // exact, transcribed
  "purpose": "...",
  "legalReference": { "act": [...], "rules": [...] },
  "pageCount": 2,
  "fee": { "model": "first_schedule | none | stamp_duty | other", "note": "...", "dependsOn": [...] },
  "layout": { "columns": 2, "notes": "..." },
  "sections": [ Section, ... ],   // array order IS printed order
  "constraints": [ Constraint, ... ],   // form-level cross-field rules
  "attachments": [ Attachment, ... ],
  "notes": [ "verbatim footnotes / warnings" ],
  "metadata": { ... }
}
```

A **Section** holds ordered **fields** and may itself be conditional (`visibleWhen`) or
`officeUseOnly`. Everything else nests inside fields.

---

## Field kinds

One discriminator, `kind`, drives the field. Kind-specific requirements are enforced by the schema
(e.g. a `radio` must have `options`, a `table` must have `columns`).

| `kind` | Represents | Requires |
|---|---|---|
| `text` | Single-line text | — |
| `textarea` | Multi-line text (descriptions, name/address blocks) | — |
| `number` | Numeric | — |
| `date` | Date | — |
| `checkbox` | One boolean tick | — |
| `checkboxGroup` | Several **individually addressable** checkboxes (multi-select) | `options` |
| `radio` | Single-select, mutually exclusive | `options` |
| `dropdown` | Single-select from a (possibly large) list | `options` |
| `strikeoutChoice` | Single-select whose **unchosen** option is struck through on export (`I/We`, `has/have`, `alone/jointly`) | `options` |
| `signature` | A signature mark | — |
| `signatureBlock` | Container grouping signature + name + date + capacity | `fields` |
| `boilerplate` | Verbatim pre-printed text, no input (undertakings, declarations) | `text` |
| `group` | Container of nested fields; combine with `repeatable` for repeating blocks | `fields` |
| `table` | Columns + repeatable rows | `columns` |

Shared optional properties on any field: `label`, `helpText`, `placeholder`, `format`, `required`,
`requiredWhen`, `visibleWhen`, `enabledWhen`, `repeatable`, `validation`, `autofill`, `sensitive`,
`export`, `officeUseOnly`, `constraints`, `presentation`.

### Why these choices

- **`checkbox` vs `checkboxGroup`.** The specs mandate "document every checkbox, never combine". A
  `checkboxGroup` keeps each option individually addressable (its own `value`), so every printed
  checkbox is preserved and can be targeted by conditions — never merged.
- **`strikeoutChoice` as its own kind.** Functionally a single-select, but it carries export
  semantics (`export.strikeoutUnselected`) so the generated form reproduces the official strike-out.
- **Address is not a special kind.** Structured addresses (Form 1, Form 30) are a `group` of child
  fields; free-text addresses are a `textarea` with `format: "address"`. One less special case.

---

## Field paths (how references work)

Conditions, constraints, and validators reference fields by a **dotted path** of ids:

```
<section_id>.<field_id>
<section_id>.<group_id>.<child_field_id>
<section_id>.<table_id>.<column_id>       // a table column
```

Ids must be unique within their scope; paths make them globally addressable. (Global uniqueness of
*paths* is a tooling-time check — JSON Schema validates shape, not cross-reference integrity.)

---

## Conditional logic

A `condition` is a small boolean expression, used by `visibleWhen`, `requiredWhen`, `enabledWhen`,
and inside constraints. Leaves reference a field path; composites nest.

```jsonc
// leaf
{ "field": "section2.type_of_application", "op": "equals", "value": "convention" }
// ops: equals notEquals in notIn isFilled isEmpty gt gte lt lte matches
// (for multi-select fields, `in` tests membership of a value in the selection)

// composite
{ "allOf": [ CondA, CondB ] }
{ "anyOf": [ CondA, CondB ] }
{ "not": CondA }
```

Real uses from the specs: Form 1 §8–§11 shown only for the matching *Type of Application*; Form 3's
foreign-applications table shown only when option (iii) is chosen; Form 27's licensing contact
fields required only when "available for licensing = YES".

---

## Validation & constraints

- **Field-level `validation`** — intrinsic checks on one field: `pattern` (+`patternMessage`),
  `minLength`/`maxLength`, `min`/`max`, `notFuture`/`notPast` for dates.
- **`constraints`** (on form, section, or group) — cross-field rules:
  `exactlyOneOf`, `atLeastOneOf`, `atMostOneOf`, `allOrNone`, `requiredTogether`, and `custom`
  (evaluates an `assert` condition). Each has a `message` and `severity` (`error` | `warning`), and
  an optional `when` guard.

Examples in the shipped definitions: application-number and financial-year `pattern`s, `notFuture`
on filing dates, a `custom` "exactly one of Worked/Not-worked per row" (Form 27), and a `custom`
"≥1 foreign row when option (iii)" (Form 3). Time-bar rules (e.g. Form 31's 12-month grace window)
are expressed as `custom` constraints with a `warning`/`error` severity.

---

## Auto-fill hints (decoupled from the extraction model)

Each field may carry an `autofill` hint describing **where a value could come from** — never
enforcing it:

```jsonc
"autofill": {
  "strategy": "direct | derived | manual",
  "sources": [ { "sourceType": "form1", "key": "application.number" } ],
  "derivation": "…",              // for derived
  "confidence": "high | medium | low"
}
```

`sourceType` and `key` are an **open vocabulary** on purpose. The internal extraction object (the
former "Patent Profile") is still being modelled and is under the project freeze — so the schema
points at it by *semantic name*, not by a bound structure. When the extraction schema is finalized,
these keys map to it without changing any form definition. Recommended vocabularies are documented
inline in the schema (`autofillSource`).

---

## Repeatable rows

`repeatable: { min, max (null = unbounded), itemLabel }` marks:
- a **group** → the whole block repeats (Form 1/6/10/12 applicant blocks (a)–(c), inventor blocks);
- a **table** → rows repeat (Form 3 foreign applications, Form 27 patents, Form 1 applicants/inventors);
- a **single field** → repeated entries (opposition "grounds, one after another").

---

## Signature blocks

A `signatureBlock` is a `group` specialized to signing: it nests a `signature` field, a signatory
`name`, optionally a `date` and a `capacity` (applicant vs registered agent). Forms with **multiple**
signing points (Form 1's inventor / convention-applicant / final declaration; Form 5's several
declarations) simply list several signature blocks — one uniform construct.

---

## Sensitive data & export fidelity

- **`sensitive`** — `{ pii, redacted, requiresOtp, note }`. Captures the form's own handling rules:
  Form 1 "OTP verification mandatory — will be redacted" fields, Form 8A Aadhaar, Form 18A female
  photo-ID evidence. Consumers must treat these specially (mask, never log/URL, redact on publish).
- **`export`** — `{ verbatim, strikeoutUnselected }`. Ensures boilerplate is reproduced exactly and
  strike-out choices render like the official form.
- **`officeUseOnly`** — read-only "FOR OFFICE USE ONLY" blocks (Form 1, Form 18, Form 18A headers).

---

## Capability → form coverage

Every capability requested is exercised by real forms:

| Capability | Representative forms |
|---|---|
| Sections | all |
| Fields | all |
| Tables | 1 (applicants/inventors/convention), 3 (foreign apps), 18A (evidence), 27 (worked/not-worked), 30 (address) |
| Checkboxes | 1 (type/category/§12(iii)/attachments), 18A (grounds), 27 (reasons), 31 (§31 limbs) |
| Radio buttons | 3 (ii/iii), 8 (include/exclude), 14 (six opposition types), 16 (proof branch), 27 (YES/NO) |
| Conditional fields | 1 (§8–§11 by type), 3 (table by (iii)), 5 (§3/§4), 18/18A (request branches), 27 (contact by YES) |
| Signature blocks | all; multi-signature: 1, 5 |
| Repeatable rows | 1, 3, 6, 10, 12, 27 |
| Validation rules | application/patent-number & financial-year patterns; date `notFuture`; per-row XOR (27); 12-month bar (31) |
| Auto-fill hints | 3, 27 (shown); applicable to every applicant/inventor/title/number/date field |

---

## Known limitations (candidates for schemaVersion 1.1)

- **Row-aggregate conditions.** The condition DSL references fields, not "any/all rows of a table".
  So "show the reasons section if *any* table row is Not-worked" isn't directly expressible in 1.0.
  In the Form 27 example this is handled via the reason `checkboxGroup` instead. A future `scope`
  (`row` | `anyRow` | `allRows`) or aggregate ops would close this.
- **Global reference integrity.** JSON Schema validates document *shape*; it can't verify that every
  `condition.field` / `constraint.fields` path resolves to a real field, or that ids are globally
  unique. Add a linter at authoring time.
- **Open vocabularies.** `format`, `autofill.sourceType`, and `autofill.key` are intentionally open
  strings (not closed enums) so the extraction model can evolve without a schema bump. Trade-off:
  typos aren't caught by the schema — the authoring linter should check them against a registry.

---

## Validation

The schema is a valid Draft 2020-12 schema; the example and the reference implementation validate
against it; and negative cases (radio without options, table without columns, boilerplate without
text, custom constraint without assert, bad identifier, unknown kind) are correctly rejected.

```bash
python -m pip install jsonschema
python - <<'PY'
import json
from jsonschema import Draft202012Validator
schema = json.load(open("form-definition.schema.json", encoding="utf-8"))
Draft202012Validator.check_schema(schema)
v = Draft202012Validator(schema)
for f in ["examples/form_27.definition.json", "../definitions/form_03.definition.json"]:
    errs = list(v.iter_errors(json.load(open(f, encoding="utf-8"))))
    print(f, "OK" if not errs else [e.message for e in errs])
PY
```
