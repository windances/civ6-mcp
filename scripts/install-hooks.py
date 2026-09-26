"""Install this repository's git hooks: the mandatory text-integrity gate before every commit.

    python scripts/install-hooks.py            # install (idempotent), and check the hook runs
    python scripts/install-hooks.py --revert   # put core.hooksPath back to the default

The hook itself is `.githooks/pre-commit`, which runs `scripts/fix-text-encoding.py --check`: a
document without a BOM, or a file whose characters are the leavings of a GBK round trip, blocks the
commit. That check is the one thing that would have caught the 2026-09-26 corruption (278 characters
in five files, valid UTF-8, every BOM in place, 843 tests green) before it landed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".githooks"
HOOK = HOOKS / "pre-commit"
CHECK = ROOT / "scripts" / "fix-text-encoding.py"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the git hooks that gate on text integrity.")
    parser.add_argument("--revert", action="store_true", help="restore the default hooks path")
    args = parser.parse_args()

    if not HOOK.is_file():
        print(f"missing {HOOK.relative_to(ROOT)} - the hook is tracked, so this checkout is incomplete")
        return 1
    if not CHECK.is_file():
        print(f"missing {CHECK.relative_to(ROOT)} - the hook has nothing to run")
        return 1

    if args.revert:
        result = git("config", "--unset", "core.hooksPath")
        print("core.hooksPath unset" if result.returncode == 0 else "core.hooksPath was not set")
        return 0

    result = git("config", "core.hooksPath", ".githooks")
    if result.returncode != 0:
        print(f"git config failed: {result.stderr.strip()}")
        return 1
    print(f"core.hooksPath = .githooks ({HOOK.relative_to(ROOT)} runs on every commit)")

    # Prove the gate runs and currently passes, without writing anything.
    check = subprocess.run([sys.executable, str(CHECK), "--check"], cwd=ROOT, capture_output=True, text=True)
    for line in (check.stdout + check.stderr).splitlines():
        print(f"  {line}")
    if check.returncode != 0:
        print("the gate is installed and the tree does NOT pass it - repair before committing")
        return 1
    print("the tree passes the gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
