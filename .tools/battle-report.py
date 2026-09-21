"""Report one run's battle from the game's own logs: who hit whom, for how much, and the outcome.

Used for a stretch played in the game window, where the MCP has no telemetry at all. The blocks
are separated by a turn number that goes backwards (these files accumulate across sessions), and
`--china` picks the player id that is us.

    python .tools/battle-report.py                # every block, China (id 0) only
    python .tools/battle-report.py --civ 0
"""

from __future__ import annotations

import argparse
import csv
import os
import pathlib
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

LOGS = pathlib.Path(
    os.path.expandvars(r"%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\Logs")
)
MOSCOW_IDS = {"327683", "327681", "65536", "131072", "524294", "262146"}


def read(name: str) -> list[list[str]]:
    path = LOGS / name
    if not path.exists():
        print(f"missing: {path}")
        return []
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        return [r for r in csv.reader(fh) if r]


def cell(row: list[str], i: int) -> str:
    return row[i].strip() if i < len(row) else ""


def num(value: str) -> float:
    try:
        return float(str(value).strip())
    except ValueError:
        return 0.0


def blocks(rows: list[list[str]]) -> list[list[list[str]]]:
    out, cur, prev = [], [], None
    for row in rows:
        turn = int(row[0]) if row and row[0].strip().isdigit() else None
        if turn is None:
            continue
        if prev is not None and turn < prev:
            out.append(cur)
            cur = []
        cur.append(row)
        prev = turn
    if cur:
        out.append(cur)
    return out


def combat(civ: int) -> None:
    data = read("CombatLog.csv")
    if not data:
        return
    for bi, blk in enumerate(blocks(data[1:])):
        out: dict[int, dict[str, float]] = defaultdict(
            lambda: {"n": 0, "dealt": 0.0, "taken": 0.0, "city": 0.0}
        )
        incoming: dict[int, dict[str, float]] = defaultdict(lambda: {"n": 0, "dmg": 0.0})
        targets: dict[str, int] = defaultdict(int)
        for row in blk:
            turn, att, dfd = int(row[0]), int(row[1]), int(row[2])
            dealt, taken = num(cell(row, -1)), num(cell(row, -2))
            if att == civ:
                s = out[turn]
                s["n"] += 1
                s["dealt"] += dealt
                s["taken"] += taken
                if "UNKNOWN" in cell(row, 6) or "CITY_CENTER" in cell(row, 6):
                    s["city"] += dealt
                targets[cell(row, 4)] += 1
            if dfd == civ:
                incoming[turn]["n"] += 1
                incoming[turn]["dmg"] += dealt
        print(f"\n=== CombatLog block {bi + 1}: turns {blk[0][0]}..{blk[-1][0]} ({len(blk)} rows) ===")
        print(f"  {'T':>4} {'our atk':>7} {'dealt':>6} {'to city':>7} {'we took':>7} | {'hits on us':>10} {'damage':>7}")
        for turn in sorted(set(out) | set(incoming)):
            s = out.get(turn, {"n": 0, "dealt": 0, "taken": 0, "city": 0})
            i = incoming.get(turn, {"n": 0, "dmg": 0})
            print(
                f"  {turn:>4} {s['n']:>7.0f} {s['dealt']:>6.0f} {s['city']:>7.0f} {s['taken']:>7.0f} |"
                f" {i['n']:>10.0f} {i['dmg']:>7.0f}"
            )
        n = sum(v["n"] for v in out.values())
        dealt = sum(v["dealt"] for v in out.values())
        taken = sum(v["taken"] for v in out.values())
        turns = len([t for t, v in out.items() if v["n"]])
        print(
            f"  total: {n:.0f} attacks over {turns} attack-turns, {dealt:.0f} dealt"
            f" ({dealt / max(1, turns):.0f}/turn), {taken:.0f} taken from retaliation;"
            f" {sum(v['dmg'] for v in incoming.values()):.0f} taken from all sources"
        )
        if targets:
            print("  targets (defender object ids, hit count):", dict(sorted(targets.items())))


def stats(civ_names: tuple[str, ...], turns: tuple[int, int]) -> None:
    rows = read("Player_Stats.csv")[1:]
    print("\n=== Player_Stats ===")
    print(f"  {'T':>4} {'civ':<16} {'cities':>6} {'pop':>4} {'land':>4} {'gold':>5} {'sci':>4} {'cul':>4}")
    for row in rows:
        turn = int(cell(row, 0)) if cell(row, 0).isdigit() else 0
        if not (turns[0] <= turn <= turns[1]):
            continue
        name = cell(row, 1).replace("CIVILIZATION_", "")
        if name not in civ_names:
            continue
        print(
            f"  {turn:>4} {name:<16} {num(cell(row, 2)):>6.0f} {num(cell(row, 3)):>4.0f}"
            f" {num(cell(row, 5)):>4.0f} {num(cell(row, 12)):>5.0f} {num(cell(row, 14)):>4.0f}"
            f" {num(cell(row, 15)):>4.0f}"
        )


def diplomacy() -> None:
    rows = read("DiplomacySummary.csv")[1:]
    print("\n=== DiplomacySummary: captures, peace, wars ===")
    for row in rows:
        action = cell(row, 3)
        if action in ("City Capture", "We Made Peace", "Peace", "City Revolt", "War Declared"):
            print(f"  T{cell(row, 0):<4} {cell(row, 1):>3} -> {cell(row, 2):<3} {action}  {cell(row, 4)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--civ", type=int, default=0, help="our player id in the logs (default 0 = China)")
    ap.add_argument("--from", dest="start", type=int, default=1)
    ap.add_argument("--to", dest="end", type=int, default=9999)
    args = ap.parse_args()
    combat(args.civ)
    stats(("CHINA", "RUSSIA"), (args.start, args.end))
    diplomacy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
