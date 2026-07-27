# Form 8A

**Official Name:** Certificate of Inventorship

**Purpose:** Used by an inventor to **request the grant of a Certificate of Inventorship** in
respect of a patent, **or** to request a **duplicate** certificate (with a statement of the
circumstances in which the original was lost, destroyed, damaged or cannot be produced).

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970)
- The Patents Rules, 2003 — **Rule 70A**

**Page count:** 1

---

## Overall Layout Notes

Two rows: Row 1 = the request (with an **"OR"** branch: original vs duplicate certificate); Row 2 =
signature plus a **mandatory identity block** (Aadhaar for Indian inventors, full address, mobile,
email). Several fields carry the OTP/redaction annotation.

---

## Sections

### Section 1 — Inventor & Patent, and Request Type

**Field 1.1 — Request type**
- Field Type: Radio Button (`Certificate of Inventorship` | `Duplicate certificate of inventorship`)
- Required: Mandatory · Repeatable: No · Auto-fill: No (user chooses).

**Field 1.2 — Name of the Inventor ("I ……")**
- Field Type: Text · Required: Mandatory · Repeatable: No
- Auto-fill: **Yes** — inventor name from Form 5 / Form 1 §4 / Certificate.

**Field 1.3 — Patent Number**
- Field Type: Text · Required: Mandatory · Auto-fill: **Yes** — from Patent Certificate.

**Field 1.4 — Statement of circumstances (duplicate only)**
- Field Type: Multi-line Text
- Required: **Conditional** — Mandatory when Field 1.1 = Duplicate ("… the original certificate of
  inventorship was lost, destroyed, damaged or cannot be produced are as follows:").
- Repeatable: No · Auto-fill: No.

### Section 2 — Signature & Mandatory Identity Block

Header: "To be signed by the inventor and the date of filing of this request." Then, under
**"(BELOW INFORMATION IS MANDATORILY REQUIRED TO BE SUBMITTED)"**:

| # | Field Label | Type | Required? | Auto-fill | Notes |
|---|---|---|---|---|---|
| 2.1 | Signature | Signature | Mandatory | No | Signed by the inventor personally |
| 2.2 | Name of the Inventor who has signed | Text | Mandatory | Yes (inventor name) | |
| 2.3 | Aadhaar number of the Inventor | Number | Conditional | No | **For Indian inventors**; sensitive PII — see notes |
| 2.4 | House No. | Text | Mandatory | Yes | Address block |
| 2.5 | Apartment/Street | Text | Mandatory | Yes | |
| 2.6 | City | Text | Mandatory | Yes | |
| 2.7 | State | Text | Mandatory | Yes | |
| 2.8 | Country | Text / Dropdown | Mandatory | Yes | |
| 2.9 | Pin Code | Number | Mandatory | Yes | |
| 2.10 | Mobile Phone | Number (phone) | Mandatory | Yes | **OTP verification mandatory — will be redacted** |
| 2.11 | Email | Text (email) | Mandatory | Yes | **OTP verification mandatory — will be redacted** |
| 2.12 | Dated this __ day of __ 20__ | Date | Mandatory | Yes (derived) | Date of filing the request |

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, at ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None (the identity block is documented as fields above, not a printed grid).

---

## Signature Block

- **Signature (Field 2.1)** — Type: Signature. Mandatory. Must be signed by the **inventor personally**
  (not merely the agent), per Row 2's heading.
- **Name of signatory (Field 2.2)** — Type: Text. Mandatory.
- **Date (Field 2.12)** — Type: Date. Mandatory.
- **Place** — not printed; do not invent.

---

## Special Notes

- **Footer note (disclaimer):** "This Certificate does not, in any manner whatsoever, confer or
  derogate from any rights under the patent." Reproduce verbatim; surface to the user.
- **Sensitive PII — Aadhaar:** Field 2.3 collects an Aadhaar number for Indian inventors. Treat as
  highly sensitive: never place in URLs/logs, mask in the UI, and follow the redaction handling the
  form implies. Required only for Indian inventors (Conditional).
- **OTP/redaction:** Mobile (2.10) and Email (2.11) require OTP verification and are redacted in the
  published record.
- **OR branch:** original vs duplicate certificate — the duplicate branch unlocks the mandatory
  statement of circumstances (Field 1.4).
- **Signed by inventor:** unlike most forms, Form 8A is signed by the inventor, not (only) the agent.
- **Fee:** no fee is printed on the face of Form 8A; confirm against the current First Schedule/Rule 70A.
