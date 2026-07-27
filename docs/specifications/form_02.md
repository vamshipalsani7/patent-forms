# Form 2

**Official Name:** Provisional / Complete Specification

**Purpose:** The specification document describing the invention. Filed as either a
**Provisional** specification (early description) or a **Complete** specification (full
disclosure with claims). Attached to Form 1. Form 2 is largely a structured container for
free-form technical content (description, claims, abstract) rather than discrete data fields.

**Legal Reference:**
- The Patent Act, 1970 (39 of 1970)
- The Patents Rules, 2003 — **Section 10 and Rule 13**

**Page count:** 1 (form face; the specification content itself continues on separate pages)

---

## Overall Layout Notes

- Form 2 is a **Provisional OR Complete** specification — a top-level Strike-out Choice that
  governs Sections 3 and 5 (claims are not applicable to a provisional specification).
- Most sections are large free-text areas whose actual content is supplied on **separate
  continuation pages** ("Description shall start from next page", claims/abstract on separate pages).

---

## Section 0 — Specification Type (global choice)

**Field 0.1 — Provisional / Complete**
- Field Type: Strike-out Choice (`Provisional` | `Complete`)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — detect from the uploaded specification (presence of
  claims/abstract and the preamble wording indicates Complete; absence indicates Provisional).
- Validation Notes: Determines whether Sections 5 (Claims) and 7 (Abstract) apply.

---

## Sections

### Section 1 — Title of the Invention
- **Field 1.1 — Title of the invention** — Type: Multi-line Text. Required: Mandatory.
  Repeatable: No. Auto-fill: **Yes (strong)** from the uploaded specification / Form 1 title.
  Validation: must match Form 1 Section 5.

### Section 2 — Applicant(s)
Description: Identifies the applicant(s). Sub-fields (a)–(c). Repeatable per applicant.
- **Field 2.a — Name** — Text. Mandatory. Repeatable: Yes. Auto-fill: from specification / Form 1.
  Validation: full name, family name first (per Note).
- **Field 2.b — Nationality** — Text / Dropdown (country). Mandatory. Auto-fill: from docs.
- **Field 2.c — Address** — Address / Multi-line Text. Mandatory. Auto-fill: from docs.
  Validation: complete address with postal index no./code, state and country (per Note).

### Section 3 — Preamble to the Description
Description: Pre-printed preamble text, selected by specification type. Two columns:
- **PROVISIONAL:** "The following specification describes the invention."
- **COMPLETE:** "The following specification particularly describes the invention and the manner
  in which it is to be performed."
- **Field 3.1 — Preamble** — Type: Static/Boilerplate (selected by Field 0.1). Required: Mandatory
  (reproduce verbatim per chosen type). Auto-fill: derived from specification type. No user text.

### Section 4 — Description
- **Field 4.1 — Description** — Type: Multi-line Text (large; continues on separate pages).
  Required: Mandatory. Repeatable: No. Auto-fill: **Yes** — body text from the uploaded
  specification. Note on form: "Description shall start from next page."

### Section 5 — Claims
Header text: "CLAIMS (**not** applicable for provisional specification. Claims should start with
the preamble — **'I/we claim'** on separate page)".
- **Field 5.1 — Claims** — Type: Multi-line Text (separate page). Required: **Conditional**
  (Mandatory for Complete; not applicable for Provisional). Repeatable: Yes (multiple claims).
  Auto-fill: **Yes** — claims from the uploaded complete specification. Validation: must begin
  with the preamble "I/we claim".

### Section 6 — Date and Signature
Header text: "DATE AND SIGNATURE (to be given at the end of last page of specification)".
See **Signature Block**.

### Section 7 — Abstract of the Invention
Header text: "ABSTRACT OF THE INVENTION (to be given along with complete specification on separate page)".
- **Field 7.1 — Abstract** — Type: Multi-line Text (separate page). Required: **Conditional**
  (Mandatory for Complete specification). Repeatable: No. Auto-fill: **Yes** — abstract from the
  uploaded complete specification.

---

## Tables

None. (Form 2 has no tabular fields on its face; applicant details repeat as blocks.)

---

## Signature Block (Section 6)

- **Date** — Type: Date. Required: Mandatory. Given at the end of the last page of the specification.
- **Signature** — Type: Signature. Required: Mandatory. Signed by the applicant(s) or authorised
  registered patent agent.
- **Name** — implied (family name first). Type: Text.
- **Place** — not a distinct printed field; do not invent.

---

## Special Notes

Transcribed **Note** block:
- "Repeat boxes in case of more than one entry." → applicant details repeatable.
- "To be signed by the applicant(s) or by authorized registered patent agent."
- "Name of the applicant should be given in full, family name in the beginning."
- "Complete address of the applicant should be given stating the postal index no./code, state and country."
- "Strike out the column which is/are not applicable." → governs the Provisional/Complete choice
  (Sections 3 & 5) and any is/are style choices.

UI notes:
- Form 2 is primarily a **document container**; the editor should support large rich-text areas
  (description, claims, abstract) and clearly reflect the Provisional vs Complete mode, hiding/
  disabling claims & abstract for Provisional (without discarding entered content).
- Attachments: drawings and sequence listings accompany the specification (declared on Form 1 §13),
  not embedded as Form 2 fields.
- Fees: no fee on the face of Form 2 (fee is handled with Form 1 filing).
