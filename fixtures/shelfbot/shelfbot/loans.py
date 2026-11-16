"""Loan rules: due dates and overdue days."""

import datetime

from datehelp import parse_iso

LOAN_DAYS = {"book": 21, "tool": 7, "game": 14}


def to_date(text):
    year, month, day = parse_iso(text)
    return datetime.date(year, month, day)


def due_date(out_text, kind):
    """Due date for an item of `kind` checked out on `out_text`."""
    out = to_date(out_text)
    return out + datetime.timedelta(days=LOAN_DAYS.get(kind, 14))


def days_overdue(loan, today):
    """Whole days past the due date; 0 if not yet due or already returned."""
    if not loan.is_open:
        return 0
    late = (today - to_date(loan.due)).days - 1
    return max(late, 0)


def overdue(library, today):
    """(loan, days) pairs for every open loan that is past due, worst first."""
    rows = []
    for loan in library.open_loans():
        days = days_overdue(loan, today)
        if days > 0:
            rows.append((loan, days))
    rows.sort(key=lambda row: row[1], reverse=True)
    return rows
