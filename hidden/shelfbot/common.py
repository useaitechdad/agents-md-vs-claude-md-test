import os
import subprocess
import sys

REPO = os.environ["BENCH_REPO"]
HERE = os.path.dirname(os.path.abspath(__file__))


def cli(data, *argv):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([os.path.join(REPO, "vendor"), REPO])
    env.setdefault("SHELFBOT_TODAY", "2028-03-10")
    proc = subprocess.run(
        [sys.executable, "-m", "shelfbot", "--data", os.path.join(HERE, data)] + list(argv),
        cwd=REPO, env=env, capture_output=True, text=True, timeout=60,
    )
    return proc.returncode, proc.stdout, proc.stderr
