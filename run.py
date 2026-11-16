#!/usr/bin/env python3
"""Bench harness for the AGENTS.md vs CLAUDE.md vs None video.

  run.py one --project P --setup S --task T --agent A [--model M] [--run N] [--dry-run]
  run.py warmup [--dry-run]          one uncounted Claude session in the clean config folder
  run.py probe --agent A [--dry-run] isolation check: is a global-file phrase in context?
  run.py pilot [--dry-run]           warmup + 3 probes + 6 pilot runs, then stops
  run.py pilot-claude [--dry-run]    the Claude part again (run 10), then stops
  run.py test2 [--dry-run]           test 2 batch (73 runs, resumable), then stops
  run.py summary                     test 2 grid of markers
  run.py test1 [--dry-run]           test 1 batch (81 runs, resumable), then stops
  run.py summary1                    test 1 pass counts per cell
  run.py test3-hunt [--dry-run]      test 3 stage 1 (20 Flash runs), then stops
  run.py summary3                    test 3 hunt mistake counts

Nothing under ~/.claude, ~/.codex or ~/.gemini is moved or edited by this script. Claude Code
runs with CLAUDE_CONFIG_DIR and Codex with CODEX_HOME pointing into the bench folder; Codex's
auth.json there is a symlink to ~/.codex/auth.json, so Codex itself may refresh that login.
Antigravity runs with your normal ~/.gemini config, including GEMINI.md.
Claude Code uses its own /login in that folder, or with INSTR_BENCH_USE_TOKEN=1 a token read
from the Keychain at call time and never written to disk.
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

KIT = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.abspath(os.environ.get("INSTR_BENCH", "/Users/Shared/instr-bench"))
ACTIVE = {}  # pid -> Popen of running agents, so an interrupted batch can stop them all
STOP = []  # set when a batch is interrupted
LAUNCH = threading.Lock()  # held while checking STOP and starting/registering an agent
HOME_CLAUDE = os.path.join(BENCH, "home", "claude")
HOME_CODEX = os.path.join(BENCH, "home", "codex")
KEYCHAIN_SERVICE = "instr-bench-claude-token"
TIMEOUT_S = 20 * 60

PROMPTS = {
    ("pocket-units", "T"): "Add a `to_kelvin(celsius)` function to `pocket_units/convert.py` and add a test for it.",
    ("pocket-units", "T6"): "Add a `furlong` length unit (201.168 metres) to `pocket_units/core/tables.py` and add a test for it.",
    ("shelfbot", "A"): "Overdue loans show one day too few. Fix it.",
    ("shelfbot", "B"): "Add a `share` command that prints a member's current loans as Markdown.",
    ("shelfbot", "C"): "Loans due on Feb 29 crash. Fix it.",
    ("shelfbot", "D"): "Add a `--json` flag to `list`.",
}

DEFAULT_MODELS = {
    "claude": "opus",
    "codex": "gpt-6-astra",
    "agy": "gemini-4-argon-high",
    "agy-claude": "claude-opus-5-5-high",
    "agy-flash": "gemini-3.8-flash-high",
    "agy-hydrogen": "gemini-4-hydrogen-high",
}

# For `probe`: a phrase that appears only in your own global instruction file for that
# agent (~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, ~/.gemini/GEMINI.md), never in the
# fixtures. Set it with INSTR_BENCH_CANARY_CLAUDE / _CODEX / _AGY.
CANARIES = {
    agent: os.environ.get("INSTR_BENCH_CANARY_" + agent.upper(), "<a phrase from your global file>")
    for agent in ("claude", "codex", "agy")
}


def claude_token():
    proc = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                          capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        sys.exit("No Claude token in the Keychain. Run `claude setup-token` in your own Terminal, then:\n"
                 "  security add-generic-password -s %s -a bench -w\n"
                 "and paste the token when asked." % KEYCHAIN_SERVICE)
    return proc.stdout.strip()


def ensure_homes():
    if not os.path.isdir(BENCH):
        os.makedirs(BENCH, mode=0o700)  # private to you; an existing folder is left as it is
    os.makedirs(HOME_CLAUDE, exist_ok=True)
    os.makedirs(HOME_CODEX, exist_ok=True)
    link = os.path.join(HOME_CODEX, "auth.json")
    if not os.path.lexists(link):
        os.symlink(os.path.expanduser("~/.codex/auth.json"), link)


def agent_command(agent, model, prompt, repo, dry_run):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDECODE", "CLAUDE_CONFIG_DIR")}
    if agent == "claude":
        env["CLAUDE_CONFIG_DIR"] = HOME_CLAUDE
        env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
        # Default: the clean config folder holds its own /login. Set INSTR_BENCH_USE_TOKEN=1
        # to use a `claude setup-token` token from the Keychain instead.
        if os.environ.get("INSTR_BENCH_USE_TOKEN") == "1":
            env["CLAUDE_CODE_OAUTH_TOKEN"] = "<keychain>" if dry_run else claude_token()
        cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
               "--model", model, "--effort", "high", "--dangerously-skip-permissions",
               "--no-session-persistence",
               # Account-level connectors and skills would otherwise load into
               # every run; Codex and agy get neither.
               "--strict-mcp-config", "--disable-slash-commands"]
    elif agent == "codex":
        env["CODEX_HOME"] = HOME_CODEX
        cmd = ["codex", "exec", "--json", "-m", model, "-c", 'model_reasoning_effort="high"',
               "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-C", repo, prompt]
    elif agent.startswith("agy"):
        cmd = ["agy", "-p", prompt, "--output-format", "stream-json", "--model", model,
               "--dangerously-skip-permissions"]
    else:
        sys.exit("unknown agent %s" % agent)
    return cmd, env


def version(agent):
    exe = {"claude": "claude", "codex": "codex"}.get(agent, "agy")
    return subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip()


def make_repo(project, setup, dest):
    shutil.copytree(os.path.join(KIT, "fixtures", project), dest,
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    overlay = os.path.join(KIT, "setups", project, setup)
    for root, _, files in os.walk(overlay):
        for name in files:
            if name == ".keep":
                continue
            src = os.path.join(root, name)
            dst = os.path.join(dest, os.path.relpath(src, overlay))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
    git = ["git", "-C", dest]
    subprocess.run(git + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["-c", "user.name=bench", "-c", "user.email=bench@example.invalid",
                          "commit", "-qm", "base"], check=True)
    return subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def last_usage(events_path):
    usage = None
    with open(events_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"usage"' in line or '"total_cost_usd"' in line:
                try:
                    usage = json.loads(line)
                except ValueError:
                    pass
    return usage


def run_agent(run_dir, agent, model, prompt, repo, dry_run, meta):
    cmd, env = agent_command(agent, model, prompt, repo, dry_run)
    if dry_run:
        print("[dry-run] %s\n  cwd=%s\n  env: %s" % (
            " ".join(cmd), repo,
            ", ".join("%s=%s" % (k, env[k]) for k in ("CLAUDE_CONFIG_DIR", "CODEX_HOME") if k in env)))
        return None
    meta.update(agent=agent, model=model, prompt=prompt, cli_version=version(agent),
                started=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    events = os.path.join(run_dir, "events.jsonl")
    t0 = time.time()
    with open(events, "w") as out, open(os.path.join(run_dir, "stderr.log"), "w") as err:
        # Own process group, so a timeout also stops anything the agent started.
        with LAUNCH:  # an interrupted batch either sees this agent in ACTIVE or it never starts
            if STOP:
                raise RuntimeError("interrupted before start: %s" % repo)
            proc = subprocess.Popen(cmd, cwd=repo, env=env, stdout=out, stderr=err,
                                    stdin=subprocess.DEVNULL, start_new_session=True)
            ACTIVE[proc.pid] = proc
        try:
            meta["exit_code"] = proc.wait(timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            meta["exit_code"] = "timeout"
        finally:  # also on Ctrl-C: stop the agent and anything it left running
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            proc.wait()
            ACTIVE.pop(proc.pid, None)
    meta["wall_seconds"] = round(time.time() - t0, 1)
    meta["usage_event"] = last_usage(events)
    with open(os.path.join(run_dir, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    return meta


def one(project, setup, task, agent, model=None, run=1, dry_run=False):
    model = model or DEFAULT_MODELS[agent]
    if setup not in os.listdir(os.path.join(KIT, "setups", project)) or not re.fullmatch(r"[A-Za-z0-9_-]+", setup):
        sys.exit("unknown setup %s for %s" % (setup, project))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", model):
        sys.exit("model name must be letters, digits, dot, dash or underscore: %s" % model)
    if project == "pocket-units":
        task = "T6" if setup == "S6" else "T"
    prompt = PROMPTS[(project, task)]
    run_dir = os.path.join(BENCH, "runs", project, setup, task, agent, model, "r%d" % run)
    if os.path.exists(run_dir) and not dry_run:
        sys.exit("already exists, not overwriting: %s" % run_dir)
    repo = os.path.join(run_dir, "repo")
    if dry_run:
        print("\n== %s %s %s %s r%d" % (project, setup, task, agent, run))
        return run_agent(run_dir, agent, model, prompt, repo, True, {})
    ensure_homes()
    os.makedirs(run_dir)
    base = make_repo(project, setup, repo)
    meta = {"project": project, "setup": setup, "task": task, "run": run, "base_commit": base}
    with open(os.path.join(run_dir, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    run_agent(run_dir, agent, model, prompt, repo, False, meta)
    if STOP:
        raise RuntimeError("interrupted, not graded: %s" % run_dir)
    with open(os.path.join(run_dir, "grade.stdout"), "w") as gout:
        graded = subprocess.run([sys.executable, os.path.join(KIT, "grade.py"), run_dir],
                                stdout=gout, stderr=subprocess.STDOUT)
    if graded.returncode != 0 or not os.path.exists(os.path.join(run_dir, "grade.json")):
        meta["grade_error"] = True
        with open(os.path.join(run_dir, "meta.json"), "w") as fh:
            json.dump(meta, fh, indent=2)
        raise RuntimeError("GRADER FAILED, no grade.json: %s (see grade.stdout)" % run_dir)
    print("done %s  exit=%s  %.0fs" % (run_dir, meta.get("exit_code"), meta.get("wall_seconds", 0)))
    return meta


def scratch_repo(name):
    run_dir = os.path.join(BENCH, "scratch", name + time.strftime("-%Y%m%d-%H%M%S"))
    os.makedirs(run_dir)
    repo = os.path.join(run_dir, "repo")
    make_repo("pocket-units", "S0", repo)
    return repo


def warmup(dry_run=False):
    prompt = "Reply with the single word ready."
    if dry_run:
        print("\n== warmup (claude, uncounted)")
        return run_agent(None, "claude", DEFAULT_MODELS["claude"], prompt, "<scratch>", True, {})
    ensure_homes()
    repo = scratch_repo("warmup")
    run_agent(os.path.dirname(repo), "claude", DEFAULT_MODELS["claude"], prompt, repo, False, {})
    print("warmup done:", repo)


def probe(agent, dry_run=False):
    """Asks the agent whether a phrase from your global file is in its context. This is the
    agent's own answer, so read the reply (and the events log) yourself."""
    phrase = CANARIES[agent]
    if not dry_run and (not phrase.strip() or phrase.startswith("<")):
        sys.exit("Set INSTR_BENCH_CANARY_%s to a phrase from your own global file first." % agent.upper())
    prompt = ("Do not use any tools. Apart from this message, does any text in your context "
              "(system prompt, instruction or memory files) contain the exact phrase \"%s\"? "
              "Answer YES or NO, then list the instruction or memory files you were given, if any." % phrase)
    if dry_run:
        print("\n== probe %s" % agent)
        return run_agent(None, agent, DEFAULT_MODELS[agent], prompt, "<scratch>", True, {})
    ensure_homes()
    repo = scratch_repo("probe-" + agent)
    meta = {"probe": agent, "phrase": phrase}
    run_agent(os.path.dirname(repo), agent, DEFAULT_MODELS[agent], prompt, repo, False, meta)
    print("probe %s done: %s" % (agent, os.path.dirname(repo)))


