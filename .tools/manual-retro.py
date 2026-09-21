"""Compare the hand-played Moscow turns with the agent's run of the same turns.

The MCP records nothing while a human plays in the game window, but Civ VI's own logs do:
CombatLog.csv (one row per exchange, both sides' damage), UnitOperations.log (the orders given),
DiplomacySummary.csv (City Capture, peace proposals), Player_Stats.csv (cities, army, gold),
Player_WarWeariness.csv. Because those files accumulate across sessions, each run is a *block*
of rows, and a block boundary is where the turn number goes backwards: the agent's run over
T101-T137 is the first block, the hand-played T120-T124 stretch is the last one.

    python .tools/manual-retro.py
"""

from __future__ import annotations

import csv
import os
import pathlib
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

LOGS = pathlib.Path(
    os.path.expandvars(r"%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\Logs")
)
CHINA, RUSSIA = 0, 1  # ids as used by CombatLog.csv / Game_PlayerScores.csv / UnitOperations.log


def read(name: str) -> list[list[str]]:
    path = LOGS / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        return [r for r in csv.reader(fh) if r]


def blocks(rows: list[list[str]]) -> list[list[list[str]]]:
    out: list[list[list[str]]] = []
    cur: list[list[str]] = []
    prev: int | None = None
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


def cell(row: list[str], i: int) -> str:
    """CSV fields come back space-padded, so every comparison has to be stripped."""
    return row[i].strip() if i < len(row) else ""


def num(value: str) -> float:
    try:
        return float(str(value).strip())
    except ValueError:
        return 0.0


def short(unit: str) -> str:
    return unit.replace("UNIT_", "").replace("DISTRICT_", "").replace("CIVILIZATION_", "")


def combat_blocks() -> list[list[list[str]]]:
    return blocks(read("CombatLog.csv")[1:])


def manual_detail() -> None:
    blocks_ = combat_blocks()
    blk = blocks_[-1]
    print("=" * 78)
    print(f"HAND-PLAYED BLOCK  (CombatLog.csv, turns {blk[0][0]}..{blk[-1][0]}, {len(blk)} rows)")
    print("=" * 78)
    for row in blk:
        turn, att, dfd = int(row[0]), int(row[1]), int(row[2])
        ids = row[4] if ":" in row[4] else row[3]
        attacker, defender = short(row[5]), short(row[6])
        dealt, taken = num(row[-1]), num(row[-2])
        side = "OURS  " if att == CHINA else ("THEIRS" if dfd == CHINA else "other ")
        print(
            f"  T{turn:<4} {side} {attacker:<22} -> {defender:<20}"
            f" dealt {dealt:>5.0f} took {taken:>5.0f}   [{ids}]"
        )


def branch_table() -> None:
    blocks_ = combat_blocks()
    agent, manual = blocks_[0], blocks_[-1]

    def by_turn(blk: list[list[str]]) -> dict[int, dict[str, float]]:
        out: dict[int, dict[str, float]] = defaultdict(
            lambda: {"atk": 0, "dealt": 0.0, "taken": 0.0, "city": 0.0, "kills": 0}
        )
        for row in blk:
            turn, att, dfd = int(row[0]), int(row[1]), int(row[2])
            dealt, taken = num(row[-1]), num(row[-2])
            if att == CHINA:
                s = out[turn]
                s["atk"] += 1
                s["dealt"] += dealt
                s["taken"] += taken
                if "UNKNOWN" in row[6] or "CITY_CENTER" in row[6]:
                    s["city"] += dealt
        return out

    a, m = by_turn(agent), by_turn(manual)
    print()
    print("=" * 78)
    print("SAME TURNS, TWO EXECUTIONS  (attacks / damage dealt / damage taken by China)")
    print("=" * 78)
    print(f"  {'T':>4} | {'agent: n':>8} {'dealt':>6} {'taken':>6} {'to city':>7}"
          f" | {'human: n':>8} {'dealt':>6} {'taken':>6} {'to city':>7}")
    for turn in sorted(set(a) | set(m)):
        sa, sm = a.get(turn), m.get(turn)
        def cell(s: dict[str, float] | None, key: str, width: int, fmt: str = "{:.0f}") -> str:
            return f"{fmt.format(s[key]):>{width}}" if s else " " * width
        print(
            f"  {turn:>4} | {cell(sa, 'atk', 8)} {cell(sa, 'dealt', 6)} {cell(sa, 'taken', 6)}"
            f" {cell(sa, 'city', 7)} | {cell(sm, 'atk', 8)} {cell(sm, 'dealt', 6)}"
            f" {cell(sm, 'taken', 6)} {cell(sm, 'city', 7)}"
        )
    for label, s in (("agent", a), ("human", m)):
        attacks = sum(v["atk"] for v in s.values())
        dealt = sum(v["dealt"] for v in s.values())
        taken = sum(v["taken"] for v in s.values())
        active = len([v for v in s.values() if v["atk"]])
        print(
            f"  {label:<6} {attacks:>3} attacks over {active} attack-turns,"
            f" {dealt:>6.0f} damage dealt ({dealt / max(1, active):>5.0f}/turn),"
            f" {taken:>5.0f} taken"
        )


