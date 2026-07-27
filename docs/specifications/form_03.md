# Form 3

**Official Name:** Statement and Undertaking Under Section 8

**Purpose:** Used by an applicant to disclose to the Indian Patent Office the particulars
of corresponding applications for the same or substantially the same invention filed in
countries outside India, and to give an undertaking to keep the Controller informed, in
writing, of such foreign filings up to the date of grant of the patent.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 8**
- The Patents Rules, 2003 — **Rule 12, sub-rules (2) and (3)**

**Page count:** 2

---

## Overall Layout Notes

Form 3 is printed as a **two-column table** with five numbered rows (1–5) plus a footer.

- The **left column** carries the numbered row labels (1–5).
- The **right column** carries pre-printed declaration text with inline blanks, plus the
  actual fill-in fields and the foreign-applications table.
- The left-column labels and the right-column declarations are only **loosely aligned**
  semantically (a known quirk of the official Form 3). This spec documents both columns
  exactly as printed; implementers should follow the field list below, not assume the
  left label names the field to its right.
- The instruction **"Strike out whichever is not applicable."** governs every strike-out
  choice on the form (see Special Notes).

---

## Sections

### Section 1 — Applicant Declaration (Row 1)

**Left-column label:** `1. Name of the applicant(s).`
**Right-column text:** `I/We …………… hereby declare:`

Description: Identifies the applicant(s) making the statement and undertaking. The phrase
"I/We … hereby declare" opens the declaration that continues through Rows 2–3.

**Field 1.1 — Name of the applicant(s)**
- Field Label: `Name of the applicant(s)` (right column: `I/We ……`)
- Field Type: Multi-line Text
- Required?: Mandatory
- Repeatable?: Yes — multiple applicants may be listed within the block
- Auto-fill Opportunity: **Yes** — applicant name(s) from Form 1 (Application for Grant of
  Patent), the Provisional/Complete Specification cover page, or a Patent Certificate.
- Validation Notes: Must not be empty. See Strike-out Choice 1.2 for `I/We`.

**Field 1.2 — I / We (singular vs plural)**
- Field Label: `I/We`
- Field Type: Strike-out Choice (`I` | `We`)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — choose `I` for a single applicant, `We` for
  multiple, based on the applicant count detected in uploaded documents.
- Validation Notes: Exactly one option retained. This choice recurs verbatim throughout the
  form and should be applied consistently.

---

### Section 2 — Foreign Applications Declaration (Row 2)

**Left-column label:** `2. Name, address and nationality of the joint applicant.`
**Right-column text:** declaration items (i), (ii), (iii).

Description: The core of Form 3. Declares whether corresponding foreign applications exist
and, if so, lists their particulars in the table. Item (i) states the Indian application;
items (ii) and (iii) are the mutually exclusive alternatives (no foreign filings vs. foreign
filings listed below).

**Field 2.1 — Indian patent application number** *(item (i): "application for patent number ……")*
- Field Label: Indian application (patent) number
- Field Type: Text (application number format)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes** — from Form 1 filing receipt / application number on the
  Specification or filing acknowledgement.
- Validation Notes: Should match the IPO application-number pattern (e.g. `NNNNNN/CC/YYYY`).

**Field 2.2 — Date of the Indian application** *(item (i): "in India, dated ……")*
- Field Label: Date of application in India
- Field Type: Date
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes** — filing date from Form 1 / filing acknowledgement.
- Validation Notes: Valid calendar date; not in the future.

**Field 2.3 — Alone / jointly with** *(item (i): "alone/jointly with ……")*
- Field Label: `alone/jointly with`
- Field Type: Strike-out Choice (`alone` | `jointly with`)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — `alone` for a single applicant, `jointly with`
  when co-applicants exist.
- Validation Notes: If `jointly with` is retained, Field 2.4 becomes Mandatory.

**Field 2.4 — Names of joint applicant(s)** *(item (i): "jointly with .......")*
- Field Label: Joint applicant name(s)
- Field Type: Multi-line Text
- Required?: Conditional (Mandatory when Field 2.3 = `jointly with`)
- Repeatable?: Yes
- Auto-fill Opportunity: **Yes** — co-applicant names from Form 1 / Specification.
- Validation Notes: Required only when the application was filed jointly.

**Field 2.5 — Foreign-filing status choice** *(items (ii) vs (iii))*
- Field Label: Foreign application status (choose one)
  - `(ii)` I/We have **not** made any application for the same/substantially the same invention outside India, **or**
  - `(iii)` I/We **have** made application(s) for patent in other countries, particulars given below.
- Field Type: Radio Button (single select between (ii) and (iii))
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — select `(iii)` if any foreign/PCT/priority
  documents were uploaded; otherwise `(ii)`. User confirms.
- Validation Notes: If `(iii)` selected, the Foreign Applications Table (below) must contain
  at least one row. Contains an embedded Strike-out Choice `same/substantially the same`.

**Field 2.6 — same / substantially the same** *(embedded in (ii) and (iii))*
- Field Label: `same/substantially the same`
- Field Type: Strike-out Choice (`same` | `substantially the same`)
- Required?: Conditional (applies to the retained declaration)
- Repeatable?: No
- Auto-fill Opportunity: No
- Validation Notes: Exactly one option retained.

> See **Table T1 — Foreign Applications** below for item (iii)'s particulars.

---

### Section 3 — Assignment & Undertaking (Row 3)

**Left-column label:** `3. Name and address of the assignee`
**Right-column text:** items (i) and (ii), then the "Dated this…" line.

Description: Optional declaration that rights in the Indian application have been assigned,
followed by the mandatory Section 8 undertaking (boilerplate) and the date of the statement.

