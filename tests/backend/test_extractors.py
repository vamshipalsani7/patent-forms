"""The seven document-intelligence extractors, against realistic document text.

Each sample below is written to match the printed layout of the real document —
the IPO's machine-generated certificate template, the Form 2 cover page's
"(a) NAME / (b) NATIONALITY / (c) ADDRESS" blocks, the two-party recital of a
deed. Regexes tested only against text shaped to suit them prove nothing.

Every extractor gets the same three-part treatment:
  1. it finds what the demand analysis says the document must yield;
  2. it declines to invent anything from an unrelated document;
  3. its known confusion — the plausible wrong answer sitting a few lines away
     from the right one — does not happen.

Part 3 is the one that matters. Both bugs found while building these extractors
were of that kind, and neither was visible from the value alone.
"""

from __future__ import annotations

import unittest

import context  # noqa: F401  — sets sys.path

from extractors.assignment_document import AssignmentDocumentExtractor
from extractors.form1 import Form1Extractor
from extractors.form2_specification import Form2SpecificationExtractor
from extractors.form5 import Form5Extractor
from extractors.form26_authorisation import Form26AuthorisationExtractor
from extractors.patent_certificate import PatentCertificateExtractor
from extractors.pct_document import PctDocumentExtractor
from extractors.priority_document import PriorityDocumentExtractor

UNRELATED = "INVOICE\nAcme Stationery Supplies\nTotal Due: 4,500.00\nDate: 01/01/2020"


def run(extractor, text):
    """Extract from synthetic page text. No AcroForm, so this is the anchor path."""
    return extractor.extract_from_file("/nonexistent.pdf", "doc_test", [(1, text)])


def by_key(facts):
    """{key: value} keeping only the first fact per key."""
    result = {}
    for fact in facts:
        result.setdefault(fact.key, fact.value)
    return result


def values_for(facts, key):
    return [f.value for f in facts if f.key == key]


# --- document samples --------------------------------------------------------

CERTIFICATE = """GOVERNMENT OF INDIA
THE PATENT OFFICE
PATENT CERTIFICATE
(Rule 74 Of The Patents Rules)
Patent No. 384756
Application No. 201811012345
Date of Filing : 30/03/2018
Patentee : ACME INNOVATIONS PRIVATE LIMITED

It is hereby certified that a patent has been granted to the patentee for an invention
entitled "A NOVEL METHOD FOR EFFICIENT SOLAR PANEL COOLING" as disclosed in the above
mentioned application for the term of twenty years from the 30th day of March 2018 in
accordance with the provisions of the Patents Act, 1970.

Date of Grant : 15/07/2021
"""

FORM26 = """FORM 26
THE PATENTS ACT, 1970
(39 of 1970)
&
THE PATENTS RULES, 2003
FORM FOR AUTHORISATION OF A PATENT AGENT
(See section 127 and 132 and rule 135)

I/We, Acme Innovations Private Limited, of 12 MG Road, Bengaluru 560001, do hereby
authorise Shri RAJESH KUMAR, IN/PA-1234, of Kumar & Associates, to act on my/our behalf.
"""

SPECIFICATION = """FORM 2
THE PATENTS ACT, 1970 (39 of 1970)
&
THE PATENTS RULES, 2003
COMPLETE SPECIFICATION
(See section 10; rule 13)

1. TITLE OF THE INVENTION
A NOVEL METHOD FOR EFFICIENT SOLAR PANEL COOLING

2. APPLICANT(S)
(a) NAME: ACME INNOVATIONS PRIVATE LIMITED
(b) NATIONALITY: Indian
(c) ADDRESS: 12 MG Road, Bengaluru 560001, Karnataka, India

3. INVENTOR(S)
(a) NAME: RAJESH KUMAR
(b) NATIONALITY: Indian
(c) ADDRESS: 44 Residency Road, Bengaluru 560025, India
(a) NAME: PRIYA SHARMA
(b) NATIONALITY: Indian

4. PREAMBLE TO THE DESCRIPTION
The following specification particularly describes the invention.
"""

