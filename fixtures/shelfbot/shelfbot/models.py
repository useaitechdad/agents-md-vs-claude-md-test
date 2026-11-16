"""Plain records for members, items and loans."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Member:
    id: str
    name: str
    email: str
    phone: str


@dataclass
class Item:
    id: str
    title: str
    kind: str


@dataclass
class Loan:
    item_id: str
    member_id: str
    out: str
    due: str
    returned: Optional[str] = None

    @property
    def is_open(self):
        return self.returned is None