def diplomacy() -> None:
    rows = read("DiplomacySummary.csv")[1:]
    print()
    print("=" * 78)
    print("CITY CAPTURES AND PEACE PROPOSALS (DiplomacySummary.csv, whole file)")
    print("=" * 78)
    for row in rows:
        action = cell(row, 3)
        if action in ("City Capture", "We Made Peace", "Deal Proposed", "Peace"):
            extra = f" - {cell(row, 4)}" if cell(row, 4) else ""
            print(f"  T{cell(row, 0):<4} {cell(row, 1):>3} -> {cell(row, 2):<3} {action}{extra}")


def agent_arc() -> None:
    blk = combat_blocks()[0]
    per_turn: dict[int, dict[str, float]] = defaultdict(
        lambda: {"n": 0, "dealt": 0.0, "taken": 0.0, "city": 0.0}
    )
    for row in blk:
        turn = int(row[0])
        if cell(row, 1) != str(CHINA):
            continue
        s = per_turn[turn]
        s["n"] += 1
        s["dealt"] += num(row[-1])
        s["taken"] += num(row[-2])
        if "UNKNOWN" in cell(row, 6) or "CITY_CENTER" in cell(row, 6):
            s["city"] += num(row[-1])
    print()
    print("=" * 78)
    print(f"THE AGENT'S WHOLE RUN IN THIS LOG (CombatLog.csv first block, {len(blk)} rows)")
    print("=" * 78)
    for turn in sorted(per_turn):
        s = per_turn[turn]
        print(
            f"  T{turn:<4} {s['n']:>2} attacks, dealt {s['dealt']:>5.0f}"
            f" (city {s['city']:>4.0f}), took {s['taken']:>4.0f}"
        )


def orders() -> None:
    rows = read("UnitOperations.log")
    blk = blocks(rows)[-1]
    print()
    print("=" * 78)
    print(f"ORDERS ISSUED BY CHINA IN THE HAND-PLAYED BLOCK (UnitOperations.log, {len(blk)} rows)")
    print("=" * 78)
    per_turn: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in blk:
        if len(row) < 5 or row[2].strip() != str(CHINA):
            continue
        per_turn[int(row[0])][short(row[4]) if len(row) > 4 else "?"] += 1
    for turn in sorted(per_turn):
        kinds = ", ".join(f"{k} x{v}" for k, v in sorted(per_turn[turn].items(), key=lambda kv: -kv[1]))
        print(f"  T{turn}: {kinds}")


def stats() -> None:
    rows = read("Player_Stats.csv")[1:]
    blk = blocks(rows)[-1]
    print()
    print("=" * 78)
    print("CHINA / RUSSIA AT THE END OF EACH BLOCK (Player_Stats.csv)")
    print("=" * 78)
    for label, blkrows in (("agent", blocks(rows)[0][-40:]), ("hand", blk[-40:])):
        print(f"  {label}:")
        for row in blkrows:
            if cell(row, 1) in ("CIVILIZATION_CHINA", "CIVILIZATION_RUSSIA"):
                print(
                    f"    T{cell(row, 0):<4} {short(cell(row, 1)):<8} cities {num(cell(row, 2)):>2.0f}"
                    f" pop {num(cell(row, 3)):>3.0f} land units {num(cell(row, 5)):>2.0f}"
                    f" gold {num(cell(row, 12)):>4.0f} science {num(cell(row, 14)):>4.0f}"
                )


def war_weariness() -> None:
    rows = read("Player_WarWeariness.csv")[1:]
    ours = [r for r in rows if r and r[0].strip() == str(CHINA) and len(r) > 3]
    print()
    print("=== China's war weariness, last 6 records (Player_WarWeariness.csv) ===")
    for row in ours[-6:]:
        print(f"  vs player {row[1]:<3} delta {row[2]:>6} total {row[3]:>6} ({row[4]})")


def main() -> int:
    manual_detail()
    branch_table()
    agent_arc()
    diplomacy()
    orders()
    stats()
    war_weariness()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