DEED = """DEED OF ASSIGNMENT

THIS DEED OF ASSIGNMENT is made on this 12th day of March, 2020

BETWEEN
Acme Innovations Private Limited, a company incorporated under the laws of India,
having its registered office at 12 MG Road, Bengaluru 560001, Karnataka, India
(hereinafter referred to as the "ASSIGNOR") of the ONE PART

AND
Globex Corporation, a company incorporated under the laws of the United States of America,
having its principal place of business at 500 Market Street, San Francisco, CA 94105, USA
(hereinafter referred to as the "ASSIGNEE") of the OTHER PART
"""

PRIORITY = """CERTIFIED COPY OF PRIORITY DOCUMENT

UNITED STATES PATENT AND TRADEMARK OFFICE

Application Number: 16/123,456
Filing Date: March 12, 2018
Applicant(s): Acme Innovations Inc.
Title of Invention: A Novel Method for Efficient Solar Panel Cooling
"""

FORM5 = """FORM 5
THE PATENTS ACT, 1970
DECLARATION AS TO INVENTORSHIP
(See section 10(6) and rule 13(6))

I/We Acme Innovations Private Limited, the applicant(s) hereby declare that the true and
first inventor(s) of the invention disclosed in the complete specification filed in
pursuance of my/our application numbered 202211012345 dated 30/03/2018 is/are

2. INVENTOR(S)
(a) NAME: RAJESH KUMAR
(b) NATIONALITY: Indian
(a) NAME: PRIYA SHARMA
(b) NATIONALITY: Indian
"""

PCT = """PATENT COOPERATION TREATY
PCT
INTERNATIONAL APPLICATION PUBLISHED UNDER THE PCT

International Application No.: PCT/IN2019/050123
International Filing Date: 12 March 2019 (12.03.2019)
Applicant: ACME INNOVATIONS PRIVATE LIMITED
"""


# --- 1. Patent Certificate (63 citations) ------------------------------------

class TestPatentCertificate(unittest.TestCase):
    def setUp(self):
        self.facts = run(PatentCertificateExtractor(), CERTIFICATE)
        self.values = by_key(self.facts)

    def test_extracts_patent_number(self):
        self.assertEqual("384756", self.values["patent.number"])

    def test_extracts_patentee_name(self):
        self.assertEqual("ACME INNOVATIONS PRIVATE LIMITED", self.values["patentee.name"])

    def test_extracts_grant_date_as_iso(self):
        self.assertEqual("2021-07-15", self.values["patent.grantDate"])

    def test_extracts_invention_title_without_its_quotes(self):
        self.assertEqual(
            "A NOVEL METHOD FOR EFFICIENT SOLAR PANEL COOLING",
            self.values["invention.title"],
        )

    def test_does_not_read_the_filing_date_as_the_grant_date(self):
        """Both dates are printed, four lines apart, in the same format."""
        self.assertNotEqual("2018-03-30", self.values["patent.grantDate"])

    def test_prose_reference_to_the_patentee_is_not_captured_as_a_name(self):
        """"granted to the patentee for an invention entitled …" must not
        yield a patentee named "for an invention entitled"."""
        self.assertNotIn("invention", self.values["patentee.name"].lower())

    def test_applicant_name_is_aliased_from_the_patentee_at_lower_confidence(self):
        applicant = next(f for f in self.facts if f.key == "applicant.name")
        patentee = next(f for f in self.facts if f.key == "patentee.name")
        self.assertEqual(patentee.value, applicant.value)
        self.assertLess(
            applicant.confidence, patentee.confidence,
            "an inferred value must rank below the value it was inferred from",
        )

    def test_invents_nothing_from_an_unrelated_document(self):
        self.assertEqual([], run(PatentCertificateExtractor(), UNRELATED))


# --- 2. Form 26 / Power of Attorney (32 citations) ---------------------------

