# Form 18

**Official Name:** Request / Express Request for Examination of Application for Patent

**Purpose:** Used to request that a patent application be **examined** under Sections 12 and 13.
Covers three cases: an ordinary request by the applicant, an **express** request (PCT national-
phase, examined without waiting for the 31-month period), and a request by any other interested
person.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 11B**
- The Patents Rules, 2003 — **Rules 20(4)(ii) and 24B(1)(i)**

**Page count:** 1

---

## Overall Layout Notes

Single-column, sectioned form (1–4) with a **FOR OFFICE USE ONLY** header block. Section 2 has an
**"Or"** branch (ordinary vs express request); Section 3 is for a request by an interested person
(distinct from the applicant). *(Related: Form 18A is the separate "Expedited Examination" form.)*

---

## Section 0 — For Office Use Only (Header)

Read-only, completed by the office; reproduce on preview.

| Field | Type | Notes |
|---|---|---|
| RQ. No | Text | Office allotted |
| Filing Date | Date | Office |
| Amount of Fee Paid | Number (currency) | Office |
| CBR No | Text | Office |
| Signature | Signature | Office |

---

## Sections

### Section 1 — Applicant(s) / Other Interested Person

| # | Field Label | Type | Required? | Auto-fill | Notes |
|---|---|---|---|---|---|
| 1.a | NAME | Text | Mandatory | Yes (Form 1) | |
| 1.b | NATIONALITY | Text / Dropdown | Mandatory | Yes | |
| 1.c | ADDRESS | Address / Multi-line Text | Mandatory | Yes | |
| 1.d | Date of publication of the application under section 11A | Date | Conditional | Partial (publication record) | |

### Section 2 — Request by the Applicant(s) (ordinary **Or** express)

**Field 2.0 — Request mode** — Radio Button (`Ordinary request` | `Express request (PCT)`). Mandatory.

**Ordinary request:** "I/We hereby request that my/our application for patent no. …… filed on ……
for the …… invention titled …… shall be examined under sections 12 and 13 of the Act."
- **Field 2.1 — Application for patent no.** — Text · Conditional (Mandatory if applicant request) · Auto-fill: **Yes** (Form 1).
- **Field 2.2 — Filed on (date)** — Date · Conditional · Auto-fill: **Yes** (filing date).
- **Field 2.3 — Title of the invention** — Text · Conditional · Auto-fill: **Yes** (Form 1 §5 / Form 2).

**Express request (Or):** "I/We hereby make an express request that my/our application for patent no.
…… filed on …… based on Patent Cooperation Treaty (PCT) application no. …… dated …… made in country
…… shall be examined under sections 12 and 13 of the Act, immediately without waiting for the expiry
of 31 months as specified in rule 20(4)(ii)."
- **Field 2.4 — PCT application no.** — Text · Conditional (express) · Auto-fill: **Yes** (PCT docs).
- **Field 2.5 — PCT dated** — Date · Conditional · Auto-fill: **Yes**.
- **Field 2.6 — Made in country** — Text / Dropdown · Conditional · Auto-fill: **Yes**.

### Section 3 — Request by Any Other Interested Person

"I/We the interested person request for the examination of the application no. …… dated …… filed by
the applicant …… titled …… under sections 12 and 13 of the Act. As an evidence of my/our interest in
the application for patent following documents are submitted. (a) ……"
- **Field 3.1 — Application no.** — Text · Conditional (Mandatory if interested-person request) · Auto-fill: **Yes**.
- **Field 3.2 — Dated** — Date · Conditional · Auto-fill: **Yes**.
- **Field 3.3 — Filed by the applicant** — Text · Conditional · Auto-fill: **Yes**.
- **Field 3.4 — Title** — Text · Conditional · Auto-fill: **Yes**.
- **Field 3.5 — Evidence of interest (documents) (a)…** — Text (list) · Conditional · Repeatable: Yes · Auto-fill: **Yes**.

### Section 4 — Address for Service
- **Field 4.1 — Address for service** — Address / Multi-line Text · Mandatory · Auto-fill: from agent/applicant.

### Section 5 — Date, Signature & Signatory
- **Field 5.0 — Dated this __ day of __ 20__** — Date · Mandatory.
- **Signature / Name of the signatory** — see Signature Block.
- **Addressee:** `To, The Controller of Patents — The Patent Office, at ……` — Field: Patent Office
  location (Dropdown: Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None. (Evidence documents in Section 3 form a short repeatable list.)

---

## Signature Block

- **Date (Field 5.0)** — Type: Date. Mandatory.
- **Signature** — Type: Signature. Mandatory. Signed by the applicant(s) or authorised registered patent agent.
- **Name of the signatory** — Type: Text. Mandatory.
- **Place** — not printed; do not invent.

---

## Special Notes

Transcribed **NOTE** block:
- "To be signed by the applicant(s) or by his authorized registered patent agent."
- "Strike out the column which is/are not applicable." → the three request scenarios (2 ordinary, 2
  express, 3 interested-person) are alternatives; retain only the applicable one.
- "For fee : See First Schedule." A prescribed fee applies (examination request).

UI notes:
- **Three mutually relevant scenarios** — applicant/ordinary, applicant/express (PCT), interested
  person. The editor should select one scenario and show only its fields.
- **Deadline awareness:** the ordinary request for examination is time-bound (rule 24B); surface the
  due date. The express PCT request skips the 31-month wait (rule 20(4)(ii)).
- **Distinguish from Form 18A** (Expedited Examination) — different eligibility and fee.
