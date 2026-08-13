# IPO Form Specifications

Developer specifications for the official Indian Patent Office (IPO) forms, derived
**directly and only** from the official PDFs in `docs/`. These markdown files are the
permanent source of truth for implementing each form's editor, pre-fill, preview, and
export in the Patent Forms application.

> **Source of truth.** Every spec is transcribed from the corresponding government PDF
> in `docs/`. Fields are never invented, never omitted, and never rearranged. Where the
> official form is ambiguous or the source scan has an OCR artifact, the spec says so
> explicitly rather than guessing.

> **Machine schema.** These human-readable specs are the source; the generic, form-agnostic
> **Form Definition schema** derived from them lives in [`schema/`](schema/README.md) — one
> JSON Schema that every form-definition file validates against.

---

## How to read these specs

Each file documents one form and follows a fixed structure:

- **Header block** — Form number, official name, purpose, legal reference, page count.
- **Sections** — in the exact order they appear on the form, each with title + description.
- **Fields** — every field in order, each with the attributes below.
- **Tables** — documented separately (columns, row behaviour, multiplicity).
- **Checkboxes** — documented individually, never combined.
- **Signature block** — each component (signature, name, date, place, capacity) separately.
- **Special Notes** — attachments, strike-out instructions, footnotes, fees, warnings, UI notes.

### Per-field attributes

| Attribute | Allowed values |
|---|---|
| **Field Type** | Text, Number, Date, Checkbox, Radio Button, Dropdown, Table, Signature, Address, Multi-line Text, Strike-out Choice, Static/Boilerplate |
| **Required?** | Mandatory, Optional, Conditional, Unknown |
| **Repeatable?** | Yes, No |
| **Auto-fill Opportunity** | Whether/how the field can be pre-filled from uploaded patent documents |
| **Validation Notes** | Obvious validations implied by the form |

### Project-specific field-type conventions

- **Strike-out Choice** — the official paper form prints two or more alternatives
  (e.g. `I/We`, `alone/jointly`, `has/have`) and instructs the filer to strike out the
  inapplicable one. In the app this is a single-select (radio/toggle) control. Documented
  as *Strike-out Choice* to preserve the official wording.
- **Static/Boilerplate** — pre-printed declaration/undertaking text with no user input.
  Documented because the exported form must reproduce it verbatim, but it is not an editable field.
- **Address** — a composite (name/street/city/state/country/postcode) rendered as one logical field.

> **Governing principle (from the product vision):** the software *suggests*, the user
> *decides*. Every field — including auto-filled ones — must remain fully editable and is
> never locked. Auto-fill columns describe opportunity only, never enforcement.

### Recurring patterns across forms

- **Addressee:** almost every form ends "To — The Controller of Patents, The Patent Office,
  at ……". Modelled as a **Patent Office location** dropdown (Delhi / Mumbai / Chennai / Kolkata).
- **Signatory:** most forms are signed by the applicant **or** an authorised registered patent
  agent, followed by "Name of the natural person who has signed".
- **Fee:** most forms footnote "For fee: See First Schedule"; a few are explicitly **No Fee**
  (Form 27) or carry other requirements (Form 26 is stamped under the Indian Stamp Act).
- **OTP/redaction:** the amended Form 1, Form 8A and others mark email/phone fields
  "OTP verification mandatory — will be redacted" — treat as sensitive.

---

## Form index & status

All 35 forms transcribed from `docs/`. Legend: ✅ complete.

| Form | File | Official name (as transcribed) | Status |
|---|---|---|---|
| 1 | `form_01.md` | Application for Grant of Patent | ✅ |
| 2 | `form_02.md` | Provisional / Complete Specification | ✅ |
| 3 | `form_03.md` | Statement and Undertaking Under Section 8 | ✅ |
| 4 | `form_04.md` | Request for Extension of Time or Condonation of Delay | ✅ |
| 5 | `form_05.md` | Declaration as to Inventorship | ✅ |
| 6 | `form_06.md` | Claim or Request Regarding Any Change in Applicant for Patent | ✅ |
| 7 | `form_07.md` | Notice of Opposition | ✅ |
| 7A | `form_07a.md` | Representation for Opposition to Grant of Patent | ✅ |
| 8 | `form_08.md` | Request or Claim Regarding Mention of Inventor as Such in a Patent | ✅ |
| 8A | `form_08a.md` | Certificate of Inventorship | ✅ |
| 9 | `form_09.md` | Request for Publication | ✅ |
| 10 | `form_10.md` | Application for Amendment of Patent | ✅ |
| 11 | `form_11.md` | Application for Direction of the Controller | ✅ |
| 12 | `form_12.md` | Request for Grant of Patent Under Section 26(1) & 52(2) | ✅ |
| 13 | `form_13.md` | Application for Amendment of the Application for Patent / Complete Specification / Any Document Related Thereto | ✅ |
| 14 | `form_14.md` | Notice of Opposition to Amendment / Restoration / Surrender / Compulsory Licence / Revision / Correction of Clerical Errors | ✅ |
| 15 | `form_15.md` | Application for the Restoration of Patent | ✅ |
| 16 | `form_16.md` | Application for Registration of Title/Interest in a Patent (or Share/Document Affecting Proprietorship) | ✅ |
| 17 | `form_17.md` | Application for Compulsory Licence | ✅ |
| 18 | `form_18.md` | Request / Express Request for Examination of Application for Patent | ✅ |
| 18A | `form_18a.md` | Request for Expedited Examination of Application for Patent | ✅ |
| 19 | `form_19.md` | Application for Revocation of a Patent for Non Working | ✅ |
| 20 | `form_20.md` | Application for Revision of Terms and Conditions of Licence | ✅ |
| 21 | `form_21.md` | Request for Termination of Compulsory Licence | ✅ |
| 22 | `form_22.md` | Application for Registration of Patent Agent | ✅ |
| 23 | `form_23.md` | Application for the Restoration of the Name in the Register of Patent Agents | ✅ |
| 24 | `form_24.md` | Application for Review / Setting Aside Controller's Decision / Order | ✅ |
| 25 | `form_25.md` | Request for Permission for Making Patent Application Outside India | ✅ |
| 26 | `form_26.md` | Form for Authorisation of a Patent Agent / or Any Person in a Matter or Proceeding | ✅ |
| 27 | `form_27.md` | Statement Regarding the Working of Patented Invention(s) on a Commercial Scale in India | ✅ |
| 28 | `form_28.md` | To Be Submitted by a Small Entity / Startup / Educational Institution | ✅ |
| 29 | `form_29.md` | Request for Withdrawal of the Application for Patent | ✅ |
| 30 | `form_30.md` | To Be Used When No Other Form Is Prescribed | ✅ |
| 31 | `form_31.md` | Grace Period | ✅ |

> Each spec file carries the **exact** official name and legal citation transcribed from its PDF.
> The `List of forms.pdf` in `docs/` is the government cover index and was not itself specced.