def pilot(dry_run=False):
    warmup(dry_run)
    for agent in ("claude", "codex", "agy"):
        probe(agent, dry_run)
    for agent in ("claude", "codex", "agy"):
        one("pocket-units", "S3", "T", agent, dry_run=dry_run, run=0)
        one("shelfbot", "five", "C", agent, dry_run=dry_run, run=0)
    print("\nPilot finished. Stop here and report before any batch.")


def pilot_claude(dry_run=False):
    """The Claude part of the pilot again, saved as run 10."""
    warmup(dry_run)
    probe("claude", dry_run)
    one("pocket-units", "S3", "T", "claude", dry_run=dry_run, run=10)
    one("shelfbot", "five", "C", "claude", dry_run=dry_run, run=10)
    print("\nClaude pilot finished. Stop here and report before any batch.")


def test2_jobs():
    """Test 2: S0-S6 x 3 agents x runs 1-3, S4 on Claude runs 1-10, S2x = S2 in agy with Claude."""
    jobs = []
    for setup in ("S0", "S1", "S2", "S3", "S4", "S5", "S6"):
        for agent in ("claude", "codex", "agy"):
            n = 10 if (setup, agent) == ("S4", "claude") else 3
            jobs += [("pocket-units", setup, "T", agent, r) for r in range(1, n + 1)]
    jobs += [("pocket-units", "S2", "T", "agy-claude", r) for r in (1, 2, 3)]
    return jobs


