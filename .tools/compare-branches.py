from _game import require_game, require_game_pair, current_game_key
"""Compare the live branch against the archived (abandoned) branch, turn by turn.

After the rollback to T59, the abandoned branch's diary rows live in
.civ6-mcp-data/branches/abandoned-T60-T174/. The live diary restarts at T60 and
grows as the replay proceeds. Once the replay reaches a turn the archive also
covers, this prints them side by side.

Usage:
    .venv\\Scripts\\python.exe .tools\\compare-branches.py            # all overlaps
    .venv\\Scripts\\python.exe .tools\\compare-branches.py --at 90    # one turn
    .venv\\Scripts\\python.exe .tools\\compare-branches.py --milestones
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".civ6-mcp-data"
GAME = require_game()
ARCHIVE = DATA / "branches" / "abandoned-T60-T174"
LIVE_DIARY = DATA / f"diary_{GAME}.jsonl"
LIVE_CITIES = DATA / f"diary_{GAME}_cities.jsonl"


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def agent_rows(rows: list[dict]) -> dict[int, dict]:
    """Last agent row per turn (the log can repeat a turn)."""
    out: dict[int, dict] = {}
    for r in rows:
        if "v" in r and not r.get("is_agent"):
            continue
        out[int(r.get("turn") or 0)] = r
    return out


def my_city_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("pid") == 0]


METRICS = [
    ("cities", "城"),
    ("pop", "人口"),
    ("science", "科技"),
    ("culture", "文化"),
    ("gold", "金币"),
    ("military", "军力"),
    ("districts", "区域"),
    ("improvements", "改良"),
    ("wonders", "奇观"),
    ("territory", "领土"),
    ("techs_completed", "科技数"),
    ("civics_completed", "市政数"),
    ("era_score", "时代分"),
]


def find_archive() -> Path | None:
    if ARCHIVE.exists():
        return ARCHIVE
    parent = DATA / "branches"
    if not parent.exists():
        return None
    dirs = sorted(p for p in parent.iterdir() if p.is_dir())
    return dirs[-1] if dirs else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", type=int, help="show one turn in detail")
    ap.add_argument("--milestones", action="store_true", help="first-appearance comparison")
    args = ap.parse_args()

    arch = find_archive()
    if arch is None:
        print("no archive found under .civ6-mcp-data/branches/")
        return 1

    fut_files = sorted(arch.glob("diary_future_*.jsonl"))
    fut_city_files = sorted(arch.glob("diary_cities_future_*.jsonl"))
    if not fut_files:
        print(f"no diary_future_*.jsonl in {arch}")
        return 1

    old = agent_rows(load(fut_files[0]))
    new_all = load(LIVE_DIARY)
    new = agent_rows(new_all)
    old_cities = my_city_rows(load(fut_city_files[0])) if fut_city_files else []
    new_cities = my_city_rows(load(LIVE_CITIES))

    overlaps = sorted(set(old) & set(new))
    print(f"archive          {arch.relative_to(ROOT)}")
    print(f"abandoned branch {len(old)} turns (T{min(old)}..T{max(old)})" if old else "abandoned branch empty")
    print(f"live branch      {len(new)} turns (T{min(new)}..T{max(new)})" if new else "live branch empty")
    print(f"overlapping turns: {len(overlaps)}" + (f"  ({overlaps[0]}..{overlaps[-1]})" if overlaps else ""))

    if args.milestones:
        # The archive starts at the cut, so anything that already existed before it
        # shows its first appearance as the cut turn. Say "<=T60" rather than "T60"
        # so a pre-existing Chapel does not read as newly built.
        cut = min(old) if old else None

        def fmt(v, censored=False):
            if v is None:
                return "-"
            return f"<=T{cut}" if (censored and cut is not None and v <= cut) else f"T{v}"

        out_lines = ["=== first turn each item appears (abandoned -> live) ==="]
        out_lines.append(f"archive covers T{cut}.. ; live covers T{min(new)}..T{max(new)}")
        want_districts = [
            "CAMPUS", "COMMERCIAL_HUB", "HOLY_SITE", "ENCAMPMENT", "GOVERNMENT",
            "THEATER", "INDUSTRIAL_ZONE", "AQUEDUCT", "HARBOR",
        ]
        want_items = [
            "BUILDING_LIBRARY", "BUILDING_MARKET", "BUILDING_GRANARY", "BUILDING_UNIVERSITY",
            "UNIT_TREBUCHET", "UNIT_CATAPULT", "UNIT_BATTERING_RAM", "UNIT_SIEGE_TOWER",
            "UNIT_CHINESE_CROUCHING_TIGER", "UNIT_CROSSBOWMAN", "UNIT_MUSKETMAN",
            "UNIT_BOMBARD",
        ]

        def first_district(rows, needle):
            for r in sorted(rows, key=lambda r: r["turn"]):
                if needle in str(r.get("districts") or ""):
                    return r["turn"]
            return None

        def first_produced(rows, needle):
            for r in sorted(rows, key=lambda r: r["turn"]):
                if str(r.get("producing") or "") == needle:
                    return r["turn"]
            return None

        def first_wonder(rows):
            for t in sorted(rows):
                if (rows[t].get("wonders") or 0) > 0:
                    return t
            return None

        out_lines.append("")
        out_lines.append(f"{'item':<32} {'abandoned':>10}  {'live':>10}")
        for d in want_districts:
            out_lines.append(
                f"district {d:<23} {fmt(first_district(old_cities, d), True):>10}  "
                f"{fmt(first_district(new_cities, d)):>10}"
            )
        for i in want_items:
            out_lines.append(
                f"build    {i:<23} {fmt(first_produced(old_cities, i), True):>10}  "
                f"{fmt(first_produced(new_cities, i)):>10}"
            )
        out_lines.append(
            f"wonder   {'(first any)':<23} {fmt(first_wonder(old), True):>10}  "
            f"{fmt(first_wonder(new)):>10}"
        )

        def first_city(rows):
            seen = {}
            for r in sorted(rows, key=lambda r: r["turn"]):
                seen.setdefault(r.get("city"), r["turn"])
            return seen

        oc, nc = first_city(old_cities), first_city(new_cities)
        out_lines.append("")
        out_lines.append(f"{'city founded':<32} {'abandoned':>10}  {'live':>10}")
        for city in sorted(set(oc) | set(nc), key=lambda c: (oc.get(c) or nc.get(c) or 0)):
            if str(city).startswith("LOC_"):
                continue
            out_lines.append(
                f"{str(city):<32} {fmt(oc.get(city), True):>10}  {fmt(nc.get(city)):>10}"
            )
        report = "\n".join(out_lines)
        # The Windows console is cp936 here and mangles both CJK and the em dash,
        # so the readable copy goes to a UTF-8 file and stdout stays ASCII.
        out_path = ROOT / ".tools" / "_branch_compare.txt"
        out_path.write_text(report, encoding="utf-8")
        print(f"wrote {out_path.relative_to(ROOT)} (UTF-8; read it there for the CJK names)")
        print(report.encode("ascii", "replace").decode("ascii"))
        return 0

    if not overlaps:
        print("\nno overlapping turns yet - the replay has not reached T"
              f"{min(old) if old else '?'}.")
        print("re-run this once the live branch passes that turn.")
        return 0

    turns = [args.at] if args.at else overlaps
    print(f"\n{'T':>4}  {'metric':<10} {'abandoned':>12} {'live':>12} {'delta':>10}")
    for t in turns:
        if t not in old or t not in new:
            print(f"\nT{t}: not in both branches")
            continue
        print()
        for key, label in METRICS:
            a, b = old[t].get(key), new[t].get(key)
            try:
                d = f"{b - a:+g}"
            except (TypeError, ValueError):
                d = ""
            print(f"{t:>4}  {label:<10} {str(a):>12} {str(b):>12} {d:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
