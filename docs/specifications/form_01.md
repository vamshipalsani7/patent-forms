# Form 1

**Official Name:** Application for Grant of Patent

**Purpose:** The primary application by which an applicant requests the grant of a patent
in India. Captures applicant(s), inventor(s), title, agent, address for service, priority/
PCT/divisional/patent-of-addition particulars, statutory declarations, and the list of
attachments (including Form 2 specification, Form 3, Form 5).

**Legal Reference:**
- The Patents Act, 1970 (39 of 1970) — **Sections 7, 54 and 135**
- The Patents Rules, 2003 — **Rule 20, sub-rule (1)**

**Page count:** 4

---

## Overall Layout Notes

- This is the most complex IPO form. It is organised into a **FOR OFFICE USE ONLY** header
  block plus **13 numbered paragraphs** (with sub-parts 3A/3B and declaration groups (i)–(iii)).
- The form uses **tick `( )` boxes** for category selections (this spec treats each as a
  Checkbox unless the options are mutually exclusive, in which case Radio Button).
- Multiple applicant/inventor rows are supported ("Repeat boxes in case of more than one entry").
- Several fields carry the standing OTP/redaction annotation: *"OTP verification mandatory — will
  be redacted"*. These are transcribed on the field and flagged for the UI.

---

## Section 0 — For Office Use Only (Header)

Description: Pre-printed box completed by the Patent Office, **not** by the applicant. Reproduce
on preview but keep read-only / non-editable by the applicant.

| Field | Type | Required? | Repeatable? | Auto-fill | Notes |
|---|---|---|---|---|---|
| Application No. | Text | Unknown (office) | No | No — office allotted | Read-only for applicant |
| Filing date | Date | Unknown (office) | No | No | Read-only |
| Amount of Fee paid | Number (currency) | Unknown (office) | No | No | Read-only |
| CBR No. | Text | Unknown (office) | No | No | Read-only |
| Signature | Signature | Unknown (office) | No | No | Office signature |

---

## Section 1 — Applicant's Reference / Identification No.

**Label:** `1. APPLICANT'S REFERENCE / IDENTIFICATION NO. (AS ALLOTTED BY OFFICE)`

**Field 1.1 — Applicant's reference / identification no.**
- Field Type: Text
- Required?: Optional
- Repeatable?: No
- Auto-fill Opportunity: **Yes** — if an earlier office-allotted reference exists in uploaded docs.
- Validation Notes: Free text; office-allotted identifier.

---

## Section 2 — Type of Application

**Label:** `2. TYPE OF APPLICATION [Please tick (✓) at the appropriate category]`

Description: Selects the nature of the application. Rendered on the form as a grid that also
permits combinations (e.g. a Convention application that is also Divisional or a Patent of
Addition). Each category is documented individually per the "document every checkbox" rule.

| # | Checkbox Label | Type | Required? | Notes |
|---|---|---|---|---|
| 2.1 | Ordinary | Checkbox | Conditional | Base type |
| 2.2 | Convention | Checkbox | Conditional | Base type; enables Section 8 |
| 2.3 | PCT-NP (PCT National Phase) | Checkbox | Conditional | Enables Section 9 |
| 2.4 | PPH (Patent Prosecution Highway) | Checkbox | Conditional | |
| 2.5 | Divisional | Checkbox | Conditional | Enables Section 10; may combine with a base type |
| 2.6 | Patent of Addition | Checkbox | Conditional | Enables Section 11; may combine with a base type |

- **Required?:** At least one base category must be selected (Mandatory as a group).
- **Auto-fill Opportunity:** **Yes (derived)** — infer from uploaded documents (PCT forms →
  PCT-NP; priority/convention docs → Convention; reference to a parent application → Divisional;
  reference to a main patent → Patent of Addition).
- **Validation Notes:** Selecting Convention/PCT-NP/Divisional/Patent of Addition should require
  the corresponding particulars in Sections 8/9/10/11 respectively.

> **Cross-check note:** the printed grid arranges Divisional and Patent of Addition so they can
> be paired with a base type. Preserve the official grid layout on export; confirm exact cell
> arrangement against `docs/Form_1.PDF` page 1.

---

## Section 3A — Applicant(s)

**Label:** `3A. APPLICANT(S)`

Description: One row per applicant. See **Table T1 — Applicants**. The address is a composite
sub-block. Repeatable for multiple applicants.

---

## Section 3B — Category of Applicant