def test1_jobs():
    """Test 1: shelfbot tasks A-C x setups none/five/long x 3 agents x runs 1-3 (81)."""
    return [("shelfbot", setup, task, agent, r)
            for task in ("A", "B", "C") for setup in ("none", "five", "long")
            for agent in ("claude", "codex", "agy") for r in (1, 2, 3)]


def summary1():
    """Test 1 grid: pass count out of runs done, plus median seconds, per cell."""
    import statistics
    rows = {}
    for j in test1_jobs():
        d = job_dir(*j)
        if not os.path.exists(os.path.join(d, "grade.json")):
            continue
        with open(os.path.join(d, "grade.json")) as fh:
            gr = json.load(fh)
        with open(os.path.join(d, "meta.json")) as fh:
            meta = json.load(fh)
        rows.setdefault((j[2], j[1], j[3]), []).append((gr.get("pass"), meta.get("wall_seconds", 0), gr))
    for (task, setup, agent), rs in sorted(rows.items()):
        notes = []
        for _, _, gr in rs:
            if gr.get("contact_leaked"):
                notes.append("leak")
            if not gr.get("vendor_untouched", True):
                notes.append("vendor")
            if not gr.get("hidden_tests_pass"):
                notes.append("hidden-fail")
        print("%s %-5s %-7s %d/%d  median %3.0fs  %s" % (task, setup, agent, sum(bool(r[0]) for r in rs),
              len(rs), statistics.median(r[1] for r in rs), " ".join(notes)))
    report_ungraded(test1_jobs())


