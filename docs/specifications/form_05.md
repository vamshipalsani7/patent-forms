# Form 5

**Official Name:** Declaration as to Inventorship

**Purpose:** Declaration by the applicant(s) identifying the true and first inventor(s) of the
invention disclosed in the complete specification. Includes a convention-country assignment
declaration and a statement of assent by additional inventor(s) not named in the application form.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 10(6)**
- The Patents Rules, 2003 — **Rule 13(6)**

**Page count:** 1

---

## Overall Layout Notes

Four numbered sections, each with its own dated signature line. Sections 3 and 4 are conditional
(convention-country assignment; additional inventors).

---

## Sections

### Section 1 — Name of Applicant(s)

**Label:** `1. NAME OF APPLICANT(S)`
Pre-printed continuation: "…… hereby declare that the true and first inventor(s) of the invention
disclosed in the complete specification filed in pursuance of my/our application numbered ……
dated …… is/are"

**Field 1.1 — Name of applicant(s)**
- Field Type: Multi-line Text
- Required?: Mandatory · Repeatable?: Yes
- Auto-fill: **Yes** — applicant name(s) from Form 1 / Specification.
- Validation: full name, family name first. Contains Strike-out Choice `my/our`, `is/are`.

**Field 1.2 — Application number**
- Field Type: Text · Required?: Mandatory · Repeatable?: No
- Auto-fill: **Yes** — from Form 1 / filing acknowledgement.
- Validation: IPO application-number format.

**Field 1.3 — Dated (of the application)**
- Field Type: Date · Required?: Mandatory · Repeatable?: No
- Auto-fill: **Yes** — filing date from Form 1.

### Section 2 — Inventor(s)

**Label:** `2. INVENTOR(S)` with sub-fields (a) NAME, (b) NATIONALITY, (c) ADDRESS.
Repeatable per inventor. Followed by its own dated signature line.

- **Field 2.a — Name** — Text. Mandatory. Repeatable: Yes. Auto-fill: inventor names from Form 1 §4 / specification.
- **Field 2.b — Nationality** — Text / Dropdown. Mandatory. Auto-fill: from docs.
- **Field 2.c — Address** — Address / Multi-line Text. Mandatory. Auto-fill: from docs. Validation: postal index/code, state, country.
- **Field 2.d — Dated this __ day of __ 20__** — Date. Mandatory.
- **Signature / Name of the signatory** — see Signature Block (S2).

### Section 3 — Convention-Country Assignment Declaration

**Label:** `3. DECLARATION TO BE GIVEN WHEN THE APPLICATION IN INDIA IS FILED BY THE APPLICANT(S)
IN THE CONVENTION COUNTRY:-`
Boilerplate: "We the applicant(s) in the convention country hereby declare that our right to apply
for a patent in India is by way of assignment from the true and first inventor(s)."

- **Field 3.1 — Declaration** — Static/Boilerplate. Required: **Conditional** (only when the India
  application is filed by a convention-country applicant). Reproduce verbatim.
- **Field 3.2 — Dated this __ day of __ 20__** — Date. Conditional.
- **Signature / Name of the signatory** — see Signature Block (S3). Conditional.

### Section 4 — Statement by Additional Inventor(s)

**Label:** `4. STATEMENT (to be signed by the additional inventor(s) not mentioned in the
application form)`
Boilerplate: "I/We assent to the invention referred to in the above declaration, being included in
the complete specification filed in pursuance of the stated application."

- **Field 4.1 — Statement** — Static/Boilerplate. Required: **Conditional** (only when there are
  additional inventors not named on Form 1). Reproduce verbatim.
- **Field 4.2 — Dated this __ day of __ 20__** — Date. Conditional.
- **Signature of the additional inventor(s) / Name** — see Signature Block (S4). Repeatable per additional inventor.

### Footer — Addressee
`To, The Controller of Patents — The Patent Office, at ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None. (Inventor details repeat as blocks, not a printed grid.)

---

## Signature Block

Multiple signature points — document each separately:
- **S2 (Section 2, applicant's declaration):** Date, Signature, Name of the signatory. Mandatory.
- **S3 (Section 3, convention-country applicant):** Date, Signature, Name of the signatory. Conditional.
- **S4 (Section 4, additional inventor):** Date, Signature of the additional inventor(s), Name.
  Conditional; repeatable per additional inventor.
- **Place** — not a distinct printed field; do not invent.
- Signatures may be by the applicant(s) or authorised registered patent agent (per Note), except
  where the form requires the specific person (e.g. additional inventor in S4).

---

## Special Notes

Transcribed **Note** block:
- "Repeat boxes in case of more than one entry." → inventor blocks repeatable.
- "To be signed by the applicant(s) or by authorized registered patent agent otherwise where mentioned."
- "Name of the inventor and applicant should be given in full, family name in the beginning."
- "Complete address of the inventor should be given stating the postal index no./code, state and country."
- "Strike out the column which is/are not applicable." → governs `my/our`, `is/are`, etc.

UI notes:
- Sections 3 and 4 are **conditional** — show only when relevant (convention-country filing;
  additional inventors). Never discard entered data when hiding.
- Strong auto-fill synergy with Form 1 (inventors §4) and the complete specification.
- Attachments: none prescribed on the face. Fees: none on the face of Form 5.