**Label:** `3B. CATEGORY OF APPLICANT [Please tick (✓) at the appropriate category]`

| # | Checkbox Label | Type | Required? | Notes |
|---|---|---|---|---|
| 3B.1 | Natural Person | Checkbox | Conditional | Mutually exclusive with "Other than Natural Person" |
| 3B.2 | Other than Natural Person | Checkbox | Conditional | Umbrella for the following sub-categories |
| 3B.3 | Small Entity | Checkbox | Conditional | Sub-category; affects fees |
| 3B.4 | Startup | Checkbox | Conditional | Sub-category; affects fees |
| 3B.5 | Educational institution | Checkbox | Conditional | Sub-category; affects fees |
| 3B.6 | Others | Checkbox | Conditional | Sub-category |

- **Required?:** Mandatory as a group (a category must be chosen).
- **Auto-fill Opportunity:** **Yes** — from Form 28 (Small Entity/Startup) if uploaded, or the
  applicant type recorded elsewhere.
- **Validation Notes:** Category directly determines the fee schedule. "Natural Person" vs
  "Other than Natural Person" are mutually exclusive; the sub-categories qualify the latter.

---

## Section 4 — Inventor(s)

**Label:** `4. INVENTOR(S) [Please tick (✓) at the appropriate category]`

**Field 4.1 — Are all the inventor(s) same as the applicant(s) named above?**
- Field Type: Radio Button (`Yes` | `No`)
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (derived)** — compare inventor and applicant sets from uploaded docs.
- Validation Notes: If `No`, **Table T2 — Inventors** must be completed.

If **No**, furnish inventor details in **Table T2 — Inventors** (below).

---

## Section 5 — Title of the Invention

**Field 5.1 — Title of the invention**
- Field Type: Multi-line Text
- Required?: Mandatory
- Repeatable?: No
- Auto-fill Opportunity: **Yes (strong)** — title from Form 2 (Specification), Provisional/
  Complete Specification cover, or Patent Certificate.
- Validation Notes: Must match the title on the Specification (Form 2).

---

## Section 6 — Authorised Registered Patent Agent(s)

**Label:** `6. AUTHORISED REGISTERED PATENT AGENT(S)`

| # | Field Label | Type | Required? | Repeatable? | Auto-fill | Notes |
|---|---|---|---|---|---|---|
| 6.1 | IN/PA No. | Text | Conditional | Yes | From Form 26 (Authorisation) | Agent registration no. |
| 6.2 | Name | Text | Conditional | Yes | From Form 26 | Agent name |
| 6.3 | Mobile No. | Number (phone) | Conditional | Yes | From Form 26 | **OTP verification mandatory — will be redacted** |

- **Required?:** Conditional — Mandatory when the application is filed through a patent agent.

---

## Section 7 — Address for Service of Applicant in India

**Label:** `7. ADDRESS FOR SERVICE OF APPLICANT IN INDIA`

| # | Field Label | Type | Required? | Repeatable? | Auto-fill | Notes |
|---|---|---|---|---|---|---|
| 7.1 | Name | Text | Mandatory | No | From agent/applicant | |
| 7.2 | Postal Address | Address / Multi-line Text | Mandatory | No | From agent/applicant | Must be in India |
| 7.3 | Telephone No. | Number (phone) | Optional | No | From docs | |
| 7.4 | Mobile No. | Number (phone) | Mandatory | No | From docs | **OTP verification mandatory — will be redacted** |
| 7.5 | Fax No. | Number | Optional | No | From docs | |
| 7.6 | E-mail ID | Text (email) | Mandatory | No | From docs | **OTP verification mandatory — will be redacted** |

- **Validation Notes:** Address for service must be an address in India (statutory requirement).

---

## Section 8 — Convention Application Particulars

**Label:** `8. IN CASE OF APPLICATION CLAIMING PRIORITY OF APPLICATION FILED IN CONVENTION
COUNTRY, PARTICULARS OF CONVENTION APPLICATION`

See **Table T3 — Convention Application(s)**. Conditional on Section 2 = Convention.

---

## Section 9 — PCT National Phase Particulars

**Label:** `9. IN CASE OF PCT NATIONAL PHASE APPLICATION, PARTICULARS OF INTERNATIONAL
APPLICATION FILED UNDER PATENT CO-OPERATION TREATY (PCT)`

