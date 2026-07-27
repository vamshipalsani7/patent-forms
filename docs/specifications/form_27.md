# Form 27

**Official Name:** Statement Regarding the Working of Patented Invention(s) on a Commercial Scale in India

**Purpose:** The mandatory annual statement by which a patentee/licensee reports whether each
patented invention has been **worked in India** in a given financial year, and (if not worked) the
reasons, and whether the patent is available for licensing.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 146(2)**
- The Patents Rules, 2003 — **Rule 131(1)**

**Page count:** 1

**Fee:** **No Fee** (explicitly marked "No Fee" on the form face).

---

## Overall Layout Notes

Two-column table with six numbered rows. Contains a **worked/not-worked table** (Section 3),
**reason checkboxes** (Section 4), and **licensing-availability checkboxes** (Section 5). One form
may cover multiple **related** patents granted to the same patentee(s).

---

## Sections

### Section 1 — Patentee/Licensee & Patent Number(s)

Pre-printed: "I/We, the **Patentee(s)/Licensee** ……, in respect of patent number(s) ……, furnish this
statement, (Explanation: One form may be filed in respect of multiple patents, provided all of them
are related patents and are granted to the same patentee(s))."

- **Field 1.1 — Capacity** — Strike-out Choice (`Patentee(s)` | `Licensee`) · Mandatory · Auto-fill: **Partial**.
- **Field 1.2 — Name, address, nationality** *(instruction 1)* — Multi-line Text (composite) · Mandatory ·
  Auto-fill: **Yes** — from Certificate.
- **Field 1.3 — Patent number(s)** — Text · Mandatory · Repeatable: Yes · Auto-fill: **Yes** — from Certificate.
  Validation: multiple patents allowed only if **related** and granted to the same patentee(s).

### Section 2 — Financial Year

**Field 2.1 — Financial year** — Text (e.g. `2024–2025`) · Mandatory · Auto-fill: **Partial** (default to
the most recent completed financial year). Instruction: "State the financial year to which the statement relates."

### Section 3 — Worked / Not Worked → see **Table T1**.

### Section 4 — If Not Worked, Reasons (checkboxes)

Document each checkbox individually. Type: Checkbox; Required?: Conditional (Mandatory when any patent
marked "Not worked"); Repeatable?: No.

| # | Checkbox (verbatim) |
|---|---|
| 4.1 | Patented Invention is under development/ commercial trial |
| 4.2 | Patented Invention is under Review/approval with Regulatory authorities |
| 4.3 | Exploring commercial licensing |
| 4.4 | Any other, may specify: ______ |

- **Field 4.4a — "Any other" specify text** — Text · Conditional (Mandatory if 4.4 ticked) · Auto-fill: No.

### Section 5 — Availability for Licensing (checkboxes)

- **Field 5.1 — Whether the patent is available for licensing** — Checkbox pair / Radio (`YES` | `NO`) ·
  Mandatory · Auto-fill: No.
- **Conditional (if YES):** "would you be interested in receiving communications from any person
  interested in seeking a license. If so, kindly provide contact details as below:"
  - **Field 5.2 — Email address** — Text (email) · Conditional · Auto-fill: **Partial** · Notes: contact detail.
  - **Field 5.3 — Contact Number** — Number (phone) · Conditional · Auto-fill: **Partial**.

### Section 5.x — Truth Declaration & Date
- **Truth declaration** — Static/Boilerplate: "The facts and matters stated above are true to the best
  of my/ our knowledge, information and belief." Required: Mandatory.
- **Dated this __ day of __ 20__** — Date · Mandatory.

### Section 6 — Signature
- Instruction 6: "To be signed by Patentee(s) / Licensee / Authorised Agent furnishing the statement."
  See Signature Block.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, at ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

### Table T1 — Worked / Not Worked (Section 3)

| Column | Field Type | Required? | Auto-fill |
|---|---|---|---|
| Patent Number(s) | Text | Mandatory | Yes (from Certificate) |
| Worked [Tick (✓) if applicable] | Checkbox | Conditional | No |
| Not worked [Tick (✓) if applicable] | Checkbox | Conditional | No |

- **Row behaviour:** one row per patent number covered by the statement.
- **Multiple rows allowed:** **Yes** (for related patents of the same patentee).
- **Validation:** per row, exactly one of Worked / Not worked should be ticked; "Not worked" rows
  activate the Section 4 reason checkboxes.

---

## Signature Block

- **Date** — Type: Date. Mandatory.
- **Signature(s)** — Type: Signature. Mandatory. Signed by Patentee(s) / Licensee / Authorised Agent.
  Repeatable (multiple patentees).
- **Name** — captured via Section 1 details.
- **Place** — not printed; do not invent.

---

## Special Notes

- **No Fee:** explicitly marked "No Fee" — do **not** attach a fee step to this form.
- **Annual statutory obligation (UI):** Form 27 must be filed for every financial year in which the
  patent was in force (per Rule 131). Surface reminders — non-filing carries penalties. This is a
  strong candidate for the app's reminder/queue behaviour (as a *supporting* feature to form prep).
- **Multi-patent rule:** one form may cover several patents only if they are **related** and share the
  same patentee(s) — validate before combining.
- **Strike-out:** `Patentee(s)/Licensee`, `my/our`.
- **Contact details (5.2/5.3):** collected only when the patent is offered for licensing; treat as
  contact PII.
