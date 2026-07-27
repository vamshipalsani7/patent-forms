# Form 30

**Official Name:** To Be Used When No Other Form Is Prescribed

**Purpose:** A **generic/catch-all** form for any request to the Patent Office for which no specific
form is prescribed. The user states the relevant provision, the purpose, and the details of the request.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970)
- The Patents Rules, 2003 — **Rule 8, sub-rule (2)**

**Page count:** 1

---

## Overall Layout Notes

Two-column table with eight numbered rows. Because it is a catch-all, its fields are deliberately
general (purpose + details as free text). This is the one form whose *content* is genuinely
open-ended — but its **field set is still fixed** and must not be conflated with any other form.

---

## Sections

### Section 1 — Applicant / Patentee / Other

**Left-column label:** `1. Name of the Applicant/Patentee/Other`
- **Field 1.1 — I/We (name)** — Multi-line Text · Mandatory · Repeatable: Yes · Auto-fill: **Yes** (Form 1 / Certificate).
  Strike-out `Applicant/Patentee/Other`.

### Section 2 — Complete Address

**Left-column label:** `2. Complete address including postal index number/code and State along with
e-mail ID, telephone, mobile and fax number.` → see **Table T1 — Address block**.

### Section 3 — Application No. / Patent No.
- **Field 3.1** — Text · Mandatory · Auto-fill: **Yes** (Form 1 / Certificate). Strike-out `Application No. / Patent No.`

### Section 4 — Relevant Section / Rules
- **Field 4.1** — Text · Mandatory · Auto-fill: No · Notes: the statutory provision under which the request is made.

### Section 5 — Purpose of Request
- **Field 5.1** — Multi-line Text · Mandatory · Auto-fill: No.

### Section 6 — Details of Request
- **Field 6.1** — Multi-line Text · Mandatory · Auto-fill: No.

### Section 7 — Signature
**Left-column label:** `7. To be signed by applicant` — See Signature Block.

### Section 8 — Signatory
**Left-column label:** `8. Name of the natural person who has signed along with designation and
official seal, if any.`
- **Field 8.1 — Name (+ designation, official seal if any)** — Text · Mandatory.

### Footer — Addressee
`To, The Controller of Patents, The Patent Office, at ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

### Table T1 — Address block (Section 2)

Rendered on the form as a grid of labelled cells:

| Field | Type | Required? | Auto-fill |
|---|---|---|---|
| House No. | Text | Mandatory | Yes |
| Street | Text | Mandatory | Yes |
| City | Text | Mandatory | Yes |
| State | Text | Mandatory | Yes |
| Country | Text / Dropdown | Mandatory | Yes |
| Pin code | Number | Mandatory | Yes |
| Telephone No. | Number (phone) | Optional | Yes |
| Mobile No. | Number (phone) | Mandatory | Yes |
| Fax No. | Number | Optional | Yes |
| E-mail ID | Text (email) | Mandatory | Yes |

- **Row behaviour:** a single address block (not multi-row).

---

## Signature Block

- **Signature (Section 7)** — Type: Signature. Mandatory. Signed by the applicant.
- **Name (Section 8)** — Type: Text, with **designation and official seal if any**. Mandatory.
- **Date** — no explicit "Dated this…" line is printed on Form 30; do not invent (record signing date at app level).
- **Place** — not printed; do not invent.

---

## Special Notes

- **Catch-all nature:** use only when no specific form fits. The editor should make clear this is the
  fallback; the "Relevant section/rules", "Purpose", and "Details" fields carry the substance.
- **No fee note** is printed on the face; the applicable fee (if any) depends on the underlying request
  — surface a caution to check the First Schedule for the specific action.
- **Strike-out:** `Applicant/Patentee/Other`, `Application No./Patent No.`
- **Do not template the content:** unlike other forms, avoid pre-filling Purpose/Details with canned
  text — the whole point is that the request is bespoke. Auto-fill only the identity/address/number fields.
- **Formatting artifact:** the source ends the addressee line with a stray `".` — a transcription artifact.
