# Authoring Pattern Library

Reusable, copy-paste building blocks for authoring IPO form-definition files
(`docs/specifications/definitions/<form>.definition.json`).

Roughly six blocks recur across almost all 34 forms. Authoring each definition
from scratch would re-derive them 30+ times and drift; this library captures the
canonical shape of each — extracted verbatim from the reference implementation
[`form_03.definition.json`](../definitions/form_03.definition.json) and the specs
in [`docs/specifications/`](..) — so every new definition starts from proven,
registry-clean JSON.

## What this is — and is not

- **It is** authoring guidance plus canonical JSON snippets. You **copy** a
  snippet into your definition and rename its ids.
- **It is not** an include/import mechanism. There is no runtime resolution, no
  `$ref` into these files. Definitions remain standalone documents.
- **It is not** a renderer or schema change. Nothing here is loaded by the app.
  The machine-readable catalog ([`patterns.json`](patterns.json)) exists only so
  the library can be **tested** (see below), not so it can be executed.

Because it is not a form, the catalog is named `patterns.json`, **not**
`*.definition.json` — so the vocabulary linter never mistakes it for a form.

## How to author a new definition using these patterns

1. **Start from the plan.** Find your form's row in the Definition Authoring Plan
   (complexity, dependencies, which patterns it uses).
