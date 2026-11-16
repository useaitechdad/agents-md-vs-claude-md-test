# Results (our runs, November 14–15, 2026)

Small samples: 3 runs per cell unless noted. Output of `run.py summary`, `summary1` and `summary3`.

## Test 2: which instructions were followed (pocket-units)

Each entry is the marker on the first line of the edited file, one per run.
`*` means the event log shows a tool call that read or tried to read an instruction file
(pattern matching in `grade.py`, a hint rather than proof).
`agy-claude` is Antigravity running `claude-opus-5-5-high`.
S4 on Claude Code was run 10 times; every other cell 3 times.

```
S0   agy         none none none
S0   claude      none* none none*
S0   codex       none* none* none
S1   agy         AGENTS AGENTS AGENTS
S1   claude      AGENTS AGENTS AGENTS
S1   codex       AGENTS* AGENTS* AGENTS*
S2   agy         CLAUDE* CLAUDE* CLAUDE*
S2   agy-claude  CLAUDE* CLAUDE* CLAUDE*
S2   claude      CLAUDE CLAUDE CLAUDE
S2   codex       CLAUDE* CLAUDE* CLAUDE*
S3   agy         AGENTS AGENTS* AGENTS*
S3   claude      CLAUDE CLAUDE* CLAUDE*
S3   codex       AGENTS* AGENTS* AGENTS*
S4   agy         AGENTS* AGENTS* AGENTS*
S4   claude      AGENTS* AGENTS* AGENTS* AGENTS* AGENTS* AGENTS* AGENTS* AGENTS* AGENTS* AGENTS*
S4   codex       AGENTS* AGENTS* AGENTS*
S5   agy         AGENTS AGENTS* AGENTS
S5   claude      AGENTS AGENTS AGENTS
S5   codex       AGENTS* AGENTS* AGENTS*
S6   agy         NESTED* NESTED* NESTED*
S6   claude      NESTED* NESTED* NESTED*
S6   codex       NESTED* NESTED* NESTED*
(* = a tool call read or tried to read an instruction file)
```

## Test 1: pass counts (shelfbot)

Medians are wall-clock seconds. `hidden-fail` = hidden tests failed in at least one run;
`vendor` = at least one run edited `vendor/`. Antigravity's three no-file fails: twice it stopped
to ask a question and changed nothing (one job B run, one job C run), and once it fixed the bug
inside `vendor/` (job C).

```
A five  agy     3/3  median  97s
A five  claude  3/3  median  29s
A five  codex   3/3  median  35s
A long  agy     3/3  median  79s
A long  claude  3/3  median  28s
A long  codex   3/3  median  35s
A none  agy     3/3  median  69s
A none  claude  3/3  median  25s
A none  codex   3/3  median  33s
B five  agy     3/3  median 132s
B five  claude  3/3  median  34s
B five  codex   3/3  median  57s
B long  agy     3/3  median  98s
B long  claude  3/3  median  26s
B long  codex   3/3  median  53s
B none  agy     2/3  median 111s  hidden-fail
B none  claude  3/3  median  42s
B none  codex   3/3  median  62s
C five  agy     3/3  median 130s
C five  claude  3/3  median  30s
C five  codex   3/3  median  53s
C long  agy     3/3  median 137s
C long  claude  3/3  median  40s
C long  codex   3/3  median  48s
C none  agy     1/3  median 129s  hidden-fail vendor
C none  claude  3/3  median  31s
C none  codex   3/3  median  48s
```

## Extra: Gemini 3.8 Flash in Antigravity, no file (shelfbot A–D)

5 runs per job. One job C run was stopped by hand and is not counted. One job D run timed out
(counted as not passed). The columns count four mistakes we looked for: not running the tests,
touching unrelated files, adding a dependency, leaving debug prints.

```
A  pass 5/5  no_test_run 0  unrelated_files 0  new_dependency 0  debug_print 0
B  pass 5/5  no_test_run 0  unrelated_files 0  new_dependency 0  debug_print 0
C  pass 4/4  no_test_run 0  unrelated_files 0  new_dependency 0  debug_print 0
D  pass 4/5  no_test_run 0  unrelated_files 0  new_dependency 0  debug_print 0
```
