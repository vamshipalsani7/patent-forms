# Form 18A

**Official Name:** Request for Expedited Examination of Application for Patent

**Purpose:** Used to request **expedited** examination of a patent application under Rule 24C. The
applicant states the request (ordinary / PCT-express / conversion of an existing Form 18 request),
ticks the eligibility ground(s), and submits the mandatory evidence for the chosen ground.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 11B**
- The Patents Rules, 2003 — **Rule 24C**

**Page count:** 3

---

## Overall Layout Notes

- **FOR OFFICE USE ONLY** header block, then Sections 1–4 plus address-for-service, signature and note.
- **Section 2** offers **three mutually exclusive request statements** (joined by "or").
- **Section 3** is a set of **eligibility-ground checkboxes** (document each individually).
- **Section 4** is a **reference table** mapping each ground to the mandatory evidence document(s).
- *(Related: Form 18 is the ordinary/express request for examination; 18A is specifically the
  **expedited** route under rule 24C, with eligibility grounds and evidence.)*

---

## Section 0 — For Office Use Only (Header)

Read-only, completed by the office; reproduce on preview.

| Field | Type | Notes |
|---|---|---|
| RQ No. | Text | Office allotted |
| Filing Date | Date | Office |
| Amount of fee Paid | Number (currency) | Office |
| CBR no | Text | Office |
| Signature | Signature | Office |

---

## Sections

### Section 1 — Applicant(s)

| # | Field Label | Type | Required? | Auto-fill |
|---|---|---|---|---|
| 1.A | NAME | Text | Mandatory | Yes (Form 1) |
| 1.B | NATIONALITY | Text / Dropdown | Mandatory | Yes |
| 1.C | ADDRESS | Address / Multi-line Text | Mandatory | Yes |

### Section 2 — Request Statement (choose one of three)

**Field 2.0 — Request type** — Radio Button:
1. **Ordinary:** "…request that my/our application for patent no. …… filed on …… for the …… invention
   titled …… shall be examined under sections 12 and 13 of the Act."
2. **PCT-express:** "… based on Patent Cooperation Treaty (PCT) application no. …… dated …… made in
   country …… shall be examined … immediately without waiting for the expiry of 31 months as specified
   in rule 20(4)(ii)."
3. **Conversion:** "…request that my/our request for examination bearing no. …… for application for
   patent no. …… filed on …… for the …… invention titled …… may be converted to a request for expedited
   examination of patent application under rule 24C …"

Conditional sub-fields (Mandatory for the selected branch):
- **2.1 — Application for patent no.** — Text · Auto-fill: **Yes** (Form 1).
- **2.2 — Filed on (date)** — Date · Auto-fill: **Yes**.
- **2.3 — Invention title** — Text · Auto-fill: **Yes** (Form 1 §5 / Form 2).
- **2.4 — PCT application no.** *(branch 2)* — Text · Auto-fill: **Yes** (PCT docs).
- **2.5 — PCT dated** *(branch 2)* — Date · Auto-fill: **Yes**.
- **2.6 — Made in country** *(branch 2)* — Text / Dropdown · Auto-fill: **Yes**.
- **2.7 — Existing request-for-examination no.** *(branch 3)* — Text · Auto-fill: **Partial** (from Form 18/RQ).

### Section 3 — Eligibility Grounds (tick the applicable box)

Each is a **Checkbox** (document individually; several grounds are alternatives — at least one applies).
Required?: at least one Mandatory. Auto-fill: **Partial (derived)** — infer from applicant category
(Form 1 §3B) / uploaded evidence; user confirms.

| # | Ground (verbatim) |
|---|---|
| 3.1 | that India has been indicated as the competent International Searching Authority or elected as an International Preliminary Examining Authority in the corresponding international application |
| 3.2 | that the applicant is a startup |
| 3.3 | that the applicant is a small entity |
| 3.4 | that the applicant is a natural person or in the case of joint applicants, all the applicants are natural persons, then applicant or at least one of the applicants is a female |
| 3.5 | that the applicant is an institution established by a Central, Provincial or State Act, which is owned or controlled by the Government |
| 3.6 | that the applicant is a Government company as defined in clause (45) of section 2 of the Companies Act, 2013 (18 of 2013); or that the applicant is an institution wholly or substantially financed by the Government |
| 3.7 | that the application pertains to a sector which has been notified by the Central Government, on the basis of a request from the head of department of the Central Government |
| 3.8 | that the applicant is eligible under an arrangement for processing a patent application pursuant to an agreement between Indian Patent Office and a foreign Patent Office |