| # | Field Label | Type | Required? | Auto-fill | Notes |
|---|---|---|---|---|---|
| 9.1 | International application number | Text | Conditional | From PCT docs (e.g. PCT/…) | Mandatory if PCT-NP |
| 9.2 | International filing date | Date | Conditional | From PCT docs | Mandatory if PCT-NP |

- **Conditional** on Section 2 = PCT-NP.

---

## Section 10 — Divisional Application Particulars

**Label:** `10. IN CASE OF DIVISIONAL APPLICATION FILED UNDER SECTION 16, PARTICULARS OF
ORIGINAL (FIRST) APPLICATION`

| # | Field Label | Type | Required? | Auto-fill | Notes |
|---|---|---|---|---|---|
| 10.1 | Original (first) application No. | Text | Conditional | From parent application docs | Mandatory if Divisional |
| 10.2 | Date of filing of original (first) application | Date | Conditional | From parent application docs | Mandatory if Divisional |

- **Conditional** on Section 2 = Divisional.

---

## Section 11 — Patent of Addition Particulars

**Label:** `11. IN CASE OF PATENT OF ADDITION FILED UNDER SECTION 54, PARTICULARS OF MAIN
APPLICATION OR PATENT`

| # | Field Label | Type | Required? | Auto-fill | Notes |
|---|---|---|---|---|---|
| 11.1 | Main application/patent No. | Text | Conditional | From main patent docs | Mandatory if Patent of Addition |
| 11.2 | Date of filing of main application | Date | Conditional | From main patent docs | Mandatory if Patent of Addition |

- **Conditional** on Section 2 = Patent of Addition.

---

## Section 12 — Declarations

**Label:** `12. DECLARATIONS`. Three declaration groups (i)–(iii).

### 12(i) — Declaration by the inventor(s)

Boilerplate (with a parenthetical note on assignee signing/assignment upload). Verbatim core:
*"I/We, the above named inventor(s) is/are the true & first inventor(s) for this Invention and
declare that the applicant(s) herein is/are my/our assignee or legal representative."*

| # | Field Label | Type | Required? | Repeatable? | Auto-fill | Notes |
|---|---|---|---|---|---|---|
| 12i.a | Date | Date | Conditional | Yes | Signing date | Per inventor |
| 12i.b | Signature(s) | Signature | Conditional | Yes | No | Per inventor |
| 12i.c | Name(s) | Text | Conditional | Yes | Inventor names (Table T2) | Per inventor |

### 12(ii) — Declaration by the applicant(s) in the convention country

Boilerplate. Verbatim core: *"I/We, the applicant(s) in the convention country declare that the
applicant(s) herein is/are my/our assignee or legal representative."* Conditional on Convention.

| # | Field Label | Type | Required? | Repeatable? | Auto-fill | Notes |
|---|---|---|---|---|---|---|
| 12ii.a | Date | Date | Conditional | Yes | Signing date | |
| 12ii.b | Signature(s) | Signature | Conditional | Yes | No | |
| 12ii.c | Name(s) of the signatory | Text | Conditional | Yes | From convention docs | |

### 12(iii) — Declaration by the applicant(s)

Opening: *"I/We the applicant(s) hereby declare(s) that:-"* followed by a list of statements the
applicant ticks/crosses as applicable. **Each statement is documented as its own checkbox** (per
the "document every checkbox" rule). Type: Checkbox; Required?: Conditional (tick those that apply);
Repeatable?: No.

| # | Checkbox statement (verbatim, abbreviated) |
|---|---|
| 12iii.1 | I am/We are in possession of the above-mentioned invention. |
| 12iii.2 | The provisional/complete specification relating to the invention is filed with this application. |
| 12iii.3 | The invention as disclosed in the specification uses the biological material from India and the necessary permission from the competent authority shall be submitted by me/us before the grant of patent to me/us. |
| 12iii.4 | There is no lawful ground of objection(s) to the grant of the Patent to me/us. |
| 12iii.5 | I am/we are the true & first inventor(s). |
| 12iii.6 | I am/we are the assignee or legal representative of true & first inventor(s). |
| 12iii.7 | The application or each of the applications, particulars of which are given in Paragraph-8, was the first application in convention country/countries in respect of my/our invention(s). |
| 12iii.8 | I/We claim the priority from the above mentioned application(s) filed in convention country/countries and state that no application for protection in respect of the invention had been made in a convention country before that date by me/us or by any person from which I/We derive the title. |
| 12iii.9 | My/our application in India is based on international application under Patent Cooperation Treaty (PCT) as mentioned in Paragraph-9. |
| 12iii.10 | The application is divided out of my/our application particulars of which is given in Paragraph-10 and pray that this application may be treated as deemed to have been filed on DD/MM/YYYY under section 16 of the Act. |
| 12iii.11 | The said invention is an improvement in or modification of the invention particulars of which are given in Paragraph-11. |

