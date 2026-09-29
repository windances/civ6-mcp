#!/usr/bin/env python3
"""Extract one military-production attempt's numbers from the raw record.

An *attempt* is one played match.  Its raw record is two files the loop already writes:

    .civ6-mcp-data/diary_<game>.jsonl   one snapshot row per player per turn (the economy)
    .civ6-mcp-data/log_<game>_*.jsonl   one row per tool call, with the tool's own reply text
                                        (the rules that failed, the orders that were refused,
                                        the city that was taken)

Nothing here is new instrumentation: the point is that the two files already hold every number an
attempt is judged on, and this turns them into the same table every time, so two attempts can be
compared without re-deriving anything by hand.

    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_-1894041591
    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_-1894041591 --step 10 --json
    .venv\\Scripts\\python.exe scripts/experiment-report.py --list

Reported, per attempt:

  * the 10-turn economy table (science/culture/gold/pop/districts/wonders/improvements/...)
  * the military table - unit composition at each boundary, so the establishment's growth is visible
  * the capture line - which turn a city was kept, from the tool reply, not from the prose
  * the rule table - `CHECK FAILED [id]` counts, i.e. which doctrine rules the attempt violated
  * the refusal table - STOPPED_MID_PATH and friends, i.e. what the orders cost
  * the process table - tool calls per turn (the attempt's own cost)
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / ".civ6-mcp-data"

# The economy columns, in the order they are worth reading.  Every one of them is a field the diary
# already stores per turn (see civ_mcp.diary); the list is short on purpose.
ECONOMY = (
    "science",
    "culture",
    "gold",
    "gold_per_turn",
    "faith",
    "military",
    "pop",
    "cities",
    "districts",
    "wonders",
    "improvements",
    "territory",
    "techs_completed",
    "civics_completed",
    "tourism",
    "era_score",
)

REFUSALS = (
    "STOPPED_MID_PATH",
    "STOPPED_SHORT",
    "BLOCKED",
    "NO_MOVES",
    "ZOC",
    "TOO FAR",
    "NO_LOS",
    "ERR:",
)

CAPTURE_RE = re.compile(r"\b(KEEP|RAZE|LIBERATE_FOUNDER|LIBERATE_PREVIOUS)\|", re.I)
RULE_RE = re.compile(r"CHECK FAILED \[([a-z0-9\-]+)\]")
ACHIEVED_RE = re.compile(r"CHECK ACHIEVED[^\n]*?\[([a-z0-9\-]+)\]")


# --------------------------------------------------------------------------- raw record


def games() -> list[str]:
    """Every game key that has a diary, newest first."""
    out = []
    for path in DATA.glob("diary_*.jsonl"):
        key = path.stem[len("diary_") :]
        out.append((path.stat().st_mtime, key))
    return [key for _, key in sorted(out, reverse=True)]


def diary_rows(game: str) -> dict[int, dict]:
    """The agent's own rows, keyed by turn (last write per turn wins)."""
    path = DATA / f"diary_{game}.jsonl"
    by_turn: dict[int, dict] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not row.get("is_agent"):
                continue
            turn = row.get("turn")
            if isinstance(turn, int):
                by_turn[turn] = row
    return by_turn


