import datetime
import unittest

from common import cli
from shelfbot import loans


class HiddenLeapDay(unittest.TestCase):
    def test_parse_leap_day(self):
        self.assertEqual(loans.to_date("2028-02-29"), datetime.date(2028, 2, 29))

    def test_non_leap_feb_29_still_rejected(self):
        with self.assertRaises(ValueError):
            loans.to_date("2027-02-29")

    def test_commands_survive_leap_day_loan(self):
        for command in ("list", "overdue"):
            code, out, err = cli("library_a.json", command)
            self.assertEqual(code, 0, "%s crashed: %s" % (command, err[-400:]))
            self.assertIn("Ten Days Late Book", out)
