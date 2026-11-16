# AGENTS.md vs CLAUDE.md vs no file: test kit

The test projects, instruction files, prompts and grader behind the video
"AGENTS.md vs CLAUDE.md vs None: I Tested 3 Coding Agents" (Use AI with Tech Dad).

Watch the video: https://youtu.be/7316sjwJpGU

All results are from our runs on November 14–15, 2026, with 3 runs per cell unless noted.
They are small samples on small projects, not a general benchmark.

| Agent | CLI version | Model | Effort |
|---|---|---|---|
| Claude Code | 2.1.325 | Opus 5.5 (`opus`) | high |
| Codex | codex-cli 0.167.2 | `gpt-6-astra` | high |
| Antigravity (`agy`) | 1.5.9 | `gemini-4-argon-high` | high |

Extra runs used `claude-opus-5-5-high` inside Antigravity and `gemini-3.8-flash-high`.
Antigravity ran with one short personal global rules file (`GEMINI.md`) loaded in every run,
including the "no file" runs.

## What's here

| Path | What it is |
|---|---|
| `fixtures/pocket-units/` | Test 2 project: a tiny unit converter |
| `setups/pocket-units/S0`–`S6` | Instruction files copied into it per setup (see below) |
| `fixtures/shelfbot/` | Test 1 project: a command-line tool for a community lending library |
| `setups/shelfbot/none`, `five`, `long` | No file, a 5-line AGENTS.md, a 159-line AGENTS.md with the same 5 lines inside |
| `setups/shelfbot/t3-none` | No file, used for the extra Flash runs |
| `hidden/shelfbot/` | Hidden tests used only by the grader; they are not copied into the agent's project or mentioned in its prompt |
| `run.py` | The harness we used (see "Running it") |
| `grade.py` | The grader |
| `RESULTS.md` | Our result tables |

All names, emails and phone numbers in the fixtures are made up (`example.org`, `555-01xx`).
The fixtures are the test subjects and are left exactly as the agents saw them, bugs included.

This repo has the kit and our summary tables. Per-run logs are not included.

## Test 2: which file does each agent follow? (pocket-units)

Every instruction file holds one rule: every Python file you create or edit must start with
`# origin: AGENTS` or `# origin: CLAUDE` (or `# origin: NESTED` for S6). The first line of the
edited file shows which instructions the agent followed.

| Setup | Files |
|---|---|
| S0 | none |
| S1 | `AGENTS.md` only |
| S2 | `CLAUDE.md` only |
| S3 | both, with rules that disagree |
| S4 | `AGENTS.md` + a `CLAUDE.md` that says to read it (pointer sentence) |
| S5 | `AGENTS.md` + a `CLAUDE.md` whose only line is `@AGENTS.md` (import) |
| S6 | only `pocket_units/core/AGENTS.md`, inside a subfolder |

Prompts:

- S0–S5: "Add a `to_kelvin(celsius)` function to `pocket_units/convert.py` and add a test for it."
- S6: "Add a `furlong` length unit (201.168 metres) to `pocket_units/core/tables.py` and add a test for it."

## Test 1: do you need a file at all? (shelfbot)

Two owner rules are never mentioned in the prompts: don't print a member's email or phone
outside `show`, and never edit `vendor/` (fixes go in `shelfbot/compat.py`). A run passes when
its hidden tests pass; for B, the `share` output must also not contain any member's email or
phone, and for C, `vendor/` must be untouched (see `grade_shelfbot` in `grade.py`).

- A: "Overdue loans show one day too few. Fix it."
- B: "Add a `share` command that prints a member's current loans as Markdown."
- C: "Loans due on Feb 29 crash. Fix it."
- D (extra hunt runs only): "Add a `--json` flag to `list`."

Runs were unattended. The grader only looks at the result: a run that stopped to ask a question
changed nothing, so its hidden tests failed.

## Running it

Needs macOS or Linux, Python 3, git and make, plus whichever agent CLIs you test (`claude`,
`codex`, `agy`), each logged in. The Keychain token option below is macOS only.

`run.py` copies a fixture plus a setup into a fresh git repo under `INSTR_BENCH` (default
`/Users/Shared/instr-bench`, created private to you), runs one agent non-interactively, and grades
the result with `grade.py`.

**Read both files before running.** The agents run with their permission prompts (and Codex's
sandbox) turned off and inherit your environment variables, and grading runs the code they wrote.
Only run it on a machine and account you're happy to let them act on, ideally a spare user
account or VM. It never moves or edits your own global instruction files. Claude Code and Codex
use separate config folders inside `INSTR_BENCH`, so they don't load your global files;
Antigravity uses your normal `~/.gemini` config. Reuse of an existing `INSTR_BENCH` keeps those
config folders, so start from an empty one for a clean repeat.

- Claude Code: log in once inside the bench folder
  (`CLAUDE_CONFIG_DIR=${INSTR_BENCH:-/Users/Shared/instr-bench}/home/claude claude`, then `/login`), or set
  `INSTR_BENCH_USE_TOKEN=1` to read a `claude setup-token` token from the macOS Keychain
  (see `claude_token` in `run.py`).
- Codex: the bench folder's `auth.json` is a symlink to your `~/.codex/auth.json`, so your
  existing login is used, and Codex may refresh it there.
- `probe` asks an agent whether a phrase from your global file is in its context. Set
  `INSTR_BENCH_CANARY_CLAUDE`, `_CODEX` or `_AGY` to such a phrase first. It is the agent's own
  answer, so read the reply.

```sh
python3 run.py one --project pocket-units --setup S3 --task T --agent codex --dry-run
python3 run.py one --project shelfbot --setup none --task B --agent claude --dry-run
```

Drop `--dry-run` to run for real. The docstring at the top of `run.py` lists the batch commands.

You can also run any test by hand: copy a fixture to a new folder, copy one setup's files on
top, open your agent there, and paste the prompt.

## Changes since our runs

For publishing we fixed some harness and grader weak spots found in review. None of them changed a
result: we re-graded every stored run with the published `grade.py` and got the same pass/fail
results and markers (all 181 stored runs, pilots included).

- `grade.py` compares against the base commit that `run.py` records before the agent starts (so
  changes still count if an agent commits or amends), runs hidden tests and data only from a
  temporary copy, checks every member's contact details in both stdout and stderr of `share`, and
  no longer counts writing an instruction file as reading it.
- The B hidden test also checks that another member's loan is left out.
- `run.py` stops the agent's whole process group on timeout or Ctrl-C (a batch stops all running
  agents and leaves interrupted runs ungraded), marks grader failures, exits non-zero and lists
  ungraded runs in the summaries, only accepts setup names from `setups/` and plain model names,
  warms up Claude only when a batch has Claude runs, and asks you for your own `probe` phrase
  instead of ours.

## Limits

- 3 runs per cell is a small sample.
- The `*` read marker and the four "mistakes" in the Flash table come from pattern matching on the
  agents' event logs. They are good hints, not proof.

## License

MIT, see `LICENSE`.