def log_rows(game: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(DATA.glob(f"log_{game}_*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    rows.sort(key=lambda r: r.get("ts") or 0)
    return rows


# --------------------------------------------------------------------------- tables


def _first_turn(by_turn: dict[int, dict]) -> int:
    return min(by_turn) if by_turn else 1


def _last_turn(by_turn: dict[int, dict]) -> int:
    return max(by_turn) if by_turn else 1


def boundaries(by_turn: dict[int, dict], step: int) -> list[int]:
    """The turns to print: the first turn, then every multiple of `step`, then the last turn."""
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    turns = [first]
    turns += [t for t in range(((first // step) + 1) * step, last + 1, step)]
    if last not in turns:
        turns.append(last)
    return sorted(set(turns))


def economy_table(by_turn: dict[int, dict], step: int) -> list[dict]:
    rows = []
    for turn in boundaries(by_turn, step):
        row = by_turn[turn]
        entry = {"turn": turn}
        for key in ECONOMY:
            entry[key] = row.get(key)
        entry["units_total"] = row.get("units_total")
        entry["trade"] = row.get("trade_routes")
        entry["exploration_pct"] = row.get("exploration_pct")
        rows.append(entry)
    return rows


def deltas(by_turn: dict[int, dict]) -> dict[str, object]:
    """Total and per-turn change between the first and last turn of the attempt."""
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    a, b = by_turn[first], by_turn[last]
    span = max(1, last - first)
    total: dict[str, float] = {}
    per_turn: dict[str, float] = {}
    for key in ECONOMY:
        try:
            delta = float(b.get(key) or 0) - float(a.get(key) or 0)
        except (TypeError, ValueError):
            continue
        total[key] = round(delta, 2)
        per_turn[key] = round(delta / span, 3)
    return {"span": span, "total": total, "per_turn": per_turn}


def composition(by_turn: dict[int, dict], step: int) -> list[tuple[int, dict]]:
    rows = []
    for turn in boundaries(by_turn, step):
        comp = by_turn[turn].get("unit_composition") or {}
        rows.append((turn, comp))
    return rows


def rule_counts(rows: list[dict]) -> tuple[collections.Counter, list[tuple[int, str]]]:
    counts: collections.Counter = collections.Counter()
    achieved: list[tuple[int, str]] = []
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for rule in RULE_RE.findall(blob):
            counts[rule] += 1
        for rule in ACHIEVED_RE.findall(blob):
            achieved.append((row.get("turn") or 0, rule))
    return counts, achieved


def refusal_counts(rows: list[dict]) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for name in REFUSALS:
            n = blob.count(name)
            if n:
                counts[name] += n
    return counts


def captures(rows: list[dict]) -> list[tuple[int, str]]:
    """City keeps/razes, deduplicated - the same reply appears in both `result` and its summary."""
    seen: set[tuple[int, str]] = set()
    out: list[tuple[int, str]] = []
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for match in CAPTURE_RE.finditer(blob):
            snippet = blob[match.start() : match.end() + 40]
            key = (row.get("turn") or 0, snippet[:28])
            if key in seen:
                continue
            seen.add(key)
            out.append((row.get("turn") or 0, snippet))
    return out


def tool_calls(rows: list[dict]) -> collections.Counter:
    return collections.Counter(row.get("tool") for row in rows)


# --------------------------------------------------------------------------- printing


def print_text(game: str, step: int, by_turn: dict[int, dict], rows: list[dict]) -> None:
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    print(f"== attempt {game}: T{first} -> T{last} ==")
    civ = by_turn[first].get("civ")
    print(f"civ: {civ}  era: {by_turn[last].get('era')}  government: {by_turn[last].get('government')}")

    print("\n-- economy --")
    header = ["turn"] + list(ECONOMY[:8]) + ["districts", "wonders", "improvements"]
    print("  ".join(f"{h:>11s}" for h in header))
    for entry in economy_table(by_turn, step):
        cells = [f"{entry['turn']:>11d}"]
        for key in header[1:]:
            value = entry.get(key)
            cells.append(f"{value:>11}" if value is not None else f"{'-':>11}")
        print("  ".join(cells))

    delta = deltas(by_turn)
    print("\n-- window delta (whole attempt) --")
    print(f"  span: {delta['span']} turns")
    for key, value in delta["total"].items():  # type: ignore[union-attr]
        rate = delta["per_turn"][key]  # type: ignore[index]
        print(f"  {key:>18s}: {value:+9.2f}   ({rate:+.3f}/turn)")

    print("\n-- military composition --")
    for turn, comp in composition(by_turn, step):
        if not comp:
            print(f"  T{turn:<4} (none)")
            continue
        body = ", ".join(f"{name}:{n}" for name, n in sorted(comp.items(), key=lambda kv: -kv[1]))
        print(f"  T{turn:<4} {body}")

    counts, achieved = rule_counts(rows)
    print("\n-- rules (CHECK FAILED counts) --")
    if counts:
        for rule, n in counts.most_common():
            print(f"  {n:>4d}  {rule}")
    else:
        print("  (no failures recorded)")
    if achieved:
        print("  achieved:")
        for turn, rule in achieved:
            print(f"  T{turn:<4} {rule}")

    refusals = refusal_counts(rows)
    print("\n-- refusals --")
    for name, n in refusals.most_common():
        print(f"  {n:>4d}  {name}")

    cap = captures(rows)
    print("\n-- captures --")
    if cap:
        for turn, text in cap:
            print(f"  T{turn:<4} {text.strip()}")
    else:
        print("  (no city captured or kept)")

    calls = tool_calls(rows)
    total = sum(calls.values())
    print("\n-- process --")
    print(f"  tool calls: {total} over {last - first + 1} turns = {total / max(1, last - first + 1):.1f}/turn")
    print("  most used: " + ", ".join(f"{t}:{n}" for t, n in calls.most_common(8)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", help="game key, e.g. china_-1894041591")
    ap.add_argument("--step", type=int, default=10, help="turn step for the tables (default 10)")
    ap.add_argument("--from", dest="start", type=int, help="first turn to report (inclusive)")
    ap.add_argument("--to", dest="end", type=int, help="last turn to report (inclusive)")
    ap.add_argument("--json", action="store_true", help="emit the tables as JSON")
    ap.add_argument("--list", action="store_true", help="list the game keys that have a diary")
    args = ap.parse_args()

    if args.list or not args.game:
        for key in games():
            by_turn = diary_rows(key)
            print(f"{key}  T{_first_turn(by_turn)} -> T{_last_turn(by_turn)}  ({len(by_turn)} turns)")
        return 0

    sys.stdout.reconfigure(encoding="utf-8")
    by_turn = diary_rows(args.game)
    if not by_turn:
        print(f"no diary rows for {args.game}", file=sys.stderr)
        return 2
    rows = log_rows(args.game)
    if args.start is not None:
        by_turn = {t: r for t, r in by_turn.items() if t >= args.start}
        rows = [r for r in rows if (r.get("turn") or 0) >= args.start]
    if args.end is not None:
        by_turn = {t: r for t, r in by_turn.items() if t <= args.end}
        rows = [r for r in rows if (r.get("turn") or 0) <= args.end]
    if not by_turn:
        print("no diary rows in that turn range", file=sys.stderr)
        return 2

    if args.json:
        counts, achieved = rule_counts(rows)
        payload = {
            "game": args.game,
            "first_turn": _first_turn(by_turn),
            "last_turn": _last_turn(by_turn),
            "economy": economy_table(by_turn, args.step),
            "delta": deltas(by_turn),
            "composition": [{"turn": t, "units": c} for t, c in composition(by_turn, args.step)],
            "rules": dict(counts),
            "achieved": achieved,
            "refusals": dict(refusal_counts(rows)),
            "captures": captures(rows),
            "tool_calls": dict(tool_calls(rows)),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print_text(args.game, args.step, by_turn, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
