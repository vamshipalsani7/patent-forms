"""Filing package generation — the documents a professional actually files.

These tests treat the outputs as filing documents, not as bytes: the PDF must
carry the official header and the entered values, must NOT carry anything
internal, must leave office-use and unsigned areas blank, and the package must
arrive under professional filenames.
"""

from __future__ import annotations

import io
import json
import unittest
import zipfile

import context  # noqa: F401  — sets sys.path

import pdfplumber
from docx import Document

from packaging.layout import ValueBook, is_office_section, printed_header
from packaging.naming import filenames, form_slug
from packaging.package import build_package, field_labels, provenance_entries
from packaging.pdf_builder import build_form_pdf
from packaging.docx_builder import build_form_docx
from packaging.reports import build_filing_summary_pdf, build_provenance_pdf

DEFINITIONS = context.DEFINITIONS_DIR


def load(form_id: str) -> dict:
    return json.loads((DEFINITIONS / f"{form_id}.definition.json").read_text(encoding="utf-8"))


def pdf_text(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as doc:
        return "\n".join((page.extract_text() or "") for page in doc.pages)


def pdf_pages(data: bytes) -> int:
    with pdfplumber.open(io.BytesIO(data)) as doc:
        return len(doc.pages)


def docx_text(data: bytes) -> str:
    document = Document(io.BytesIO(data))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)


# The five forms the milestone requires be verified.
VERIFIED_FORMS = ["form_01", "form_18", "form_18a", "form_16", "form_27"]

VALUES = {
    "requester.name": "ACME INNOVATIONS PRIVATE LIMITED",
    "requester.address": "12 MG Road, Bengaluru 560001, Karnataka, India",
    "applicant_request.invention_title": "A Novel Method for Efficient Solar Panel Cooling",
    "applicants.applicant.0.name": "ACME INNOVATIONS PRIVATE LIMITED",
    "title_of_invention.invention_title": "A Novel Method for Efficient Solar Panel Cooling",
    "office_use.rq_no": "OFFICE-ONLY-VALUE",
    "office_use.application_no": "OFFICE-ONLY-VALUE",
}


class TestFilenames(unittest.TestCase):
    def test_names_are_professional_and_space_free(self):
        for form_id in VERIFIED_FORMS:
            with self.subTest(form=form_id):
                names = filenames(load(form_id))
                for part, name in names.items():
                    self.assertNotIn(" ", name, f"{part} filename has a space")
                    self.assertFalse(name.lower().startswith("output"))
                    self.assertTrue(name.startswith("Form"))

    def test_the_form_number_appears_in_every_name(self):
        names = filenames(load("form_18a"))
        for name in names.values():
            self.assertIn("Form18A", name)

    def test_related_forms_do_not_collide(self):
        self.assertNotEqual(form_slug(load("form_18")), form_slug(load("form_18a")))

    def test_names_stay_readable(self):
        # A filename nobody can scan is as bad as a generic one.
        self.assertLessEqual(len(filenames(load("form_18"))["pdf"]), 60)


class TestOfficialPdf(unittest.TestCase):
    def test_every_verified_form_produces_a_valid_pdf(self):
        for form_id in VERIFIED_FORMS:
            with self.subTest(form=form_id):
                data = build_form_pdf(load(form_id), VALUES)
                self.assertTrue(data.startswith(b"%PDF"))
                self.assertGreater(pdf_pages(data), 0)

    def test_it_carries_the_official_printed_header(self):
        definition = load("form_18")
        header = printed_header(definition)
        text = pdf_text(build_form_pdf(definition, VALUES))
        self.assertIn(header["formTitle"], text)
        self.assertIn("REQUEST", text.upper())

    def test_entered_values_appear(self):
        text = pdf_text(build_form_pdf(load("form_18"), VALUES))
        self.assertIn("ACME INNOVATIONS", text)

    def test_office_use_values_never_appear(self):
        """The Patent Office completes those boxes; a filed form leaves them blank."""
        for form_id in ("form_01", "form_18", "form_18a"):
            with self.subTest(form=form_id):
                text = pdf_text(build_form_pdf(load(form_id), VALUES))
                self.assertNotIn("OFFICE-ONLY-VALUE", text)

    def test_no_internal_or_review_language_reaches_the_filed_document(self):
        text = pdf_text(build_form_pdf(load("form_18"), VALUES)).lower()
        for leak in ("confidence", "sourcetype", "form2_specification", "provenance",
                     "filled automatically", "edited by you", "autofill", "mapper"):
            self.assertNotIn(leak, text, f"filed PDF leaked '{leak}'")

    def test_a_long_form_stays_multi_page(self):
        self.assertGreater(pdf_pages(build_form_pdf(load("form_01"), VALUES)), 1)

    def test_hidden_fields_are_omitted_when_visibility_is_supplied(self):
        definition = load("form_18")
        visible = ["requester.name"]
        text = pdf_text(build_form_pdf(definition, VALUES, visible_paths=visible))
        self.assertIn("ACME INNOVATIONS", text)
        self.assertNotIn("A Novel Method for Efficient Solar", text)

    def test_repeatable_groups_expand_to_their_instance_count(self):
        values = dict(VALUES)
        values["applicants.applicant#count"] = 2
        values["applicants.applicant.0.name"] = "FIRST APPLICANT LIMITED"
        values["applicants.applicant.1.name"] = "SECOND APPLICANT LIMITED"
        text = pdf_text(build_form_pdf(load("form_01"), values))
        self.assertIn("FIRST APPLICANT", text)
        self.assertIn("SECOND APPLICANT", text)

    def test_tables_render_with_their_columns(self):
        definition = load("form_27")
        values = {}
        for section in definition["sections"]:
            for field in section.get("fields", []):
                if field.get("kind") == "table" and field.get("columns"):
                    path = f"{section['id']}.{field['id']}"
                    first = field["columns"][0]["id"]
                    values[path] = [{first: "TABLE-CELL-VALUE"}]
        text = pdf_text(build_form_pdf(definition, values))
        if values:  # only assert when the form actually has a table
            self.assertIn("TABLE-CELL-VALUE", text)

    def test_an_unsigned_signature_area_stays_blank(self):
        text = pdf_text(build_form_pdf(load("form_18"), VALUES))
        self.assertNotIn("data:image", text)