**Field 3.1 — Assignee name and address** *(item (i): "assigned to ……")*
- Field Label: Name and address of the assignee
- Field Type: Address (name + address block) / Multi-line Text
- Required?: Conditional (only if rights have been assigned)
- Repeatable?: Yes (multiple assignees possible)
- Auto-fill Opportunity: **Yes** — from an assignment deed / Form 6 / Form 16 if uploaded.
- Validation Notes: Leave empty if not assigned. Contains embedded Strike-out Choice
  `has/have been assigned`.

**Field 3.2 — has / have been assigned**
- Field Label: `has/have`
- Field Type: Strike-out Choice (`has` | `have`)
- Required?: Conditional
- Repeatable?: No
- Auto-fill Opportunity: No
- Validation Notes: Singular/plural agreement with the number of applications.

**Field 3.3 — Section 8 undertaking (item (ii))**
- Field Label: Undertaking to keep the Controller informed
- Field Type: Static/Boilerplate (no input)
- Required?: Mandatory (must be reproduced verbatim on export)
- Repeatable?: No
- Auto-fill Opportunity: N/A
- Validation Notes: Verbatim text: "that I/We undertake that upto the date of grant of the
  patent by the Controller, I/We would keep him informed in writing regarding the details of
  corresponding applications for patents filed outside India in accordance with the provisions
  contained in section 8 and rule 12."

**Field 3.4 — Dated this __ day of __ 20__**
- Field Label: Date of statement (`Dated this … day of … 20…`)
- Field Type: Date (rendered as day / month / year components on the form)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — default to the preparation/signing date; editable.
- Validation Notes: Valid calendar date.

---

### Section 4 — Signature (Row 4)

**Left-column label:** `4. To be signed by the applicant or his authorized registered patent agent.`
**Right-column text:** `Signature. ……………`

See **Signature Block** below.

---

### Section 5 — Name of Signatory (Row 5)

**Left-column label:** `5. Name of the natural person who has signed.`
**Right-column text:** `( …………… )`

**Field 5.1 — Name of the natural person who signed**
- Field Label: Name of the natural person who has signed
- Field Type: Text
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes** — signatory / patent agent name from Form 1 or Form 26
  (Authorisation of Patent Agent), if uploaded.
- Validation Notes: Natural person's full name (not a company name).

---

### Footer — Addressee

**Right-column text:** `To — The Controller of Patents, The Patent Office, at ……`

**Field F.1 — Patent Office location ("at …")**
- Field Label: The Patent Office at
- Field Type: Dropdown (Patent Office jurisdiction)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — the appropriate jurisdictional patent office
  (Delhi / Mumbai / Chennai / Kolkata) based on the applicant's address or the office on Form 1.
- Validation Notes: One of the four IPO offices (Delhi, Mumbai, Chennai, Kolkata).

---

## Tables

### Table T1 — Foreign Applications (item (iii), Row 2)

Particulars of corresponding applications for patent filed in other countries.

| Column | Field Type | Auto-fill |
|---|---|---|
| Name of the country | Text / Dropdown (country) | From priority/PCT/foreign filing docs |
| Date of application | Date | From foreign filing docs |
| Application No. | Text | From foreign filing docs |
| Status of the application | Text / Dropdown | From foreign filing docs / user |
| Date of publication | Date | From foreign filing docs |
| Date of disposal | Date | From foreign filing docs |

- **Row behaviour:** one row per corresponding foreign application.
- **Multiple rows allowed:** **Yes.**
- **Required?:** Conditional — at least one row required when Field 2.5 = item (iii); the
  table is left blank when item (ii) is selected.

---

## Signature Block

Documented per component:

- **Signature (Field 4.1)** — Type: Signature. Required: Mandatory. Signed by the applicant
  **or** their authorised registered patent agent. Right column: `Signature. ……`
- **Name of signatory (Field 5.1)** — Type: Text. Required: Mandatory. (Row 5.)
- **Date (Field 3.4)** — Type: Date. Required: Mandatory. ("Dated this … day of … 20…" in Row 3.)
- **Place** — *Not present as a distinct field on Form 3* (only the addressee location "at …"
  in the footer). Do not invent a Place field.
- **Capacity (applicant vs patent agent)** — Implied by Row 4's label ("applicant or his
  authorized registered patent agent"). Recommend an app-level toggle to record the signing
  capacity; not a printed field.

---

## Special Notes

- **Strike-out instruction (footnote):** `Note. - Strike out whichever is not applicable.`
  Governs all Strike-out Choice fields: `I/We`, `alone/jointly with`, `same/substantially the
  same`, `has/have`, and the singular/plural of "him/her". In the app these are single-select
  controls; on export, the unselected alternative must be struck through (or omitted per the
  chosen rendering policy) to match the official form.
- **Mutually exclusive declarations:** items (ii) and (iii) of Row 2 are alternatives — exactly
  one is retained. Selecting (iii) requires ≥1 row in Table T1; selecting (ii) leaves it blank.
- **Signing authority:** may be the applicant or an authorised registered patent agent (Row 4).
- **Addressee:** the form is addressed "To The Controller of Patents, The Patent Office, at …"
  — the office location must be filled.
- **Attachments:** none intrinsic to Form 3 (it is itself a supporting document filed with the
  patent application; foreign-filing evidence is not attached to the form).
- **Fees:** No fee is prescribed on the face of Form 3 (statement/undertaking under Section 8).
- **Continuing obligation warning (UI):** Section 8 imposes an ongoing duty to update foreign
  filing particulars up to grant. The UI should surface this so users understand Form 3 may
  need to be re-filed when new foreign applications are made.
- **Two-column rendering:** the export/preview must preserve the official two-column, five-row
  table layout and reproduce all boilerplate declaration text verbatim.