def test3_hunt_jobs():
    """Test 3 stage 1: Gemini 3.8 Flash, no file, shelfbot A-D, 5 runs each (20)."""
    return [("shelfbot", "t3-none", task, "agy-flash", r) for task in ("A", "B", "C", "D") for r in range(1, 6)]


def summary3():
    """Test 3 hunt: per task, how many of the runs show each pre-listed mistake (3 of 5 qualifies)."""
    keys = ("no_test_run", "unrelated_files", "new_dependency", "debug_print")
    for task in ("A", "B", "C", "D"):
        gs = []
        for j in test3_hunt_jobs():
            g = os.path.join(job_dir(*j), "grade.json")
            if j[2] == task and os.path.exists(g):
                with open(g) as fh:
                    gs.append(json.load(fh))
        if not gs:
            continue
        counts = {k: sum(bool(g["mistakes"][k]) for g in gs) for k in keys}
        flags = [k for k, n in counts.items() if n >= 3]
        print("%s  pass %d/%d  %s  %s" % (task, sum(bool(g.get("pass")) for g in gs), len(gs),
              "  ".join("%s %d" % kv for kv in counts.items()), ("QUALIFIES: " + ", ".join(flags)) if flags else ""))
    report_ungraded(test3_hunt_jobs())


def report_ungraded(jobs):
    """Runs that were started but have no grade.json are left out of the tables above; list them."""
    missing = [job_dir(*j) for j in jobs
               if os.path.exists(job_dir(*j)) and not os.path.exists(os.path.join(job_dir(*j), "grade.json"))]
    for d in missing:
        print("NOT GRADED (left out above): %s" % d)


def job_dir(project, setup, task, agent, run):
    if project == "pocket-units":
        task = "T6" if setup == "S6" else "T"
    return os.path.join(BENCH, "runs", project, setup, task, agent, DEFAULT_MODELS[agent], "r%d" % run)