class TestEditableDocx(unittest.TestCase):
    def test_every_verified_form_produces_a_readable_docx(self):
        for form_id in VERIFIED_FORMS:
            with self.subTest(form=form_id):
                data = build_form_docx(load(form_id), VALUES)
                self.assertTrue(data.startswith(b"PK"))
                self.assertTrue(docx_text(data).strip())

    def test_it_holds_the_same_values_as_the_pdf(self):
        definition = load("form_18")
        self.assertIn("ACME INNOVATIONS", docx_text(build_form_docx(definition, VALUES)))

    def test_it_preserves_official_section_headings(self):
        definition = load("form_18")
        text = docx_text(build_form_docx(definition, VALUES))
        titles = [s.get("title") for s in definition["sections"] if s.get("title")]
        self.assertIn(titles[1], text)

    def test_office_use_values_never_appear(self):
        self.assertNotIn("OFFICE-ONLY-VALUE", docx_text(build_form_docx(load("form_18"), VALUES)))


class TestFilingSummary(unittest.TestCase):
    def test_it_reports_the_form_documents_and_counts(self):
        data = build_filing_summary_pdf(
            load("form_18"),
            counts={"autoFilled": 41, "edited": 2, "missing": 0},
            documents=["Complete Specification", "Patent Certificate"],
        )
        text = pdf_text(data)
        self.assertIn("Patent Filing Summary", text)
        self.assertIn("Form 18", text)
        self.assertIn("Complete Specification", text)
        self.assertIn("41", text)
        self.assertIn("Ready for Filing", text)

    def test_an_incomplete_form_does_not_claim_to_be_ready(self):
        text = pdf_text(build_filing_summary_pdf(
            load("form_18"), counts={"autoFilled": 3, "edited": 0, "missing": 2}))
        self.assertNotIn("Ready for Filing", text)
        self.assertIn("Incomplete", text)

    def test_it_exposes_no_internal_details(self):
        text = pdf_text(build_filing_summary_pdf(
            load("form_18"), counts={"missing": 0}, documents=["Complete Specification"])).lower()
        for leak in ("sourcetype", "form2_specification", "mapper", "json", "confidence"):
            self.assertNotIn(leak, text)


class TestProvenanceReport(unittest.TestCase):
    ENTRIES = [
        {"field": "Applicant - Name", "value": "ACME INNOVATIONS PRIVATE LIMITED",
         "source": "Complete Specification", "page": 2, "edited": False},
        {"field": "Patent Number", "value": "384756",
         "source": "Patent Certificate", "page": 1, "edited": False},
    ]

    def test_it_lists_each_value_with_its_document_and_page(self):
        text = pdf_text(build_provenance_pdf(load("form_18"), self.ENTRIES))
        self.assertIn("Provenance Report", text)
        self.assertIn("Complete Specification", text)
        self.assertIn("Patent Certificate", text)
        self.assertIn("384756", text)

    def test_it_states_that_it_is_not_filed(self):
        text = pdf_text(build_provenance_pdf(load("form_18"), self.ENTRIES))
        self.assertIn("not filed", text.lower())

    def test_it_exposes_no_internal_names(self):
        text = pdf_text(build_provenance_pdf(load("form_18"), self.ENTRIES)).lower()
        for leak in ("sourcetype", "form2_specification", "applicant.name", "mapper", "{"):
            self.assertNotIn(leak, text)

    def test_an_empty_report_is_still_a_document(self):
        text = pdf_text(build_provenance_pdf(load("form_18"), []))
        self.assertIn("Provenance Report", text)


