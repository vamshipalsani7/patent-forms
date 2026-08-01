"""Value normalisation — the contract every extractor's Facts depend on.

Dates get their own test file because they are the one place an extractor can
be confidently, invisibly wrong. A misread name looks odd in review; a date
silently read month-first ("03/04/2018" as 4 March rather than 3 April) looks
entirely plausible and lands on a filing that turns on it.
"""

from __future__ import annotations

import unittest

import context  # noqa: F401  — sets sys.path

from extractors.normalize import clean_value, normalize_date


class TestCleanValue(unittest.TestCase):
    def test_collapses_pdf_whitespace_runs(self):
        self.assertEqual("A Better Widget", clean_value("A    Better     Widget"))

    def test_strips_table_and_label_punctuation(self):
        self.assertEqual("Acme Ltd", clean_value("  | Acme Ltd ,  "))

    def test_strips_smart_quotes_left_by_certificate_titles(self):
        self.assertEqual("A NOVEL METHOD", clean_value("“A NOVEL METHOD”"))

    def test_leaves_interior_punctuation_alone(self):
        self.assertEqual(
            "12 MG Road, Bengaluru 560001",
            clean_value("12 MG Road, Bengaluru 560001"),
        )


class TestDateFormats(unittest.TestCase):
    def test_reads_iso(self):
        self.assertEqual("2018-03-30", normalize_date("2018-03-30"))

    def test_reads_slash_separated(self):
        self.assertEqual("2018-03-30", normalize_date("30/03/2018"))

    def test_reads_dash_and_dot_separated(self):
        self.assertEqual("2018-03-30", normalize_date("30-03-2018"))
        self.assertEqual("2018-03-30", normalize_date("30.03.2018"))

    def test_reads_spelled_out_day_month_year(self):
        self.assertEqual("2019-03-12", normalize_date("12 March 2019"))

    def test_reads_abbreviated_month(self):
        self.assertEqual("2019-03-12", normalize_date("12 Mar 2019"))

    def test_reads_month_first_american_form(self):
        self.assertEqual("2018-03-12", normalize_date("March 12, 2018"))

    def test_reads_legal_prose_with_an_ordinal(self):
        self.assertEqual("2020-03-12", normalize_date("this 12th day of March, 2020"))

    def test_ignores_surrounding_label_text(self):
        self.assertEqual("2021-07-15", normalize_date("Date of Grant 15/07/2021"))


class TestDayFirstConvention(unittest.TestCase):
    """IPO documents are day-first. An ambiguous numeric date must not flip."""

    def test_ambiguous_numeric_date_is_read_day_first(self):
        self.assertEqual("2018-04-03", normalize_date("03/04/2018"))

    def test_a_day_above_twelve_still_reads_day_first(self):
        self.assertEqual("2018-03-30", normalize_date("30/03/2018"))


class TestRejection(unittest.TestCase):
    """Unparseable input returns None so no Fact is emitted at all.

    A blank field is visible to the user; a wrongly-parsed date is not.
    """

    def test_returns_none_for_empty_input(self):
        self.assertIsNone(normalize_date(""))

    def test_returns_none_when_there_is_no_date(self):
        self.assertIsNone(normalize_date("to be notified in due course"))

    def test_returns_none_for_a_two_digit_year(self):
        self.assertIsNone(normalize_date("30/03/18"))

    def test_returns_none_for_an_impossible_month(self):
        self.assertIsNone(normalize_date("30/13/2018"))

    def test_returns_none_for_an_unknown_month_name(self):
        self.assertIsNone(normalize_date("12 Smarch 2019"))


if __name__ == "__main__":
    unittest.main()
