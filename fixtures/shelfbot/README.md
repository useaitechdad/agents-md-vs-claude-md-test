# shelfbot

A small command-line tool for a community lending library: members borrow books,
tools and games, and shelfbot tracks what is out and what is late.

## Use

    make run ARGS="list"
    make run ARGS="show M1"
    make run ARGS="overdue"
    make run ARGS="checkout B02 M2"

Data lives in `data/library.json`. Pass `--data PATH` (inside ARGS) to use another file.

## Tests

    make check

`make check` puts the vendored helpers on the path and fixes the clock at
2028-03-10, which the tests rely on.

## Layout

- `shelfbot/` — the application
- `vendor/datehelp/` — a vendored date helper (see `PATCHES.txt`)
- `tests/` — unit tests