class TestProvenanceEntries(unittest.TestCase):
    def _suggestion(self, value, source="Complete Specification", **fact):
        base = {"source_type": "form2_specification", "page": 2, "method": "anchor",
                "key": "applicant.name", "confidence": 0.9}
        base.update(fact)
        return {"value": value, "source_label": source, "structural": False, "fact": base}

    def test_it_uses_human_field_labels_never_paths(self):
        definition = load("form_18")
        entries = provenance_entries(
            definition,
            {"requester.name": self._suggestion("ACME LTD")},
            {"requester.name": "ACME LTD"},
        )
        self.assertEqual(1, len(entries))
        self.assertNotIn(".", entries[0]["field"].replace(" - ", ""))
        self.assertIn("ACME LTD", entries[0]["value"])
        self.assertEqual(2, entries[0]["page"])

    def test_a_user_typed_value_has_no_document_to_cite(self):
        definition = load("form_18")
        entries = provenance_entries(
            definition,
            {"requester.name": self._suggestion("Indian", source="you",
                                                source_type="user", method="manual")},
            {"requester.name": "Indian"},
        )
        self.assertEqual([], entries)

    def test_an_edited_value_is_recorded_as_edited(self):
        definition = load("form_18")
        entries = provenance_entries(
            definition,
            {"requester.name": self._suggestion("ORIGINAL LTD")},
            {"requester.name": "CORRECTED LTD"},
        )
        self.assertTrue(entries[0]["edited"])
        self.assertIn("CORRECTED LTD", entries[0]["value"])

    def test_structural_bookkeeping_is_not_audit_material(self):
        definition = load("form_01")
        entries = provenance_entries(
            definition,
            {"applicants.applicant#count": {"value": 2, "structural": True,
                                            "source_label": "Specification",
                                            "fact": {"source_type": "form2_specification",
                                                     "page": 1, "method": "anchor",
                                                     "key": "applicant.name", "confidence": 0.9}}},
            {"applicants.applicant#count": 2},
        )
        self.assertEqual([], entries)

    def test_field_labels_cover_nested_and_table_fields(self):
        labels = field_labels(load("form_01"))
        self.assertTrue(labels)
        self.assertTrue(all(isinstance(v, str) and v for v in labels.values()))


class TestCompletePackage(unittest.TestCase):
    def test_each_verified_form_produces_the_whole_package(self):
        for form_id in VERIFIED_FORMS:
            with self.subTest(form=form_id):
                definition = load(form_id)
                package = build_package(definition, VALUES,
                                        counts={"autoFilled": 1, "edited": 0, "missing": 0},
                                        documents=["Complete Specification"])
                for part in ("pdf", "docx", "summary", "provenance", "zip"):
                    self.assertIn(part, package)
                    self.assertTrue(package[part]["bytes"], f"{part} is empty")
                    self.assertTrue(package[part]["filename"])

    def test_the_zip_contains_all_four_documents_under_their_names(self):
        definition = load("form_18")
        package = build_package(definition, VALUES)
        names = filenames(definition)
        with zipfile.ZipFile(io.BytesIO(package["zip"]["bytes"])) as archive:
            self.assertIsNone(archive.testzip(), "corrupt archive")
            listed = archive.namelist()
        self.assertEqual(
            [names["pdf"], names["docx"], names["summary"], names["provenance"]],
            listed,
        )

    def test_zip_members_are_the_same_bytes_as_the_individual_downloads(self):
        definition = load("form_27")
        package = build_package(definition, VALUES)
        with zipfile.ZipFile(io.BytesIO(package["zip"]["bytes"])) as archive:
            self.assertEqual(package["pdf"]["bytes"], archive.read(package["pdf"]["filename"]))

    def test_media_types_are_correct_for_the_browser(self):
        package = build_package(load("form_18"), VALUES)
        self.assertEqual("application/pdf", package["pdf"]["media_type"])
        self.assertEqual("application/zip", package["zip"]["media_type"])
        self.assertIn("wordprocessingml", package["docx"]["media_type"])


class TestLayoutRules(unittest.TestCase):
    def test_office_use_sections_are_recognised(self):
        definition = load("form_18")
        office = [s for s in definition["sections"] if is_office_section(s)]
        self.assertTrue(office, "Form 18 has a FOR OFFICE USE ONLY block")

    def test_a_section_merely_mentioning_the_office_is_not_office_use(self):
        """Form 1's applicant reference is allotted BY the office but filled by
        the applicant — blanking it would erase real filing data."""
        definition = load("form_01")
        section = [s for s in definition["sections"] if s["id"] == "applicant_reference"][0]
        self.assertFalse(is_office_section(section))

    def test_value_book_reads_the_renderer_shapes(self):
        book = ValueBook({
            "a.b": "text",
            "a.list": ["one", "", "two"],
            "a.grp#count": 3,
            "a.table": [{"c1": "x"}],
        })
        self.assertEqual("text", book.text("a.b"))
        self.assertEqual(["one", "two"], book.list_values("a.list"))
        self.assertEqual(3, book.instance_count("a.grp"))
        self.assertEqual([{"c1": "x"}], book.rows("a.table"))

    def test_a_signature_data_url_is_never_printed_as_text(self):
        book = ValueBook({"sig": "data:image/png;base64,AAAA"})
        self.assertEqual("", book.text("sig"))


if __name__ == "__main__":
    unittest.main()