- **Field 12iii.10a — "deemed to have been filed on DD/MM/YYYY"**: embedded Date field, Conditional
  (Mandatory when 12iii.10 is ticked). Auto-fill: parent application filing date.
- **Auto-fill (group):** **Yes (derived)** — tick statements consistent with Section 2 selections
  (e.g. tick 12iii.9 only for PCT-NP). User confirms each.
- **Validation Notes:** Several statements contain strike-out choices (`I am/We are`, `provisional/
  complete`); resolve per applicant count and specification type.

---

## Section 13 — Attachments with the Application

**Label:** `13. FOLLOWING ARE THE ATTACHMENTS WITH THE APPLICATION`

### 13(a) Form 2 — Specification particulars → see **Table T4 — Form 2 Attachment**.

### 13(b)–(j) Attachment checklist

Each item is a checkbox indicating the attachment is enclosed. Documented individually.

| # | Checkbox Label (verbatim) | Type | Required? |
|---|---|---|---|
| 13.b | Complete specification (in conformation with the international application)/as amended before the IPEA, as applicable (2 copies) | Checkbox | Conditional |
| 13.c | Sequence listing in electronic form | Checkbox | Conditional |
| 13.d | Drawings (in conformation with the international application)/as amended before the IPEA, as applicable (2 copies) | Checkbox | Conditional |
| 13.e | Priority document(s) or a request to retrieve the priority document(s) from DAS (Digital Access Service)… | Checkbox | Conditional |
| 13.f | Translation of priority document/Specification/International Search Report/International Preliminary Report on Patentability | Checkbox | Conditional |
| 13.g | Statement and Undertaking on Form 3 | Checkbox | Conditional |
| 13.h | Declaration of Inventorship on Form 5 | Checkbox | Conditional |
| 13.i | Power of Authority | Checkbox | Conditional |
| 13.j | ……… (other — free text) | Text | Optional |

- **Auto-fill Opportunity:** **Yes** — tick items whose corresponding documents were uploaded to
  the app (e.g. Form 3, Form 5, priority docs).

### Fee line