### Section 4 — Mandatory Evidence of Eligibility → see **Table T1**.

### Address for Service in India
- **Field 5.1 — Address for service in India** — Address / Multi-line Text · Mandatory · Auto-fill: from agent/applicant.

### Date, Signature & Signatory
- **Dated this __ day of __ 20__** — Date · Mandatory.
- **Signature / Name of the signatory** — see Signature Block.
- **Addressee:** `To — The Controller of Patent, The Patent Office, at ……` — Field: Patent Office
  location (Dropdown: Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

### Table T1 — Mandatory Evidence of Eligibility (Section 4)

Reference table: the document(s) that must be submitted for each ground. Not user-repeatable; the
row applicable to the selected Section-3 ground drives a required attachment.

| Ground | Required evidence |
|---|---|
| a. India as competent ISA / elected IPEA | Relevant ISA number issued by ISA, India / relevant IPEA number issued by IPEA, India |
| b. Startup | Indian applicant: certificate of recognition as a startup from DPIIT. Foreign entity: any document as evidence of eligibility |
| c. Small entity | Indian applicant: evidence of registration under the MSME Act, 2006 (27 of 2006). Foreign entity: any document as evidence |
| d. Natural person / female applicant | Indian & foreign: photo identity card of the female applicant issued by competent authority |
| e. Department of the Government | Indian & foreign: any document as evidence of eligibility |
| f. Institution established by Central/Provincial/State Act, owned/controlled by Govt | Indian & foreign: any document as evidence of eligibility |
| g. Government company (s.2(45), Companies Act 2013) | Indian & foreign: any document as evidence of eligibility |
| h. Institution wholly/substantially financed by Govt | Indian & foreign: any document as evidence of eligibility |
| i. Application in a Central-Government-notified sector | Notification from the Central Government and documents as may be required by the Controller |
| j. Eligible under an IPO–foreign-office arrangement | Declarations and documents as may be required by the Controller |

- **Row behaviour:** static reference (a–j). **Multiple rows allowed:** No (fixed enumeration).
- **Cross-check note:** the Section-3 checkboxes (8) combine some grounds that Table T1 enumerates
  separately (a–j = 10); notably T1 separates "Government company" (g) from "wholly/substantially
  financed institution" (h), and lists "department of the Government" (e). Preserve both as printed;
  the evidence required is keyed to Table T1's lettering.

---

## Signature Block

- **Date** — Type: Date. Mandatory.
- **Signature** — Type: Signature. Mandatory. Signed by the applicant(s) or his/their authorised
  registered patent agent.
- **Name of the signatory** — Type: Text. Mandatory.
- **Place** — not printed; do not invent.

---

## Special Notes

Transcribed **NOTE** block:
- "To be signed by the applicant(s) or by his/their authorized registered patent agent."
- "Strike out the column(s) which is/are not applicable." → request branches (Section 2) and grounds
  (Section 3).
- "For fee : See First Schedule." A prescribed (higher) fee applies for expedited examination.

UI notes:
- **Ground → evidence coupling:** selecting a Section-3 ground must require uploading the matching
  Table T1 evidence document; the editor should enforce/prompt this pairing.
- **Sensitive evidence:** ground (d) requires a **photo identity card of the female applicant** — treat
  as sensitive personal data (mask/redact, never place in URLs/logs).
- **Eligibility auto-derivation:** applicant category on Form 1 §3B (startup/small entity/natural
  person) strongly predicts the applicable ground — pre-tick, but leave the user to confirm.
- **Formatting artifact:** the source PDF wraps the title in stray quote marks (`"FORM 18A … ";`) —
  these are transcription artifacts, not part of the form.
