# Form 6

**Official Name:** Claim or Request Regarding Any Change in Applicant for Patent

**Purpose:** Used to claim/request that a patent application proceed in the name of a
different or additional applicant (e.g. following an assignment, agreement, operation of law,
or death of a joint applicant), and to request the Controller's direction to that effect.
**Not** for a mere change of name.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Sections 20(1), 20(4) and 20(5)**
- The Patents Rules, 2003 — **Rules 34(1), 35(1) and 36(1)**

**Page count:** 1

---

## Overall Layout Notes

Two columns: the **left column is a numbered list of instructions/footnotes (1–10)**; the
**right column is the actual form** with superscript markers (¹–¹⁰) referencing those
instructions. This spec documents the right-column fields; the left-column instructions are
captured under Special Notes. Superscript → field mapping: ¹ requester, ²(a) name, ³(b) address,
⁴(c) nationality, ⁵ current applicant, ⁶/⁷ supporting documents, ⁸ address for service,
⁹ signature, ¹⁰ name of signatory.

---

## Sections

### Section 1 — Requester & New/Changed Applicant Details

**Field 1.1 — I/We (requester)** *(marker ¹)*
- Field Type: Multi-line Text · Required: Mandatory · Repeatable: Yes
- Auto-fill: **Yes** — from assignment/agreement docs or existing applicant records.
- Validation: Strike-out Choice `I/We`.

**Field 1.2 — (a) Name** *(marker ², instruction 2: name in full, family/principal name first)*
- Field Type: Text · Required: Mandatory · Repeatable: Yes (repeat (a)–(c) per applicant, instr 1)
- Auto-fill: **Yes** — new applicant name from assignment deed / Form 16.
- Validation: full name; family name first for a natural person.

**Field 1.3 — (b) Address** *(marker ³, instruction 3: complete address incl postal index/code, state and/or country)*
- Field Type: Address / Multi-line Text · Required: Mandatory · Repeatable: Yes
- Auto-fill: **Yes** — from assignment docs.

**Field 1.4 — (c) Nationality** *(marker ⁴, instruction 4)*
- Field Type: Text / Dropdown (country) · Required: Mandatory · Repeatable: Yes
- Auto-fill: **Yes** — from docs.

### Section 2 — Application Being Transferred

**Field 2.1 — Application for patent No.**
- Field Type: Text · Required: Mandatory · Repeatable: No
- Auto-fill: **Yes** — from Form 1 / Certificate.

**Field 2.2 — Dated (of the application)**
- Field Type: Date · Required: Mandatory · Auto-fill: **Yes** — filing date.

**Field 2.3 — Made by (current applicant)** *(marker ⁵, instruction 5)*
- Field Type: Multi-line Text · Required: Mandatory · Repeatable: Yes
- Auto-fill: **Yes** — current applicant name(s) from Form 1.

**Field 2.4 — Request statement**
- Type: Static/Boilerplate — "may proceed in my/our name and further request that direction of
  the Controller, if necessary be made in that effect." Reproduce verbatim. Contains `my/our` choice.

### Section 3 — Reasons

**Field 3.1 — Reasons for making the above request**
- Field Type: Multi-line Text · Required: Mandatory · Repeatable: No · Auto-fill: No.

### Section 4 — Supporting Documents *(markers ⁶/⁷)*

Header: "I furnish the following document(s) in support of my above request:⁶" then (a)⁷,(b)⁷,(c)⁷.
- **Field 4.1 — Document (a)/(b)/(c)** — Field Type: Text (details of each document) · Required:
  Mandatory (at least one) · Repeatable: Yes · Auto-fill: **Yes** — list uploaded supporting docs.
- Validation (instr 6): "Original and certified copies of the documents shall accompany the claim
  or request. Consent by the legal representative of the deceased joint applicant shall be filed
  whenever required." (instr 7: insert the details of the documents.)

### Section 5 — Address for Service *(marker ⁸)*

**Field 5.1 — My/our address for service in India** *(instruction 8: complete address incl postal
index number/code and state along with Telephone and fax number(s))*
- Field Type: Address / Multi-line Text · Required: Mandatory · Repeatable: No
- Auto-fill: **Yes** — from agent/applicant records. Validation: must be in India; include phone/fax.

### Section 6 — Date & Signature

`Dated this …… day of ……, 200_` — see Signature Block.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, At ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None. (Applicant details (a)–(c) repeat as blocks, not a printed grid.)

---

## Signature Block

- **Date** — `Dated this … day of …, 200_` — Type: Date. Mandatory.
- **Signature (marker ⁹, instruction 9)** — Type: Signature. Mandatory. Signed by the applicant(s)
  or authorised registered patent agent.
- **Name of the natural person who has signed (marker ¹⁰, instruction 10)** — Type: Text. Mandatory.
- **Place** — not a distinct printed field; do not invent.

---

## Special Notes

- **N.B. (warning):** "This form is **not** applicable for mere change of name." Surface prominently
  in the UI — a name change uses a different mechanism.
- **Note (a):** "Strike out whichever is not applicable." → governs `I/We`, `my/our`, etc.
- **Note (b):** "For fee:- See First Schedule." A prescribed fee applies.
- **Left-column instructions (1–10)** are printed guidance and map to the superscript markers; they
  should be surfaced as inline help text in the editor, not as separate fields.
- **Attachments required:** original and certified copies of the supporting documents (assignment/
  agreement/etc.); consent of the legal representative of a deceased joint applicant where relevant.
