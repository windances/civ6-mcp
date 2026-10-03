"""Separate the tools that run again from the scripts that answered one question once.

`.tools/` accumulated 367 top-level files, and the two kinds are indistinguishable at a glance: a
live tool (`turn-verify.py`, `production-audit.py`) and a one-off written for one turn of one match
(`t103.py`, `_amenity_probe.py`) sit side by side with the same extension. That is how a directory
whose whole purpose is "the things I run" stops being readable, and it is why the guard test needs
an explicit list of live tools rather than a directory scan.

The rule here is deliberately conservative: a file moves only when it matches a **dead pattern** and
is **not** on the live list. Anything ambiguous stays where it is, because moving a live tool is
worse than leaving a dead one.

    python .tools/archive-one-offs.py            # dry run: what would move
    python .tools/archive-one-offs.py --go       # move them to .tools/archive/
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil

TOOLS = pathlib.Path(__file__).resolve().parent
ARCHIVE = TOOLS / "archive"

# Tools that take live game input or are otherwise run again. Kept by name, not by pattern: the
# point of the exercise is that a pattern cannot tell the two kinds apart.
LIVE = {
    "_game.py",
    "advance-turns.py",
    "production-audit.py",
    "production-recovery.py",
    "turn-verify.py",
    "target-recon.py",
    "archive-branch.py",
    "check-paths.py",
    "compare-branches.py",
    "dev-curve.py",
    "goal-status.py",
    "kabul-map.py",
    "kabul-state.py",
    "show-check-prune.py",
    "siege-facts.py",
    "orient.py",
    "state.py",
    "load-save.py",
    "whats-on-screen.py",
    "click-text.py",
    "click-continue.py",
    "prewar.py",
    "live-lua.py",
    "recover.py",
    "drive-load.py",
    "enter-game.py",
    "new-run.py",
    "grab-screen.py",
    "kb.py",
    "list-saves.py",
}

# A file matching any of these, and not in LIVE, is one-off. `_` and `t<turn>` are this repo's own
# conventions for scratch and turn-specific work; the rest are outputs rather than scripts.
DEAD_PATTERNS = (
    re.compile(r"^_"),
    re.compile(r"^t\d"),
    re.compile(r"^commit-msg-\d+\.txt$"),
    re.compile(r"\.(txt|log|png|csv)$"),
)


def is_one_off(name: str) -> bool:
    if name in LIVE:
        return False
    return any(pattern.search(name) for pattern in DEAD_PATTERNS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="actually move them")
    ap.add_argument("--json-dumps", action="store_true",
                    help="also move bare .json outputs not already covered by the patterns")
    args = ap.parse_args()

    files = [p for p in TOOLS.iterdir() if p.is_file()]
    moves = [p for p in files if is_one_off(p.name)]
    if args.json_dumps:
        moves += [
            p for p in files
            if p.suffix == ".json" and not is_one_off(p.name) and p not in moves
        ]
    stay = [p for p in files if p not in moves]

    print(f"top-level files : {len(files)}")
    print(f"one-offs to move: {len(moves)}")
    print(f"kept at top     : {len(stay)}")
    by_suffix: dict[str, int] = {}
    for p in moves:
        by_suffix[p.suffix or "(none)"] = by_suffix.get(p.suffix or "(none)", 0) + 1
    print("  moving by type: " + ", ".join(f"{k} x{v}" for k, v in sorted(by_suffix.items())))
    print("  sample        : " + ", ".join(p.name for p in sorted(moves)[:10]))
    print("  kept (live)   : " + ", ".join(sorted(p.name for p in stay)[:14]))

    if not args.go:
        print("\ndry run - re-run with --go to move them")
        return 0

    ARCHIVE.mkdir(exist_ok=True)
    moved = 0
    for path in moves:
        target = ARCHIVE / path.name
        if target.exists():
            target = ARCHIVE / f"{path.stem}.dup{path.suffix}"
        shutil.move(str(path), str(target))
        moved += 1
    print(f"\nmoved {moved} file(s) to {ARCHIVE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