class TestForm26Authorisation(unittest.TestCase):
    def setUp(self):
        self.values = by_key(run(Form26AuthorisationExtractor(), FORM26))

    def test_extracts_agent_name_from_the_authorisation_sentence(self):
        self.assertEqual("RAJESH KUMAR", self.values["agent.name"])

    def test_strips_the_honorific(self):
        self.assertNotIn("Shri", self.values["agent.name"])

    def test_extracts_inpa_number(self):
        self.assertEqual("1234", self.values["agent.inpaNumber"])

    def test_does_not_return_the_authorising_applicant_as_the_agent(self):
        """The applicant is named first in the same sentence as the agent."""
        self.assertNotIn("Acme", self.values["agent.name"])

    def test_reads_the_american_spelling_too(self):
        values = by_key(run(
            Form26AuthorisationExtractor(),
            "I/We, Acme Inc, do hereby authorize Dr. PRIYA SHARMA, IN/PA 5678, to act.",
        ))
        self.assertEqual("PRIYA SHARMA", values["agent.name"])
        self.assertEqual("5678", values["agent.inpaNumber"])

    def test_invents_nothing_from_an_unrelated_document(self):
        self.assertEqual([], run(Form26AuthorisationExtractor(), UNRELATED))


# --- 3. Complete / Provisional Specification (20 citations) ------------------

class TestForm2Specification(unittest.TestCase):
    def setUp(self):
        self.facts = run(Form2SpecificationExtractor(), SPECIFICATION)
        self.values = by_key(self.facts)

    def test_extracts_invention_title(self):
        self.assertEqual(
            "A NOVEL METHOD FOR EFFICIENT SOLAR PANEL COOLING",
            self.values["invention.title"],
        )

    def test_extracts_applicant_particulars(self):
        self.assertEqual("ACME INNOVATIONS PRIVATE LIMITED", self.values["applicant.name"])
        self.assertEqual("Indian", self.values["applicant.nationality"])
        self.assertEqual(
            "12 MG Road, Bengaluru 560001, Karnataka, India",
            self.values["applicant.address"],
        )

    def test_keeps_every_inventor_not_just_the_first(self):
        self.assertEqual(
            ["RAJESH KUMAR", "PRIYA SHARMA"],
            values_for(self.facts, "inventor.name"),
        )

    def test_inventor_address_comes_from_the_inventor_block(self):
        """The applicant block prints an identically-labelled (c) ADDRESS."""
        self.assertEqual(
            "44 Residency Road, Bengaluru 560025, India",
            self.values["inventor.address"],
        )

    def test_applicant_name_is_not_taken_from_the_inventor_block(self):
        self.assertNotEqual(self.values["applicant.name"], self.values["inventor.name"])

    def test_a_provisional_specification_is_read_the_same_way(self):
        provisional = SPECIFICATION.replace("COMPLETE SPECIFICATION", "PROVISIONAL SPECIFICATION")
        self.assertEqual(self.values, by_key(run(Form2SpecificationExtractor(), provisional)))

    def test_invents_nothing_from_an_unrelated_document(self):
        self.assertEqual([], run(Form2SpecificationExtractor(), UNRELATED))


# --- 4. Assignment Deed (10 citations) ---------------------------------------

class TestAssignmentDocument(unittest.TestCase):
    """The assignor/assignee confusion is the highest-consequence error here:
    a wrong party on a filed Form 16 transfers the patent to the wrong entity,
    and the value looks entirely correct in review."""

    def setUp(self):
        self.values = by_key(run(AssignmentDocumentExtractor(), DEED))

    def test_extracts_assignee_name(self):
        self.assertEqual("Globex Corporation", self.values["assignee.name"])

    def test_extracts_assignee_address(self):
        self.assertEqual(
            "500 Market Street, San Francisco, CA 94105, USA",
            self.values["assignee.address"],
        )

    def test_extracts_assignee_nationality(self):
        self.assertEqual("United States of America", self.values["assignee.nationality"])

    def test_no_assignor_value_leaks_into_any_assignee_field(self):
        for key, value in self.values.items():
            with self.subTest(key=key):
                self.assertNotIn("Acme", value)
                self.assertNotIn("MG Road", value)
                self.assertNotIn("India,", value + ",")

    def test_assignee_name_is_not_scraped_off_the_address_line(self):
        """Regression: the adjacent-marker pattern captured the tail of the
        preceding line and returned "USA" as the assignee's name."""
        self.assertNotEqual("USA", self.values["assignee.name"])

    def test_reads_a_structured_party_schedule(self):
        values = by_key(run(AssignmentDocumentExtractor(), """DEED OF ASSIGNMENT
ASSIGNOR NAME: Acme Innovations Private Limited
ASSIGNEE NAME: Globex Corporation
ASSIGNEE Address: 500 Market Street, San Francisco
"""))
        self.assertEqual("Globex Corporation", values["assignee.name"])

    def test_yields_nothing_rather_than_guessing_on_an_unrecognised_deed(self):
        """A deed naming no assignee must produce no assignee — silence is the
        correct answer when the shape is not understood."""
        facts = run(AssignmentDocumentExtractor(), """DEED OF ASSIGNMENT
BETWEEN Acme Innovations Private Limited, a company incorporated under the laws
of India, having its registered office at 12 MG Road, Bengaluru, of the ONE PART
""")
        self.assertEqual([], facts)

    def test_invents_nothing_from_an_unrelated_document(self):
        self.assertEqual([], run(AssignmentDocumentExtractor(), UNRELATED))


