"""Load and save the library's single JSON data file."""

import json
import os

from shelfbot.models import Item, Loan, Member

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "library.json")


class Library:
    def __init__(self, members, items, loans):
        self.members = {m.id: m for m in members}
        self.items = {i.id: i for i in items}
        self.loans = loans

    def open_loans(self, member_id=None):
        return [
            loan
            for loan in self.loans
            if loan.is_open and (member_id is None or loan.member_id == member_id)
        ]


def load(path=None):
    path = path or DEFAULT_PATH
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return Library(
        [Member(**m) for m in raw.get("members", [])],
        [Item(**i) for i in raw.get("items", [])],
        [Loan(**l) for l in raw.get("loans", [])],
    )


def save(library, path=None):
    path = path or DEFAULT_PATH
    raw = {
        "members": [vars(m) for m in library.members.values()],
        "items": [vars(i) for i in library.items.values()],
        "loans": [vars(l) for l in library.loans],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(raw, fh, indent=2)
        fh.write("\n")
