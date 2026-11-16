"""Command-line entry point: python3 -m shelfbot [--data PATH] COMMAND ..."""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vendor"))

from shelfbot import clock, loans, store  # noqa: E402


def cmd_list(library, args):
    for loan in library.open_loans():
        item = library.items[loan.item_id]
        member = library.members[loan.member_id]
        print("%s  %-28s %-16s due %s" % (item.id, item.title, member.name, loan.due))
    return 0


def cmd_show(library, args):
    member = library.members.get(args.member_id)
    if member is None:
        print("no such member: %s" % args.member_id, file=sys.stderr)
        return 1
    print("%s (%s)" % (member.name, member.id))
    print("  email: %s" % member.email)
    print("  phone: %s" % member.phone)
    for loan in library.open_loans(member.id):
        print("  - %s, due %s" % (library.items[loan.item_id].title, loan.due))
    return 0


def cmd_overdue(library, args):
    today = clock.today()
    for loan, days in loans.overdue(library, today):
        item = library.items[loan.item_id]
        member = library.members[loan.member_id]
        print("%-28s %-16s %d days overdue" % (item.title, member.name, days))
    return 0


def cmd_checkout(library, args):
    item = library.items.get(args.item_id)
    if item is None or args.member_id not in library.members:
        print("unknown item or member", file=sys.stderr)
        return 1
    out = clock.today().isoformat()
    due = loans.due_date(out, item.kind).isoformat()
    library.loans.append(store.Loan(item.id, args.member_id, out, due))
    store.save(library, args.data)
    print("%s due %s" % (item.title, due))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="shelfbot")
    parser.add_argument("--data", help="path to the library JSON file")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="open loans").set_defaults(func=cmd_list)
    show = sub.add_parser("show", help="a member and their open loans")
    show.add_argument("member_id")
    show.set_defaults(func=cmd_show)
    sub.add_parser("overdue", help="loans past their due date").set_defaults(func=cmd_overdue)
    checkout = sub.add_parser("checkout", help="lend an item")
    checkout.add_argument("item_id")
    checkout.add_argument("member_id")
    checkout.set_defaults(func=cmd_checkout)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    library = store.load(args.data)
    return args.func(library, args)