def batch(jobs, dry_run=False, summary_cmd="summary"):
    """Run jobs one at a time per tool, the three tools side by side. Finished runs are skipped,
    so the same command resumes after an interruption."""
    todo, broken = [], []
    for j in jobs:
        d = job_dir(*j)
        if os.path.exists(os.path.join(d, "grade.json")):
            continue
        (broken if os.path.exists(d) else todo).append(j)
    for j in broken:
        print("SKIPPED, half-finished run folder (move it aside to redo): %s" % job_dir(*j))
    print("%d runs to do, %d already done" % (len(todo), len(jobs) - len(todo) - len(broken)))
    if dry_run:
        for j in todo:
            print("  ", *j)
        return
    if not todo:
        return
    if any(j[3] == "claude" for j in todo):
        warmup()
    lanes = {}
    for j in todo:
        lanes.setdefault("agy" if j[3].startswith("agy") else j[3], []).append(j)

    failed = []

    def lane(js):
        for (project, setup, task, agent, run) in js:
            if STOP:
                return
            try:
                one(project, setup, task, agent, run=run)
            except BaseException as exc:  # one() exits on a clash; keep the lane going
                failed.append(job_dir(project, setup, task, agent, run))
                print("FAILED %s: %r" % (failed[-1], exc))

    threads = [threading.Thread(target=lane, args=(js,), daemon=True) for js in lanes.values()]
    for t in threads:
        t.start()
    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(0.5)
    except KeyboardInterrupt:
        with LAUNCH:  # after this, no new agent can start
            STOP.append(True)
            procs = list(ACTIVE.values())
        print("\nInterrupted: stopping running agents.")
        for proc in procs:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        for t in threads:  # workers finish quickly once their agent is gone; none grade
            t.join()
        sys.exit(130)
    if failed:
        sys.exit("%d runs failed; see above." % len(failed))
    print("\nBatch finished. Run `python3 run.py %s` and stop before the next test." % summary_cmd)


def summary():
    """Test 2 grid: for each setup and agent, which marker the target file got, per run."""
    rows = {}
    for j in test2_jobs():
        g = os.path.join(job_dir(*j), "grade.json")
        if not os.path.exists(g):
            continue
        with open(g) as fh:
            gr = json.load(fh)
        mark = gr.get("marker_on_target") or "none"
        if gr.get("read_instruction_files"):
            mark += "*"
        rows.setdefault((j[1], j[3]), []).append(mark)
    for (setup, agent), marks in sorted(rows.items()):
        print("%-4s %-11s %s" % (setup, agent, " ".join(marks)))
    print("(* = a tool call read or tried to read an instruction file; pattern match, a hint)")
    report_ungraded(test2_jobs())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--project", required=True, choices=["pocket-units", "shelfbot"])
    o.add_argument("--setup", required=True)
    o.add_argument("--task", default="T")
    o.add_argument("--agent", required=True, choices=sorted(DEFAULT_MODELS))
    o.add_argument("--model")
    o.add_argument("--run", type=int, default=1)
    o.add_argument("--dry-run", action="store_true")
    w = sub.add_parser("warmup")
    w.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("probe")
    p.add_argument("--agent", required=True, choices=sorted(CANARIES))
    p.add_argument("--dry-run", action="store_true")
    pl = sub.add_parser("pilot")
    pl.add_argument("--dry-run", action="store_true")
    pc = sub.add_parser("pilot-claude")
    pc.add_argument("--dry-run", action="store_true")
    t2 = sub.add_parser("test2")
    t2.add_argument("--dry-run", action="store_true")
    sub.add_parser("summary")
    t1 = sub.add_parser("test1")
    t1.add_argument("--dry-run", action="store_true")
    sub.add_parser("summary1")
    t3 = sub.add_parser("test3-hunt")
    t3.add_argument("--dry-run", action="store_true")
    sub.add_parser("summary3")
    a = ap.parse_args()
    if a.cmd == "one":
        try:
            one(a.project, a.setup, a.task, a.agent, a.model, a.run, a.dry_run)
        except RuntimeError as exc:
            sys.exit(str(exc))
    elif a.cmd == "warmup":
        warmup(a.dry_run)
    elif a.cmd == "probe":
        probe(a.agent, a.dry_run)
    elif a.cmd == "pilot-claude":
        pilot_claude(a.dry_run)
    elif a.cmd == "test2":
        batch(test2_jobs(), a.dry_run)
    elif a.cmd == "summary":
        summary()
    elif a.cmd == "test1":
        batch(test1_jobs(), a.dry_run, "summary1")
    elif a.cmd == "summary1":
        summary1()
    elif a.cmd == "test3-hunt":
        batch(test3_hunt_jobs(), a.dry_run, "summary3")
    elif a.cmd == "summary3":
        summary3()
    else:
        pilot(a.dry_run)


if __name__ == "__main__":
    main()
