# Form 31

**Official Name:** Grace Period

**Purpose:** Used by an applicant to **claim the benefit of the grace period** under Section 31 —
where a prior disclosure (display/use/publication/reading before a learned society) should not
defeat novelty — selecting the applicable limb of Section 31 and submitting the required evidence.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Section 31**
- The Patents Rules, 2003 — **Rule 29A**

**Page count:** 2

---

## Overall Layout Notes

Two-column table with five numbered rows. Section 2 is a set of **provision checkboxes** (Section
31(a)–(d)); Section 3 provides, for each selected limb, a structured **evidence block** (with
reference points a–d and a documentary-evidence free-text area). Section 4 is a mandatory undertaking.

---

## Sections

### Section 1 — Applicant & Application

Pre-printed: "I/We, the applicant ……, in respect of application number ……, filed on …… hereby claim
the benefit of grace period provided under section 31."

- **Field 1.1 — Name, address, nationality** — Multi-line Text (composite) · Mandatory · Auto-fill: **Yes** (Form 1).
- **Field 1.2 — Application number** — Text · Mandatory · Auto-fill: **Yes** (Form 1).
- **Field 1.3 — Filed on (date)** — Date · Mandatory · Auto-fill: **Yes** (filing date).

### Section 2 — Applicable Provision (checkboxes)

Document each checkbox individually. Type: Checkbox; Required?: at least one Mandatory; Repeatable?: No.

| # | Checkbox |
|---|---|
| 2.1 | Section 31(a) |
| 2.2 | Section 31(b) |
| 2.3 | Section 31(c) |
| 2.4 | Section 31(d) |

- **Auto-fill:** **Partial** — infer from the nature of the uploaded disclosure evidence; user confirms.
- **Validation:** the selected limb(s) activate the matching evidence block(s) in Section 3.

### Section 3 — Documentary Evidence (per selected limb)

Note on form: "Evidence may also include an affidavit." For each selected Section-2 limb, complete the
corresponding block. Each block's "documentary evidence submitted" is a Multi-line Text field
(Conditional — Mandatory when its limb is selected; Auto-fill: **Yes** — list uploaded evidence).

**3(i) Section 31(a) — display/use at an exhibition**
- a) **Earliest date of display or use** — Date (DDMMYYYY box) · Conditional.
- b) **Display occurred with consent of the true and first inventor / person deriving title** — YES/NO
  (Radio) · Conditional.
- c) **Display at an industrial/other exhibition to which s.31 has been extended by Central Government
  notification** — acknowledgement · Conditional.
- **3(i).evidence** — Multi-line Text · Conditional.

**3(ii) Section 31(b) — publication in consequence of display/use**
- a) **Earliest date of publication or use** — Date · Conditional.
- b) Documentary evidence in respect of s.31(a) above.
- c) Documentary evidence that the publication occurred in consequence of the display/use per s.31(b).
- **3(ii).evidence** — Multi-line Text · Conditional.

**3(iii) Section 31(c) — use without consent**
- a) **Earliest date of use** — Date · Conditional.
- b) Documentary evidence in respect of s.31(a) or (b) above.
- c) Documentary evidence regarding use of the invention per s.31(c).
- d) Documentary evidence or **affidavit** that the use occurred **without the consent** of the true and
  first inventor / person deriving title.
- **3(iii).evidence** — Multi-line Text · Conditional.

**3(iv) Section 31(d) — description before/by a learned society**
- a) **Earliest date of description or publication** — Date · Conditional.
- b) Description of the invention in a paper read by the true and first inventor before a learned society.
- c) Description published by the true and first inventor (or with consent) in the transactions of a learned society.
- **3(iv).evidence** — Multi-line Text · Conditional.

### Section 4 — Undertaking

Pre-printed: "That my invention was in the public domain from **DDMMYYYY** and this application is made
not later than 12 months from that date (earliest date as stated above in respect of section 31(a),
31(b), 31(c), or 31(d))." + "The facts and matters stated above are true to the best of my/our
knowledge, information and belief."

- **Field 4.1 — Public-domain-from date (DDMMYYYY)** — Date · Mandatory · Auto-fill: **Partial** (the earliest date from Section 3).
- **Field 4.2 — Undertaking + truth declaration** — Static/Boilerplate · Mandatory.
- **Field 4.3 — Dated this __ day of __ 20__** — Date · Mandatory.
- **Validation:** the application must be within **12 months** of the public-domain date — surface this check.

### Section 5 — Signature
- Instruction 5: "To be signed by Applicant / Authorised Agent." Note: "Affidavit, if any, shall be
  signed by the applicant." See Signature Block.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, at ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None as a grid; Section 3's per-limb structure is documented as blocks above.

---

## Signature Block

- **Date (Field 4.3)** — Type: Date. Mandatory.
- **Signature(s)** — Type: Signature. Mandatory. Applicant / Authorised Agent. **Any affidavit must be
  signed by the applicant personally** (per the Section-5 note).
- **Name** — captured via Section 1 details.
- **Place** — not printed; do not invent.

---

## Special Notes

- **Footer note:** "Select the options that are applicable." → Section-2 limbs and their evidence blocks.
- **12-month bar (UI):** Section 4 undertakes the application is filed within 12 months of the disclosure
  — the app should validate the filing date against the earliest disclosure date and warn if out of time.
- **Affidavit:** evidence may include an affidavit; where used, it must be signed by the applicant
  (not merely the agent).
- **Consent semantics differ per limb:** s.31(a)/(d) involve disclosure with consent/by the inventor;
  s.31(c) specifically concerns use **without** consent — the editor must not blur these.
- **No explicit fee note** appears on the face; confirm against the current First Schedule for Rule 29A.
