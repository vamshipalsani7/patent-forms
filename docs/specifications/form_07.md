# Form 7

**Official Name:** Notice of Opposition

**Purpose:** Used by an opponent to give notice of **post-grant opposition** to a granted
patent, stating the opponent's particulars and the grounds of opposition.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 25(2)**
- The Patents Rules, 2003 — **Rule 55A**

**Page count:** 1

---

## Overall Layout Notes

Two columns: left = numbered instructions (1–5); right = the form with superscript markers (¹–⁵).
This spec documents the right-column fields.

---

## Sections

### Section 1 — Opponent Particulars *(instruction 1: state names, address and nationality)*

**Field 1.1 — I/We (opponent: names, address, nationality)** *(marker ¹)*
- Field Type: Multi-line Text (composite: name(s), address, nationality) · Required: Mandatory
- Repeatable: Yes · Auto-fill: **Partial** — opponent is usually a third party, not in the applicant's docs.
- Validation: Strike-out Choice `I/We`.

### Section 2 — Patent Being Opposed

Pre-printed: "hereby give notice of opposition to patent No. ……) granted on application No. ……
dated …… published on dated …… made by …… on the grounds²."

- **Field 2.1 — Patent No.** — Text · Mandatory · Auto-fill: **Yes** (from Certificate) if opposing own-tracked patent.
- **Field 2.2 — Granted on (date)** — Date · Mandatory · Auto-fill: from Certificate.
- **Field 2.3 — Application No.** — Text · Mandatory · Auto-fill: from Form 1 / Certificate.
- **Field 2.4 — Application dated** — Date · Mandatory · Auto-fill: from Form 1.
- **Field 2.5 — Published on (date)** — Date · Mandatory · Auto-fill: from publication record.
- **Field 2.6 — Made by (patentee)** — Multi-line Text · Mandatory · Auto-fill: patentee name.

### Section 3 — Grounds *(instruction 2: state the grounds one after another; marker ²)*

**Field 3.1 — Grounds of opposition**
- Field Type: Multi-line Text (each ground stated separately, "one after another")
- Required: Mandatory · Repeatable: Yes (one entry per ground) · Auto-fill: No.

### Section 4 — Address for Service *(instruction 3; marker ³)*

**Field 4.1 — My/Our address for service in India** *(complete address incl postal index number/
code and state along with Telephone and fax number)*
- Field Type: Address / Multi-line Text · Required: Mandatory · Auto-fill: from opponent's agent.

### Section 5 — Signature & Signatory

- Instruction 4: "To be signed by the opponent or by his authorized registered patent agent."
- Instruction 5 / **Field 5.1 — Name of the natural person who has signed** — Text · Mandatory.
- See Signature Block.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, At ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None.

---

## Signature Block

- **Signature (marker ⁴)** — Type: Signature. Mandatory. Signed by the opponent or authorised
  registered patent agent.
- **Name of the natural person who has signed (marker ⁵)** — Type: Text. Mandatory.
- **Date** — no explicit "Dated this…" line printed on Form 7; do not invent (record signing date at app level).
- **Place** — not printed; do not invent.

---

## Special Notes

- **Fee (footer):** "For fee : See First Schedule." A prescribed fee applies (post-grant opposition).
- **Strike-out:** `I/We`, `My/Our`.
- **Opponent context:** the opponent is typically a third party — auto-fill from the applicant's
  uploaded documents is limited to the *opposed* patent's particulars, not the opponent's identity.
- **Distinguish from Form 7A:** Form 7 is **post-grant** opposition (s.25(2)); Form 7A is the
  **pre-grant** representation (s.25(1), rule 55).
- **Attachments:** written statement and evidence in support of the opposition typically accompany
  (per the opposition procedure), though not enumerated as fields on the form face.
