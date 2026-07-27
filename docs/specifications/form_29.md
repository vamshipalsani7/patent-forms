# Form 29

**Official Name:** Request for Withdrawal of the Application for Patent

**Purpose:** Used by an applicant to request that a patent application (and, if applicable, its
associated request for examination / expedited examination) be **treated as withdrawn**.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 11B(4)**
- The Patents Rules, 2003 — **Rules 7(4A) and 26**

**Page count:** 1

---

## Overall Layout Notes

Two-column table with three numbered rows plus a signature block. Row 1's right column is a single
pre-printed withdrawal sentence with inline blanks.

---

## Sections

### Section 1 — Withdrawal Request (Row 1)

**Left-column label:** `1. Name of the applicant`
Pre-printed: "I/We …… request that the application for patent numbered …… dated …… filed by me/us,
if applicable, having the request for examination / request for expedited examination numbered ……
dated ……, be treated as withdrawn under rule 7(4A) / 26."

- **Field 1.1 — Name of the applicant (I/We)** — Multi-line Text · Mandatory · Repeatable: Yes ·
  Auto-fill: **Yes** (Form 1). Validation: Strike-out `I/We`.
- **Field 1.2 — Application for patent numbered** — Text · Mandatory · Auto-fill: **Yes** (Form 1).
- **Field 1.3 — Dated (of the application)** — Date · Mandatory · Auto-fill: **Yes** (filing date).
- **Field 1.4 — Request for examination / expedited examination number** — Text · Conditional
  ("if applicable") · Auto-fill: **Partial** (from Form 18 / 18A / RQ). Strike-out `examination / expedited examination`.
- **Field 1.5 — RQ dated** — Date · Conditional · Auto-fill: **Partial**.
- **Field 1.6 — Withdrawal rule** — Strike-out Choice (`rule 7(4A)` | `rule 26`) · Mandatory · Auto-fill: No.
- **Field 1.7 — Dated this __ day of __** — Date · Mandatory · Auto-fill: derived.

### Section 2 — Signature (Row 2)
**Left-column label:** `2. To be signed by the applicant or his authorized registered patent agent`
See Signature Block.

### Section 3 — Name of Signatory (Row 3)
**Left-column label:** `3. Name of the natural person who has signed`
- **Field 3.1 — Name** — Text · Mandatory. Also **Designation** captured (form prints `(Name)` and
  `(Designation)` lines).

### Footer — Addressee
`To — The Controller of Patents, Patent Office at ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None.

---

## Signature Block

- **Date (Field 1.7)** — Type: Date. Mandatory.
- **Signature (Row 2)** — Type: Signature. Mandatory. Applicant or authorised registered patent agent.
- **Name (Row 3)** — Type: Text. Mandatory.
- **Designation** — Type: Text. Printed as a `(Designation)` line under the signature. Optional/Conditional.
- **Place** — not printed; do not invent.

---

## Special Notes

- **N.B.:** "strike out whichever not applicable." → `I/We`, `me/us`, `examination / expedited
  examination`, `rule 7(4A) / 26`.
- **No fee note** appears on the face of Form 29.
- **Irreversibility warning (UI):** withdrawal is a consequential, largely irreversible step — the app
  should present a strong confirmation and make clear what is being withdrawn (the application and,
  optionally, the examination request).
- **Formatting artifact:** the source wraps the title in a stray leading quote (`"FORM 29`) — a
  transcription artifact, not part of the form.
