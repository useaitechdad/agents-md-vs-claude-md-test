"""Today's date, overridable for tests with SHELFBOT_TODAY=YYYY-MM-DD."""

import datetime
import os


def today():
    fixed = os.environ.get("SHELFBOT_TODAY")
    if fixed:
        return datetime.date.fromisoformat(fixed)
    return datetime.date.today()