2. **Copy the `document_skeleton` pattern** as your whole file. It is the complete
   top-level envelope — `schemaVersion`, `formId`, `formNumber`, `officialName`,
   `legalReference`, `fee`, `layout` (with the two-column convention), `notes`,
   and `metadata.printedHeader` (the centred-header block) — with `<...>`
   placeholders. Fill the placeholders from your form's spec. (For the field-by-
   field meaning of each top-level key, see the schema's
   [Top-level shape](../schema/README.md#top-level-shape).) You do **not** need to
   open another definition to get the envelope.
3. **Compose sections from the patterns below.** For each printed block, copy the
   matching snippet from `patterns.json` (or the fenced JSON here) and:
   - **Rename ids** so each is unique within the form (keep the canonical name
     where there is only one instance, e.g. `signatory`, `addressee`).
   - **Set labels/titles/boilerplate `text` verbatim** from the form's
     `docs/specifications/form_*.md` — the snippet text is an example.
   - **Delete inapplicable `autofill.sources`.** Never add a `sourceType`/`key`
     that is not in [`backend/vocabulary/registry.json`](../../../backend/vocabulary/registry.json).
   - **Keep the `export` flags** (`strikeoutUnselected` on strike-out choices,
     `verbatim` on boilerplate).
4. **Lint it:** `python backend/vocabulary/lint.py` (run before committing — it
   validates every autofill reference against the registry).

### Golden rules (from the specs — easy to get wrong)

- **Invent nothing.** Only fields printed on the form. An optional line that is
  struck when N/A is an *optional field*, not a yes/no toggle.
- **No `date_line`** on Forms **7, 7A, 30** — they print no "Dated this…" line.
- **No `addressee_section`** on Form **28** — it prints no addressee.
- **Capture `Designation`** on Forms **7A, 26, 29, 30**; capture the **official
  seal** only on **26** and **30** (`signatory_with_designation`).
- The **office-use header** uses **"RQ No."** (not "Application No.") on Forms
  **18** and **18A**.
- **Flag sensitive fields** with the `sensitive` block: Form 1 OTP email/mobile,
  Form 8A **Aadhaar**, Form 18A **female photo ID**, Form 22 DOB/photos.

## Field paths

Conditions, constraints and validators reference fields by dotted path:

```
<section_id>.<field_id>
<section_id>.<group_id>.<child_field_id>
<section_id>.<table_id>.<column_id>
```

Ids must be unique within their scope. (The renderer proved these paths against
`form_03`; see `frontend/renderer/`.)

---

## Pattern catalog

Each pattern below is also in [`patterns.json`](patterns.json) under the same
key, with `appliesTo`/`authorNotes`. `shape` is what the snippet is:
**document** (the whole file), **section** (drop into the top-level `sections[]`),
**fields** (several sibling fields), or **field** (drop into a section's
`fields[]`).

### Document envelope

- **`document_skeleton`** (document) — the complete top-level file to start from:
  every required/common top-level key, `layout.columns` (the two-column
  convention), the verbatim `notes` array, and `metadata.printedHeader`. This is
  the pattern that removes any need to copy an existing definition for the
  envelope. Replace the `form_nn` / `NN` / `<...>` placeholders from the spec, set
  `layout.columns` to 1 (single-column forms like 1/18/18A) or 2 (two-column
  row-per-section forms), and delete the placeholder section.

### Inline blanks

- **`inline_blank_clause`** (fields) — how to model a printed sentence with
  fill-in blanks. The technique: give every fragment of the same printed sentence
  the **same `presentation.group`** id, alternating `boilerplate` connective words
  with input fields, so a renderer reconstructs the sentence on one line. Use this
  for any form with fill-in-the-blanks paragraphs (3, 4, 13, 25, 29, …).

```jsonc
// inline_blank_clause — one printed sentence, one presentation.group ("clause_i")
[
  { "id": "clause_intro", "kind": "boilerplate",
    "text": "(i) that I/We who have made the application for patent number",
    "export": { "verbatim": true }, "presentation": { "group": "clause_i" } },
  { "id": "application_number", "kind": "text", "label": "Application number (India)",
    "format": "applicationNumber", "required": true,
    "autofill": { "strategy": "direct",
      "sources": [ { "sourceType": "form1", "key": "application.number" } ], "confidence": "high" },
    "presentation": { "group": "clause_i", "multiline": false } },
  { "id": "clause_in_india_dated", "kind": "boilerplate", "text": "in India, dated",
    "export": { "verbatim": true }, "presentation": { "group": "clause_i" } }
  // … continue: date input, alone/jointly strike-out, … all in group "clause_i"
]
```

### Applicant details

Three variants — pick by how the form prints the applicant.

- **`applicant_names`** (field) — name-only, repeatable. Forms 3, 4, 13, 29.
- **`applicant_particulars_composite`** (field) — one blank for "name, address
  and nationality". Forms 7, 8, 9, 11, 14, 15, 17, 19, 21.
- **`applicant_block`** (field, `group`) — structured name / nationality /
  address children, repeated per applicant. Forms 1, 2, 5, 6, 10, 12. Rename to
  `inventor` (with inventor autofill) for inventor blocks.

```jsonc
// applicant_names — the single-blank case
{
  "id": "applicant_names",
  "kind": "textarea",
  "label": "Name of the applicant(s)",
  "required": true,
  "repeatable": { "min": 1, "max": null, "itemLabel": "Applicant" },
  "autofill": {
    "strategy": "direct",
    "sources": [
      { "sourceType": "form1", "key": "applicant.name" },
      { "sourceType": "form2_specification", "key": "applicant.name" },
      { "sourceType": "patent_certificate", "key": "applicant.name" }
    ],
    "confidence": "high"
  },
  "presentation": { "group": "row1", "multiline": true }
}
```

### Address for Service

- **`address_for_service`** (field) — the mandatory Indian address-for-service
  block. Forms 6, 7, 7A, 8, 10, 11, 12, 14, 16, 17, 18, 18A, 19, 21, 24.

### Signature block

- **`signature_section`** (section) — the signature. Set `title` to the form's
  printed signing instruction.
- **`signatory_section`** (section) — "Name of the natural person who has
  signed", autofill agent-name then Form 1 signatory.
- **`signatory_with_designation`** (fields) — name + designation (+ seal on
  26/30).
- **`signature_block_grouped`** (field, `signatureBlock`) — for multi-signature
  forms (1, 5, 27): repeatable signature + name + date.

### Date block

- **`date_line`** (field) — "Dated this __ day of __ 20__", derived autofill.
  **Not** on Forms 7, 7A, 30.

### Addressee block

- **`addressee_section`** (section) — "To, The Controller of Patents… at" +
  fixed four-office dropdown. **Not** on Form 28.

### Strike-out choices

`strikeoutChoice`, always with `export.strikeoutUnselected: true`.

- **`iwe_strikeout`** (field) — the ubiquitous `I/We`.
- **`strikeout_alone_jointly`**, **`strikeout_has_have`** (fields) — common
  concrete tokens.
- **`strikeout_choice_template`** (field) — generic two-way template for any
  `<a>/<b>` printed alternative (is/are, my/our, application/Patent,
  Grantee/Patentee, patentee/applicant, same/substantially, …).

Add the global note to the form's `notes[]`:
`"Note. - Strike out whichever is not applicable."`

### Common declaration sections

- **`truth_declaration`** (field) — the recurring verbatim truth declaration
  (adjust wording to the exact form). Forms 12, 13, 15, 17, 19, 21, 25, 27, 28,
  31.
- **`hereby_declare_connector`** (field) — the "hereby declare:" connector.
- **`office_use_header`** (section, `officeUseOnly`) — the read-only "FOR OFFICE
  USE ONLY" block. Forms 1, 18, 18A (rename first field to "RQ No." on 18/18A).

---

## Autofill vocabulary

Every `autofill` reference in this library uses only sourceTypes and keys
registered in [`backend/vocabulary/registry.json`](../../../backend/vocabulary/registry.json).
This is enforced by
[`tests/backend/test_pattern_library.py`](../../../tests/backend/test_pattern_library.py),
which walks every snippet with the linter's own vocabulary walker — so the
templates can never teach an author vocabulary the linter would later reject. If
you add a pattern that needs a new key, add the key to the registry first (it is
demand-driven), then the test will pass.

## Keeping the library honest

The pattern-library test also checks each snippet is a structurally valid schema
fragment (valid `kind`; `options` on choice kinds; `text` on boilerplate;
`fields` on group/signatureBlock; `columns` on table) and that every requested
pattern category is present. Run the whole suite with:

```bash
python tests/run_tests.py
```
