import datetime
import io
import os
import unittest
from contextlib import redirect_stdout

from shelfbot import cli, loans, store

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "library.json")


def run(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(["--data", DATA] + list(argv))
    return code, buf.getvalue()


class LoanRuleTests(unittest.TestCase):
    def test_book_due_after_21_days(self):
        self.assertEqual(loans.due_date("2028-03-01", "book"), datetime.date(2028, 3, 22))

    def test_tool_due_after_7_days(self):
        self.assertEqual(loans.due_date("2028-03-01", "tool"), datetime.date(2028, 3, 8))

    def test_returned_loan_is_never_overdue(self):
        library = store.load(DATA)
        returned = [l for l in library.loans if l.returned][0]
        self.assertEqual(loans.days_overdue(returned, datetime.date(2028, 12, 1)), 0)


class CommandTests(unittest.TestCase):
    def test_list_shows_open_loans_only(self):
        code, out = run("list")
        self.assertEqual(code, 0)
        self.assertIn("The Left Hand of Darkness", out)
        self.assertNotIn("Ticket to Ride", out)

    def test_show_member(self):
        code, out = run("show", "M3")
        self.assertEqual(code, 0)
        self.assertIn("A Pattern Language", out)

    def test_overdue_lists_late_items(self):
        code, out = run("overdue")
        self.assertEqual(code, 0)
        self.assertIn("Cordless drill", out)
        self.assertNotIn("A Pattern Language", out)


if __name__ == "__main__":
    unittest.main()