# --- 5. Priority Document (9 citations) --------------------------------------

class TestPriorityDocument(unittest.TestCase):
    def setUp(self):
        self.values = by_key(run(PriorityDocumentExtractor(), PRIORITY))

    def test_extracts_foreign_application_number(self):
        self.assertEqual("16/123,456", self.values["foreignApplications[].number"])

    def test_extracts_foreign_filing_date_from_an_american_format(self):
        self.assertEqual("2018-03-12", self.values["foreignApplications[].filingDate"])

    def test_reads_the_country_off_the_issuing_office(self):
        self.assertEqual("UNITED STATES", self.values["foreignApplications[].country"])

    def test_an_explicit_country_label_wins_over_the_office_name(self):
        values = by_key(run(
            PriorityDocumentExtractor(),
            "JAPAN PATENT OFFICE\nCountry: Japan\nApplication Number: 2018-123456",
        ))
        self.assertEqual("Japan", values["foreignApplications[].country"])

    def test_extracts_applicant_and_title(self):
        self.assertEqual("Acme Innovations Inc.", self.values["applicant.name"])
        self.assertEqual(
            "A Novel Method for Efficient Solar Panel Cooling",
            self.values["invention.title"],
        )

    def test_invents_nothing_from_an_unrelated_document(self):
        self.assertEqual([], run(PriorityDocumentExtractor(), UNRELATED))


# --- 6. Form 5 (7 citations) -------------------------------------------------

class TestForm5(unittest.TestCase):
    def setUp(self):
        self.facts = run(Form5Extractor(), FORM5)
        self.values = by_key(self.facts)

    def test_keeps_every_declared_inventor(self):
        self.assertEqual(["RAJESH KUMAR", "PRIYA SHARMA"], values_for(self.facts, "inventor.name"))

    def test_extracts_inventor_nationality(self):
        self.assertEqual("Indian", self.values["inventor.nationality"])

    def test_does_not_return_the_declaring_applicant_as_an_inventor(self):
        """The form opens "I/We <applicant> … hereby declare"; a whole-document
        name pattern reads that applicant as the first inventor."""
        for name in values_for(self.facts, "inventor.name"):
            self.assertNotIn("Acme", name)

    def test_invents_nothing_from_an_unrelated_document(self):
        self.assertEqual([], run(Form5Extractor(), UNRELATED))


# --- 7. PCT (6 citations) ----------------------------------------------------

class TestPctDocument(unittest.TestCase):
    def setUp(self):
        self.values = by_key(run(PctDocumentExtractor(), PCT))

    def test_extracts_international_application_number(self):
        self.assertEqual("PCT/IN2019/050123", self.values["application.number"])

    def test_extracts_international_filing_date_as_iso(self):
        self.assertEqual("2019-03-12", self.values["application.filingDate"])

    def test_reads_the_spelled_out_date_not_the_parenthesised_restatement(self):
        """"12 March 2019 (12.03.2019)" — the spelled-out month is unambiguous,
        so the parenthesised numeric form is deliberately excluded."""
        self.assertEqual("2019-03-12", self.values["application.filingDate"])

    def test_invents_nothing_from_an_unrelated_document(self):
        self.assertEqual([], run(PctDocumentExtractor(), UNRELATED))


