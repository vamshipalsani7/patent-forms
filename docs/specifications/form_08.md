# Form 8

**Official Name:** Request or Claim Regarding Mention of Inventor as Such in a Patent

**Purpose:** Used either (a) to request/claim that a person be **mentioned as an inventor** in a
patent application/patent, **or** (b) to declare that a named person **ought not** to have been
mentioned as inventor, and to apply for a certificate to that effect. A statement of circumstances
is attached.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Sections 28(2), 28(3) and 28(7)**
- The Patents Rules, 2003 — **Rules 66, 67 and 68**

**Page count:** 1

---

## Overall Layout Notes

Two columns: left = numbered instructions (1–5); right = the form with superscript markers.
The right column offers **two mutually exclusive declarations** joined by "or" (be mentioned /
ought not to have been mentioned).

---

## Sections

### Section 1 — Applicant Particulars *(instruction 1: names, address, nationality of the person making this application)*

**Field 1.1 — I/We (name, address, nationality)** *(marker ¹)*
- Field Type: Multi-line Text (composite) · Required: Mandatory · Repeatable: Yes
- Auto-fill: **Partial** — from applicant/inventor records if the requester is a party on file.
- Validation: Strike-out Choice `I/We`.

### Section 2 — Declaration (choose one)

**Field 2.1 — Declaration type**
- Field Type: Radio Button:
  - `state/claim that the following person(s) be mentioned as inventor(s)`, **or**
  - `declare that [person] ought not to have [been] mentioned as inventor … and apply for a certificate to that effect`
- Required: Mandatory · Repeatable: No · Auto-fill: No.

**Field 2.2 — Person to be mentioned / not to be mentioned as inventor** *(instruction 2; marker ²)*
- Field Type: Text (name) · Required: Mandatory · Repeatable: Yes · Auto-fill: **Partial** — inventor
  names from Form 5 / Form 1 §4.

**Field 2.3 — Patent application / Patent No.**
- Field Type: Text · Required: Mandatory · Auto-fill: **Yes** — from Form 1 / Certificate.

**Field 2.4 — Dated (of the application/patent)**
- Field Type: Date · Required: Mandatory · Auto-fill: **Yes** — filing/grant date.

**Field 2.5 — Made by (applicant/patentee)**
- Field Type: Multi-line Text · Required: Mandatory · Auto-fill: **Yes** — applicant name.

**Field 2.6 — Attached statement of circumstances**
- Type: Static/Boilerplate — "A Statement setting out the circumstances under which this
  application is made is attached together with the copy/copies thereof as required under the rules."
- Required: Mandatory (the statement is an attachment — see Special Notes).

### Section 3 — Address for Service *(instruction 3; marker ³)*

**Field 3.1 — My/Our address for service in India** *(complete address incl postal index number/
code and state along with Telephone and fax number(s))*
- Field Type: Address / Multi-line Text · Required: Mandatory · Auto-fill: from agent/applicant.

### Section 4 — Date & Signature
`Dated this …… day of …… 20_` — see Signature Block.

### Section 5 — Name of Signatory *(instruction 5; marker ⁵)*
**Field 5.1 — Name of the natural person who has signed** — Text · Mandatory.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, At ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None.

---

## Signature Block

- **Date** — `Dated this … day of … 20_` — Type: Date. Mandatory.
- **Signature (marker ⁴, instruction 4)** — Type: Signature. Mandatory. Signed by the applicant or
  authorised registered patent agent.
- **Name of the natural person who has signed (marker ⁵)** — Type: Text. Mandatory.
- **Place** — not printed; do not invent.

---

## Special Notes

- **Fee (footer):** "For fee : See First Schedule." A prescribed fee applies.
- **Strike-out:** `I/We`, `My/Our`, `state/claim`.
- **Two purposes:** the form serves both the *inclusion* and the *exclusion* of an inventor mention;
  the UI must present these as a clear single-choice and adjust wording accordingly.
- **Attachment required:** a statement setting out the circumstances (with copies) must accompany the
  request.
