# Form 12

**Official Name:** Request for Grant of Patent Under Section 26(1) & 52(2)

**Purpose:** Used by a person who succeeded in an opposition (s.25(3)) or a revocation petition
(s.64) to request the grant of a patent to themselves — in lieu of a revoked patent, or in
respect of subject matter excluded by an amendment — supported by the order and a certified copy.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Sections 26(1) & 52(2)**
- The Patents Rules, 2003 — **Rules 63A and 79**

**Page count:** 2

---

## Overall Layout Notes

Two columns: left = numbered instructions (1–9); right = the form. The declaration has five
sub-parts (i)–(v). Applicant block (a)–(c) repeats per applicant (instruction 1).

---

## Sections

### Section 1 — Applicant(s)

- **Field 1.0 — I/We** *(marker ¹)* — Multi-line Text · Mandatory · Strike-out `I/We`.
- **Field 1.1 — (a) Name** *(marker ²; instr 2: name in full, family/principal name first)* — Text ·
  Mandatory · Repeatable: Yes · Auto-fill: **Yes**.
- **Field 1.2 — (b) Address** *(marker ³; instr 3: complete address incl postal code and state and/or country)* —
  Address / Multi-line Text · Mandatory · Repeatable: Yes · Auto-fill: **Yes**.
- **Field 1.3 — (c) Nationality** *(marker ⁴; instr 4)* — Text / Dropdown · Mandatory · Repeatable: Yes ·
  Auto-fill: **Yes**.

### Section 2 — Declaration (i): Prior Opposition / Petition

Pre-printed: "hereby declare: (i) that I/We made opposition under section 25(3) before the Controller
or a petition under Section 64 of the Act before the Appellate Board or High Court of⁵ …… and the
details of the patent and the opposition for the petition are given below:"

- **Field 2.1 — Name of the High Court / forum** *(instruction 5; marker ⁵)* — Text · Conditional ·
  Auto-fill: No.
- **Field 2.2 — Patent No.** — Text · Mandatory · Auto-fill: **Yes** (from Certificate of the opposed patent).
- **Field 2.3 — Dated (of the patent)** — Date · Mandatory · Auto-fill: **Yes**.
- **Field 2.4 — Grantee / Patentee** — Text · Mandatory · Auto-fill: **Yes** (Strike-out `Grantee / Patentee`).
- **Field 2.5 — Opposition Notice dated** — Date · Conditional · Auto-fill: No.
- **Field 2.6 — Petition No.** — Text · Conditional · Auto-fill: No.
- **Field 2.7 — Petition dated** — Date · Conditional · Auto-fill: No.

### Section 3 — Declaration (ii): Claim to Inventorship

Pre-printed: "that I/We have claimed to be the true and first inventor(s)/assignee(s)/legal
representative(s) of⁶ …… the true and first inventor of the invention for which the said patent was
granted."
- **Field 3.1 — Capacity** — Radio/Strike-out (`true and first inventor(s)` | `assignee(s)` |
  `legal representative(s)`) · Mandatory · Auto-fill: No.
- **Field 3.2 — Name of the true and first inventor** *(instruction 6; marker ⁶)* — Text · Mandatory ·
  Auto-fill: **Yes** (from Form 5 / prior patent).

### Section 4 — Declaration (iii): Order Outcome

Pre-printed: "that by an order in the said opposition or petition the patent was revoked/the complete
specification of the patent was directed to be amended by exclusion of …… claims thereof."
- **Field 4.1 — Outcome** — Radio/Strike-out (`patent was revoked` | `complete specification directed
  to be amended by exclusion of claims`) · Mandatory.
- **Field 4.2 — Number/identity of excluded claims** — Text · Conditional (if amendment-by-exclusion) · Auto-fill: No.

### Section 5 — Declaration (iv): Grant in Lieu

Static/Boilerplate: "that the Controller or Appellate Board or Court ordered to grant to me a patent
in lieu of the said patent/part of the invention excluded by the amendment." (Strike-out `patent /
part of the invention`.) Required: Mandatory (reproduce).

### Section 6 — Declaration (v): Statement & Certified Copy

Static/Boilerplate: "that I/We submit a statement and certified copy of the order of the Controller
or Appellate Board or Court in support of my application and request that a patent be granted to me
in accordance with the order of the Appellate Board or Court." Required: Mandatory. Implies an
attachment (order + certified copy).

### Section 7 — Address for Service *(instruction 7; marker ⁷)*

**Field 7.1 — My/Our address for service in India** — Address / Multi-line Text · Mandatory · Auto-fill: from agent.

### Section 8 — Date, Signature & Signatory
`Dated this …… day of …… 200_` — see Signature Block.
- Instruction 8: "To be signed by the applicant(s) or his authorised registered patent agent."
- Instruction 9 / **Field 8.1 — Name of the natural person who has signed** — Text · Mandatory.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, At ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

**Inline patent/opposition details** (Section 2) function as a small fixed record rather than a
repeatable grid: Patent No., Dated, Grantee/Patentee, Opposition Notice dated / Petition No. + dated.
Not multi-row.

---

## Signature Block

- **Date** — Type: Date. Mandatory.
- **Signature (marker ⁸)** — Type: Signature. Mandatory. Applicant(s) or authorised registered patent agent.
- **Name of the natural person who has signed (marker ⁹)** — Type: Text. Mandatory.
- **Place** — not printed; do not invent.

---

## Special Notes

- **Note (a):** "Strike out whichever is not applicable." → governs the many alternatives
  (revoked/amended, inventor/assignee/legal rep, patent/part, Grantee/Patentee, etc.).
- **Note (b):** "For fee : See First Schedule." A prescribed fee applies.
- **Attachments required:** a statement and a **certified copy of the order** of the Controller /
  Appellate Board / Court (declaration (v)).
- **Complex conditional logic:** declarations (i)–(v) encode a specific post-opposition/post-revocation
  scenario; the editor should walk the user through the branch that matches their order.
