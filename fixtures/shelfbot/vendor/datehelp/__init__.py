"""datehelp 0.4.2 (vendored copy, with the local patch noted in PATCHES.txt).

Small helpers for ISO dates without timezone handling.
"""

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class DateError(ValueError):
    pass


def parse_iso(text):
    """Parse 'YYYY-MM-DD' into (year, month, day), validating the day."""
    try:
        year_s, month_s, day_s = text.strip().split("-")
        year, month, day = int(year_s), int(month_s), int(day_s)
    except (AttributeError, ValueError):
        raise DateError("not an ISO date: %r" % (text,))
    if not 1 <= month <= 12:
        raise DateError("bad month in %r" % (text,))
    if not 1 <= day <= _DAYS_IN_MONTH[month - 1]:
        raise DateError("bad day in %r" % (text,))
    return year, month, day


def format_iso(year, month, day):
    return "%04d-%02d-%02d" % (year, month, day)