# --- cross-cutting invariants ------------------------------------------------

ALL_EXTRACTORS = [
    PatentCertificateExtractor(), Form26AuthorisationExtractor(),
    Form2SpecificationExtractor(), AssignmentDocumentExtractor(),
    PriorityDocumentExtractor(), Form5Extractor(), PctDocumentExtractor(),
    Form1Extractor(),
]

SAMPLES = [CERTIFICATE, FORM26, SPECIFICATION, DEED, PRIORITY, FORM5, PCT]


class TestExtractorInvariants(unittest.TestCase):
    """Properties that must hold for every extractor, whatever it is reading."""

    def test_every_fact_only_uses_registered_vocabulary(self):
        from vocabulary.lint import load_registry

        registry = load_registry()
        for extractor in ALL_EXTRACTORS:
            for sample in SAMPLES:
                for fact in run(extractor, sample):
                    with self.subTest(extractor=extractor.SOURCE_TYPE, key=fact.key):
                        self.assertIn(fact.key, registry["keys"])
                        self.assertIn(fact.source_type, registry["sourceTypes"])

    def test_every_fact_carries_full_provenance(self):
        for extractor in ALL_EXTRACTORS:
            for fact in run(extractor, SAMPLES[0]) + run(extractor, SAMPLES[2]):
                with self.subTest(extractor=extractor.SOURCE_TYPE, key=fact.key):
                    self.assertEqual("doc_test", fact.document_id)
                    self.assertEqual(extractor.SOURCE_TYPE, fact.source_type)
                    self.assertIsNotNone(fact.page)
                    self.assertIn(fact.method, {"anchor", "acroform", "ocr", "manual"})
                    self.assertGreater(fact.confidence, 0.0)
                    self.assertLessEqual(fact.confidence, 1.0)
                    self.assertEqual(extractor.EXTRACTOR_VERSION, fact.extractor_version)
                    self.assertTrue(fact.extracted_at)

    def test_date_keys_are_always_iso_formatted(self):
        import re

        from extractors.base import DATE_KEYS

        for extractor in ALL_EXTRACTORS:
            for sample in SAMPLES:
                for fact in run(extractor, sample):
                    if fact.key in DATE_KEYS:
                        with self.subTest(extractor=extractor.SOURCE_TYPE, key=fact.key):
                            self.assertRegex(str(fact.value), r"^\d{4}-\d{2}-\d{2}$")

    def test_no_extractor_emits_an_empty_or_punctuation_only_value(self):
        for extractor in ALL_EXTRACTORS:
            for sample in SAMPLES:
                for fact in run(extractor, sample):
                    with self.subTest(extractor=extractor.SOURCE_TYPE, key=fact.key):
                        self.assertTrue(str(fact.value).strip())
                        self.assertRegex(str(fact.value), r"[A-Za-z0-9]")

    def test_only_multi_value_keys_ever_repeat(self):
        """Any other repeated key means two patterns fired for one field."""
        for extractor in ALL_EXTRACTORS:
            for sample in SAMPLES:
                seen = set()
                for fact in run(extractor, sample):
                    if fact.key in extractor.MULTI_VALUE_KEYS:
                        continue
                    with self.subTest(extractor=extractor.SOURCE_TYPE, key=fact.key):
                        self.assertNotIn(fact.key, seen, "duplicate fact for a single-value key")
                    seen.add(fact.key)

    def test_page_numbers_are_attributed_across_a_multi_page_document(self):
        pages = [(1, "PATENT CERTIFICATE\nPatent No. 384756"),
                 (2, "Patentee : ACME INNOVATIONS PRIVATE LIMITED")]
        facts = PatentCertificateExtractor().extract_from_file("/x.pdf", "doc_test", pages)
        by_page = {f.key: f.page for f in facts}
        self.assertEqual(1, by_page["patent.number"])
        self.assertEqual(2, by_page["patentee.name"])


if __name__ == "__main__":
    unittest.main()
