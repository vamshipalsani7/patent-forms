# Form 15

**Official Name:** Application for the Restoration of Patent

**Purpose:** Used by a patentee to apply for an order of the Controller **restoring a patent**
that lapsed due to non-payment of the renewal fee, explaining the circumstances of the failure
and declaring the patent has not been assigned.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 60**
- The Patents Rules, 2003 — **Rule 84**

**Page count:** 1

---

## Overall Layout Notes

Two columns: left = numbered instructions (1–3); right = the form with superscript markers.

---

## Sections

### Section 1 — Applicant Particulars *(instruction 1: name, address, nationality of the applicant(s))*

**Field 1.1 — I/We (name, address, nationality)** *(marker ¹)*
- Field Type: Multi-line Text (composite) · Required: Mandatory · Repeatable: Yes
- Auto-fill: **Yes** — patentee name/address/nationality from Certificate.
- Validation: Strike-out Choice `I/We`.

### Section 2 — Patent to be Restored

Pre-printed: "hereby apply for an order of the Controller for the restoration of Patent No. ……
dated …… granted to ……"

- **Field 2.1 — Patent No.** — Text · Mandatory · Auto-fill: **Yes** — from Certificate.
- **Field 2.2 — Dated (of the patent)** — Date · Mandatory · Auto-fill: **Yes** — grant date.
- **Field 2.3 — Granted to** — Multi-line Text · Mandatory · Auto-fill: **Yes** — patentee name(s).

### Section 3 — Circumstances of Failure to Pay Renewal Fee

Pre-printed: "The circumstances which led to the failure to pay the renewal fee for the year ……
on or before …… are as follows: ……"
*(OCR note: the source PDF shows a duplicated phrase "…the renewal fee to pay the renewal fee…";
this is an OCR artifact — the intended clause is as transcribed above.)*

- **Field 3.1 — Renewal-fee year** — Text/Number · Mandatory · Auto-fill: **Partial** — from renewal records.
- **Field 3.2 — Due date ("on or before")** — Date · Mandatory · Auto-fill: **Partial** — computed from grant/renewal schedule.
- **Field 3.3 — Circumstances (reasons)** — Multi-line Text · Mandatory · Auto-fill: No.

### Section 4 — Declarations

- **Field 4.1 — Declaration** — Static/Boilerplate: "I/We declare that I/We have not assigned the
  patent to any other person(s) and that the facts and matters stated herein are true to the best
  of my/our knowledge information and belief." Required: Mandatory.
- **Field 4.2 — Dated this __ day of __ 20__** — Date · Mandatory · Auto-fill: derived.

### Section 5 — Signature & Signatory
- Instruction 2: "To be signed by the applicant(s) or by his authorised registered patent agent."
- Instruction 3 / **Field 5.1 — Name of the natural person who has signed** — Text · Mandatory.
- See Signature Block.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, At ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None.

---

## Signature Block

- **Date (Field 4.2)** — Type: Date. Mandatory.
- **Signature (marker ², instruction 2)** — Type: Signature. Mandatory. Applicant(s) or authorised
  registered patent agent.
- **Name of the natural person who has signed (marker ³, instruction 3)** — Type: Text. Mandatory.
- **Place** — not printed; do not invent.

---

## Special Notes

- **Fee (footer):** "For fee : See First Schedule." A prescribed fee applies (restoration).
- **Strike-out:** `I/We`, `my/our`.
- **Time-bar warning (UI):** restoration under s.60 must be applied for within the statutory window
  after cessation; surface a reminder about the deadline.
- **Declaration of non-assignment** is mandatory content.
