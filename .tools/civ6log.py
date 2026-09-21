"""Read the Civilization VI game's own logs - the only witness to hand-played turns.

The MCP records nothing while a human plays in the game window, but Civ VI writes its own
telemetry to `%LOCALAPPDATA%\\Firaxis Games\\Sid Meier's Civilization VI\\Logs`. CombatLog.csv
has one row per exchange with both sides' damage; the AI/Player CSVs and Lua.log carry the
rest. These files accumulate across sessions, so a hand-played stretch shows up as a *new
block* near the end of a file whose turn numbers go backwards.

    python .tools/civ6log.py list
    python .tools/civ6log.py head CombatLog.csv
    python .tools/civ6log.py combat --from 118 --to 126
    python .tools/civ6log.py runs CombatLog.csv
    python .tools/civ6log.py grep "capture" --file Lua.log --since 08:40
"""

from __future__ import annotations

import argparse
import csv
import os
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LOGS = pathlib.Path(
    os.path.expandvars(r"%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\Logs")
)


def rows_of(name: str) -> list[list[str]]:
    path = LOGS / name
    if not path.exists():
        print(f"missing: {path}")
        return []
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        return [r for r in csv.reader(fh) if r]


def turn_of(row: list[str]) -> int | None:
    return int(row[0]) if row and row[0].strip().isdigit() else None


def runs(name: str) -> list[tuple[int, int, int]]:
    """Contiguous (start_row, end_row, last_turn) blocks: a decreasing turn starts a new one."""
    data = rows_of(name)[1:]
    out: list[tuple[int, int, int]] = []
    start = 0
    prev: int | None = None
    for i, row in enumerate(data):
        turn = turn_of(row)
        if prev is not None and turn is not None and turn < prev:
            out.append((start, i - 1, prev))
            start = i
        if turn is not None:
            prev = turn
    if data:
        out.append((start, len(data) - 1, prev or 0))
    return out


def cmd_list(_: argparse.Namespace) -> int:
    files = sorted(LOGS.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files[:40]:
        import datetime

        stamp = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M:%S")
        print(f"{stamp}  {path.stat().st_size:>10,}  {path.name}")
    return 0


def cmd_head(args: argparse.Namespace) -> int:
    rows = rows_of(args.file)
    for row in rows[: args.lines]:
        print(" | ".join(row[:20]))
    print(f"... {len(rows)} rows total")
    return 0


def cmd_runs(args: argparse.Namespace) -> int:
    for a, b, last in runs(args.file):
        rows = rows_of(args.file)[1:]
        first = rows[a][0] if a < len(rows) else "?"
        print(f"rows {a:>5}..{b:<5} turns {first:>4}..{last:<4} ({b - a + 1} rows)")
    return 0


def cmd_combat(args: argparse.Namespace) -> int:
    data = rows_of("CombatLog.csv")
    if not data:
        return 1
    header = data[0]
    print(" | ".join(header))
    n = 0
    for row in data[1:]:
        turn = turn_of(row)
        if turn is None or not (args.start <= turn <= args.end):
            continue
        # The tail rows of this file drop the two ID columns, so print positionally with the
        # raw width shown - the last two numbers are the damage dealt each way.
        print(f"T{turn:<4} " + " | ".join(row[1:]))
        n += 1
    print(f"{n} rows with turn {args.start}..{args.end}")
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    rows = rows_of(args.file)
    for row in rows[-args.lines :]:
        print(" | ".join(row[: args.cols]))
    print(f"... {len(rows)} rows total")
    return 0


def cmd_grep(args: argparse.Namespace) -> int:
    path = LOGS / args.file
    if not path.exists():
        print(f"missing: {path}")
        return 1
    pat = re.compile(args.pattern, re.I)
    shown = 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if args.since and args.since not in line[:40]:
                continue
            if not pat.search(line):
                continue
            print(line.rstrip()[: args.width])
            shown += 1
            if shown >= args.limit:
                print(f"... stopped at {args.limit} matches")
                break
    print(f"{shown} matches for {args.pattern!r} in {args.file}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    p = sub.add_parser("head")
    p.add_argument("file")
    p.add_argument("--lines", type=int, default=5)
    p.set_defaults(func=cmd_head)

    p = sub.add_parser("runs")
    p.add_argument("file")
    p.set_defaults(func=cmd_runs)

    p = sub.add_parser("tail")
    p.add_argument("file")
    p.add_argument("--lines", type=int, default=20)
    p.add_argument("--cols", type=int, default=20)
    p.set_defaults(func=cmd_tail)

    p = sub.add_parser("combat")
    p.add_argument("--from", dest="start", type=int, default=1)
    p.add_argument("--to", dest="end", type=int, default=9999)
    p.set_defaults(func=cmd_combat)

    p = sub.add_parser("grep")
    p.add_argument("pattern")
    p.add_argument("--file", default="Lua.log")
    p.add_argument("--since", default=None)
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--width", type=int, default=220)
    p.set_defaults(func=cmd_grep)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
