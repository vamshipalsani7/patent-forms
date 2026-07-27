# Form 4

**Official Name:** Request for Extension of Time or Condonation of Delay

**Purpose:** Used to request an extension of time, or condonation of delay, in respect of an
act or step under the Act/Rules, in connection with a specified application or patent, stating
the period sought, the enabling section/rule, and the reasons.

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Sections 53(2) and 142(4)**
- The Patents Rules, 2003 — **Rules 12(5), 13(6), 24B(6), 24C(11), 80(1A), 130, 131(2) and 138**

**Page count:** 1

---

## Overall Layout Notes

Two-column table with three numbered rows plus footer. The right column of Row 1 is a single
pre-printed declaration paragraph with several inline blanks.

---

## Sections

### Section 1 — Request (Row 1)

**Left-column label:** `1. Name of the applicant`
**Right-column text:** `I/We …… hereby request for extension of time for …… month(s) under
section/rule …… in connection with my/our/application/Patent No …… The reasons for making the
request are as follows:- …… Dated this …… day of …… 20…`

**Field 1.1 — Name of the applicant (I/We)**
- Field Type: Multi-line Text
- Required?: Mandatory
- Repeatable?: Yes
- Auto-fill Opportunity: **Yes** — applicant name(s) from Form 1 / Specification / Certificate.
- Validation Notes: Contains Strike-out Choice `I/We`.

**Field 1.2 — Extension period (months)**
- Field Type: Number (months)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: No
- Validation Notes: Positive integer; must be within the maximum allowed by the cited section/rule.

**Field 1.3 — Under section / rule**
- Field Type: Text (or Dropdown of the enabling provisions listed in the legal reference)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — suggest the section/rule based on the act being extended.
- Validation Notes: Should be one of the provisions in the header citation.

**Field 1.4 — Application / Patent No.**
- Field Label: `my/our/application/Patent No.`
- Field Type: Text
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes** — application/patent number from uploaded docs.
- Validation Notes: Contains Strike-out Choice `application / Patent` (and `my/our`).

**Field 1.5 — Reasons for the request**
- Field Type: Multi-line Text
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: No
- Validation Notes: Free text justification.

**Field 1.6 — Dated this __ day of __ 20__**
- Field Type: Date
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — preparation/signing date.

### Section 2 — Signature (Row 2)
**Left-column label:** `2. To be signed by the applicant or his authorized registered patent agent`
See **Signature Block**.

### Section 3 — Name of Signatory (Row 3)
**Left-column label:** `3. Name of the natural person who has signed`
- **Field 3.1 — Name of the natural person who has signed** — Type: Text. Required: Mandatory.
  Repeatable: No. Auto-fill: **Yes** from Form 1 / Form 26. Validation: natural person's full name.

### Footer — Addressee
`To — The Controller of Patents, The Patent Office, at ……`
- **Field F.1 — Patent Office location** — Dropdown (Delhi / Mumbai / Chennai / Kolkata). Mandatory.

---

## Tables

None.

---

## Signature Block

- **Signature (Field 2.1)** — Type: Signature. Required: Mandatory. Signed by applicant or
  authorised registered patent agent. Right column: `Signature ( …… )`.
- **Name (Field 3.1)** — Type: Text. Required: Mandatory (Row 3).
- **Date (Field 1.6)** — Type: Date. Required: Mandatory (within Row 1).
- **Place** — not a distinct field; do not invent.

---

## Special Notes

- **Fee (footnote):** `Note. - For fee: See First Schedule.` A prescribed fee applies; amount per
  the First Schedule (often scaled by the number of months requested and applicant category).
- **Strike-out choices:** `I/We`, `my/our`, `application/Patent`, `section/rule`.
- **Attachments:** none prescribed on the face; supporting evidence for the delay may accompany.
- **UI note:** the enabling `section/rule` (Field 1.3) should be selectable from the provisions in
  the legal-reference citation, and may drive the fee and the maximum permissible extension.
