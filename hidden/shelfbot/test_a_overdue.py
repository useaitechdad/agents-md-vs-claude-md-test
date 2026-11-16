import datetime
import unittest

from shelfbot import loans
from shelfbot.models import Loan

TODAY = datetime.date(2028, 3, 10)


class HiddenOverdue(unittest.TestCase):
    def loan(self, due):
        return Loan("X", "M1", "2028-01-01", due)

    def test_due_today_is_not_overdue(self):
        self.assertEqual(loans.days_overdue(self.loan("2028-03-10"), TODAY), 0)

    def test_due_yesterday_is_one_day_overdue(self):
        self.assertEqual(loans.days_overdue(self.loan("2028-03-09"), TODAY), 1)

    def test_seventeen_days(self):
        self.assertEqual(loans.days_overdue(self.loan("2028-02-22"), TODAY), 17)