**Field 13.fee — Total fee**
- `Total fee ₹……… in Cash/Banker's Cheque/Bank Draft bearing No. …… Date …… on …… Bank.`
- Sub-fields: Amount (Number/currency), Payment mode (Radio: Cash | Banker's Cheque | Bank Draft),
  Instrument No. (Text), Instrument Date (Date), Bank name (Text).
- Required?: Mandatory. Auto-fill: amount derivable from applicant category + claims/pages counts.

### Final declaration & signature

Boilerplate: *"I/We hereby declare that to the best of my/our knowledge, information and belief the
fact and matters stated herein are correct and I/We request that a patent may be granted to me/us
for the said invention."* — see **Signature Block**.

---

## Tables

### Table T1 — Applicants (Section 3A)

| Column | Field Type | Required? | Auto-fill |
|---|---|---|---|
| Name in Full | Text | Mandatory | Form 2 / Specification / Certificate |
| Gender (optional, for individuals) | Radio (Male / Female / Others / Prefer not to disclose) | Optional | From docs |
| Nationality | Text / Dropdown (country) | Mandatory | From docs |
| Country of Residence | Text / Dropdown (country) | Mandatory | From docs |
| Age (optional, for natural persons) | Number (years) / "Prefer not to disclose" | Optional | From docs |
| Address of the Applicant | Address sub-block (below) | Mandatory | From docs |

**Address sub-block (per applicant):** House No., Street, City, State, Country, Pin code,
**Email** (*OTP verification mandatory — will be redacted*), **Contact number** (*OTP verification
mandatory — will be redacted*).

- **Row behaviour:** one row per applicant. **Multiple rows allowed: Yes.**

### Table T2 — Inventors (Section 4, when "No")

| Column | Field Type | Required? | Auto-fill |
|---|---|---|---|
| Name in Full | Text | Conditional (Mandatory if 4.1 = No) | From Form 5 / Specification |
| Gender (optional, for natural persons) | Radio (Male / Female / Others / Prefer not to disclose) | Optional | From docs |
| Nationality | Text / Dropdown | Conditional | From docs |
| Age (optional, for natural persons) | Number (years) / "Prefer not to disclose" | Optional | From docs |
| Country of Residence | Text / Dropdown | Conditional | From docs |
| Address of the Inventor | Address sub-block: House No., Street, City, State, Country, Pin code | Conditional | From docs |

- **Row behaviour:** one row per inventor. **Multiple rows allowed: Yes.**

### Table T3 — Convention Application(s) (Section 8)

| Column | Field Type | Required? | Auto-fill |
|---|---|---|---|
| Country | Text / Dropdown | Conditional | Priority/convention docs |
| Application Number | Text | Conditional | Priority docs |
| Filing date | Date | Conditional | Priority docs |
| Name of the applicant | Text | Conditional | Priority docs |
| Title of the invention | Text | Conditional | Priority docs |
| IPC (as classified in the convention country) | Text | Conditional | Priority docs |

- **Row behaviour:** one row per convention application. **Multiple rows allowed: Yes.**

### Table T4 — Form 2 Attachment particulars (Section 13a)

| Item | Details field | Fee | Remarks |
|---|---|---|---|
| Complete/provisional specification # | No. of pages (Number) | Number | Text |
| No. of Claim(s) | No. of claims and No. of pages (Number, Number) | Number | Text |
| Abstract | No. of pages (Number) | Number | Text |
| No. of Drawing(s) | No. of drawings and No. of pages (Number, Number) | Number | Text |

- **Footnote `#`:** "In case of a complete specification, if the applicant desires to adopt the
  drawings filed with his provisional specification as the drawings or part of the drawings for the
  complete specification under rule 13(4), the number of such pages filed with the provisional
  specification are required to be mentioned here."
- **Auto-fill:** page/claim/drawing counts derivable from the uploaded Form 2 / Specification.

---

## Signature Block

Form 1 has **multiple** signature points; document each separately:

- **12(i) inventor declaration** — Date, Signature(s), Name(s). One set per inventor.
- **12(ii) convention-country applicant declaration** — Date, Signature(s), Name(s) of signatory.
- **Final applicant declaration (end of Section 13):**
  - **Dated this __ day of __ 20__** — Date. Mandatory.
  - **Signature** — Signature. Mandatory. Signed by applicant(s) or authorised registered patent agent.
  - **Name** — Text. Mandatory.
- **Addressee:** `To, The Controller of Patents, The Patent Office, at ……` — Field: Patent Office
  location (Dropdown: Delhi / Mumbai / Chennai / Kolkata). Mandatory.
- **Place** — not printed as a separate field beyond the addressee "at …"; do not invent one.

---

## Special Notes

Transcribed **Note** block (form footer, page 4):
- "Repeat boxes in case of more than one entry." → all applicant/inventor/convention rows are repeatable.
- "To be signed by the applicant(s) or by authorized registered patent agent otherwise where mentioned."
- "Tick (✓)/cross (x) whichever is applicable/not applicable in declaration in paragraph-12." →
  the 12(iii) declaration statements use tick/cross semantics.
- "Name of the inventor and applicant should be given in full, family name in the beginning."
- "Strike out the portion which is/are not applicable." → governs strike-out choices (I/We, is/are,
  provisional/complete, my/our, etc.).
- "For fee: See First Schedule." → fee amounts come from the First Schedule, keyed to applicant category.

Additional UI-relevant notes:
- **Privacy/redaction:** all fields marked *"OTP verification mandatory — will be redacted"*
  (applicant email & contact number, inventor/agent mobile, address-for-service mobile & email)
  require OTP verification and are redacted in the published record. The UI must flag these and
  must **not** treat them as ordinary text.
- **Conditional sections:** Sections 8/9/10/11 and declarations 12(ii)/12(iii).7–11 are gated by the
  Section 2 "Type of Application" selection; the editor should show/hide them accordingly (but must
  never delete user-entered data silently).
- **Attachments required (typical):** Form 2 (Specification), and as applicable Form 3, Form 5,
  Power of Authority (Form 26), priority documents, PCT documents, drawings, sequence listing.
- **Biological material (12iii.3):** if the invention uses biological material from India, competent-
  authority permission is undertaken before grant — surface as a warning/reminder.
- **Fee dependency:** total fee depends on applicant category (3B), number of claims, and number of
  pages — compute per the First Schedule; keep editable.
