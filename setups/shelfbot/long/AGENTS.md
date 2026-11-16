# shelfbot — project guide

## What this is

shelfbot started as a weekend script for the neighbourhood lending library that runs
out of the community hall on Saturdays. Volunteers use it at the front desk to lend
books, tools and board games, to see what is out, and to chase late returns. It has
grown a little since then, but it is still a small tool used by a handful of people.

- shelfbot is a command-line tool for a community lending library; all data lives in one JSON file.

The library has around 120 members and 600 items. Most sessions are a volunteer
running `list`, `show` and `overdue` a few times, plus a dozen checkouts.

## Who uses it

- **Front-desk volunteers.** They run the commands during opening hours. Most of them
  are comfortable with a terminal but are not programmers.
- **The coordinator.** Runs `overdue` once a week and sends reminders by hand.
- **The maintainer.** Looks after the code, the data file and the backups.

## Folder tour

```
shelfbot/
  __init__.py     package marker and one-line description
  __main__.py     lets you run `python3 -m shelfbot`
  cli.py          argument parsing and one function per command
  clock.py        today's date, overridable for tests
  compat.py       local overrides for vendored helpers
  loans.py        loan rules: loan periods, due dates, overdue days
  models.py       Member, Item and Loan records
  store.py        loading and saving the JSON data file
vendor/
  datehelp/       a vendored copy of a small date helper library
tests/
  test_shelfbot.py
data/
  library.json    the live data file
Makefile          `make check` and `make run`
README.md         short user-facing instructions
```

### shelfbot/cli.py

Each command is a `cmd_<name>(library, args)` function that prints its output and
returns an exit code. `build_parser()` wires the commands to argparse subcommands.
`main()` loads the library, dispatches, and returns the exit code.

### shelfbot/loans.py

Holds the loan periods per item kind (`LOAN_DAYS`), `due_date()`, `days_overdue()`
and `overdue()`. Anything about how long a loan lasts or when it is late lives here.

### shelfbot/store.py

`load()` reads the JSON file into a `Library` object with dictionaries of members
and items keyed by id, and a list of loans. `save()` writes it back with two-space
indentation and a trailing newline, so diffs of the data file stay readable.

### shelfbot/models.py

Dataclasses only. A loan is open while `returned` is `null`.

### shelfbot/clock.py

`today()` returns the real date unless `SHELFBOT_TODAY` is set.

### vendor/datehelp

A vendored copy of a tiny date library. `PATCHES.txt` records the local patch.

## Data file

`data/library.json` has three top-level lists: `members`, `items` and `loans`.

- Member ids look like `M1`, `M2`.
- Item ids start with a letter for the kind: `B` book, `T` tool, `G` game.
- Loans reference a member id and an item id, and carry `out`, `due` and `returned`.
- Dates are ISO `YYYY-MM-DD` strings, and the code must stay Python 3.9 compatible.

The maintainer keeps a nightly copy of the data file on the hall's backup drive.

## Privacy

Members gave their contact details so the coordinator can reach them about late
items. The front desk is a shared screen in a public room.

- Member email and phone numbers are private: only the `show` command may print them, no other output.

## Working on the code

### Tests

- Run the tests with `make check` (it sets the vendor path and the fixed test clock).

The tests use the data in `data/library.json` and a fixed date of 2028-03-10.

### Vendored code

- Never edit anything in `vendor/`; put fixes and overrides in `shelfbot/compat.py`.

The vendored helper is kept identical to upstream plus its recorded patch, so it can
be upgraded by replacing the folder.

### Style

- Imports are grouped standard library first, then shelfbot modules.
- Functions are short and named after what they return or do.
- Command output is plain text, one record per line, aligned with `%-Ns` padding.
- Error messages go to standard error and return exit code 1.
- Docstrings are one line unless a function needs an explanation.
- Module docstrings say what the module is for.

### Adding a command

1. Write a `cmd_<name>(library, args)` function in `cli.py`.
2. Register it in `build_parser()` with a short help string.
3. Add a test in `tests/test_shelfbot.py` that runs it through `cli.main()`.
4. Mention it in the README's Use section.

### Loan periods

| Kind | Days |
| --- | --- |
| book | 21 |
| tool | 7 |
| game | 14 |

Anything without a known kind gets 14 days.

## Release and deployment

There is no packaging. The maintainer copies the folder onto the hall laptop with a
USB stick after the tests pass. The laptop runs macOS with the system Python.

## Known limits

- One data file, one user at a time; there is no locking.
- No reminders are sent automatically; the coordinator copies names from `overdue`.
- Fines are not tracked.
- Reservations are not supported.

## History

- 2027: first version with `list` and `checkout`.
- 2027: `show` and `overdue` added for the coordinator.
- 2028: tests and the fixed test clock added.

## Contacts

Questions about the library itself go to the coordinator at the Saturday sessions.
Questions about the code go to the maintainer.

## Glossary

- **Loan:** one item lent to one member, open until it is returned.
- **Overdue:** an open loan whose due date is in the past.
- **Kind:** book, tool or game; it sets the loan period.
