"""Replay the current rule set against the abandoned siege line (T101-T116), from records only.

The Moscow assault that ran T105-T116 was rolled back to T100, so its telemetry is the only
witness. This reads that telemetry - the archived diary rows for T101-T116 and the session log
of the same turns - rebuilds what each turn looked like, and evaluates `prompts/checks/
turn-checks.md` against it. What it produces is a counterfactual: which of today's rules would
have fired on which turns, and which of the mistakes nobody would have caught.

    .venv\\Scripts\\python.exe .tools\\siege-retro.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402

DATA = pathlib.Path(".civ6-mcp-data")
BRANCH = DATA / "branches" / "abandoned-T101-T116"
LOG = DATA / "log_china_-1894041591_stoic-amber-vineyard-98.jsonl"
CHECKS = pathlib.Path("prompts/checks/turn-checks.md")


def load_rows(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip()
    ]


def turn_of(row: dict) -> int:
    value = row.get("turn")
    return int(value) if isinstance(value, str) and value.isdigit() else (value or 0)


def main() -> int:
    diary = load_rows(BRANCH / "diary_future_T101_T116.jsonl")
    agent = {r["turn"]: r for r in diary if r.get("is_agent") and isinstance(r.get("turn"), int)}
    log = load_rows(LOG)

    # Per-turn facts recovered from the log.
    attacks: dict[int, list[dict]] = {}
    damaged: dict[int, list[str]] = {}
    hints: dict[int, int] = {}
    orders: dict[int, int] = {}
    for row in log:
        turn = turn_of(row)
        if not isinstance(turn, int) or turn < 101:
            continue
        res = str(row.get("result") or "")
        if row.get("tool") == "unit_action":
            params = row.get("params") or {}
            if params.get("action") == "attack":
                distance = re.search(r"range:(\d+) dist:(\d+)", res)
                attacks.setdefault(turn, []).append(
                    {
                        "unit": params.get("unit_id"),
                        "x": params.get("target_x"),
                        "y": params.get("target_y"),
                        "error": (re.search(r"Error: ([A-Z_]+)", res) or [None, ""])[1]
                        if "Error:" in res
                        else "",
                        "dealt": int((re.search(r"est damage dealt:~(\d+)", res) or [0, 0])[1])
                        if "est damage dealt" in res
                        else 0,
                        "into_city": "Target tile is a city" in res,
                        "dist": int(distance.group(2)) if distance else None,
                    }
                )
            elif params.get("unit_id"):
                orders[turn] = orders.get(turn, 0) + 1
        if row.get("tool") == "get_units":
            hints[turn] = hints.get(turn, 0) + len(re.findall(r">> CAN ATTACK", res))
        if row.get("tool") == "end_turn":
            for m in re.finditer(
                r"Your \S+ \((UNIT_[A-Z_]+)\) took (\d+) damage", res
            ):
                damaged.setdefault(turn, []).append(m.group(1))

    text = CHECKS.read_text(encoding="utf-8")
    print(f"=== replay of {CHECKS} against the abandoned line T101-T116 ===")
    print(f"turns with diary rows: {sorted(agent)}")
    print()
    header = f"{'T':>4} {'mil':>4} {'siege':>5} {'rng':>3} {'mel':>3} {'ram':>3} | {'atk':>3} {'err':>3} {'dmg':>3} | rules that would fire"
    print(header)
    print("-" * len(header))
    fired: dict[str, list[int]] = {}
    for turn in sorted(agent):
        row = agent[turn]
        context = et._context_from_row(row)
        if context is None:
            continue
        made = attacks.get(turn, [])
        context.metrics["attacks_this_turn"] = len([a for a in made if not a["error"]])
        context.metrics["damaged_this_turn"] = len(damaged.get(turn, []))
        try:
            run = turn_checks.run_checks(text, context)
        except turn_checks.CheckError as exc:
            print(f"{turn:>4}  run_checks failed: {exc}")
            continue
        ids = sorted(run.failing_ids)
        for rid in ids:
            fired.setdefault(rid, []).append(turn)
        comp = row.get("unit_composition") or {}
        siege = int(comp.get("CATAPULT", 0)) + int(comp.get("TREBUCHET", 0))
        rng = int(comp.get("ARCHER", 0)) + int(comp.get("CROSSBOWMAN", 0))
        mel = int(comp.get("WARRIOR", 0)) + int(comp.get("SWORDSMAN", 0))
        ram = int(comp.get("BATTERING_RAM", 0))
        print(
            f"{turn:>4} {row.get('military', 0):>4} {siege:>5} {rng:>3} {mel:>3} {ram:>3} |"
            f" {len(made):>3} {len([a for a in made if a['error']]):>3} {len(damaged.get(turn, [])):>3} |"
            f" {', '.join(ids) if ids else '-'}"
        )

    print()
    print("=== per rule: turns it would have fired ===")
    for rid in sorted(fired):
        print(f"  {rid:<38} {fired[rid]}")

    print()
    print("=== siege geometry from the attack results (the game's own distance) ===")
    for turn in sorted(attacks):
        for a in attacks[turn]:
            if a["into_city"] or (a["x"], a["y"]) == (54, 40):
                print(
                    f"  T{turn}: unit {a['unit']} -> ({a['x']},{a['y']})"
                    f" city-tile={a['into_city']} error={a['error'] or '-'} dealt~{a['dealt']}"
                )
    print()
    print("=== what the log shows that the diary cannot: hint vs attack, and siege distance ===")
    for turn in sorted(set(list(hints) + list(attacks))):
        made = [a for a in attacks.get(turn, []) if not a["error"]]
        distances = [a["dist"] for a in attacks.get(turn, []) if a.get("dist")]
        print(
            f"  T{turn}: legal-attack hints {hints.get(turn, 0):>2} | attacks made {len(made):>2}"
            f" | attack distances {distances or '-'}"
            f" -> unused-attack upper bound {max(0, hints.get(turn, 0) - len(made))}"
        )

    print()
    print("=== enemy contact as the end_turn threat lines recorded it ===")
    for turn in sorted(agent):
        seen: list[str] = []
        for row in log:
            if turn_of(row) != turn or row.get("tool") != "end_turn":
                continue
            for owner, unit, cs, hp, dist in re.findall(
                r"THREAT: (\S+) (UNIT_[A-Z_]+) CS:(\d+)[^|]*?HP:(\d+)/\d+ spotted (\d+) tiles away",
                str(row.get("result") or ""),
            ):
                entry = f"{unit} CS{cs} HP{hp} {dist}t"
                if entry not in seen:
                    seen.append(entry)
        if seen:
            print(f"  T{turn}: " + "; ".join(seen))

    print()
    print("=== our own damage events in the end_turn results ===")
    for turn in sorted(agent):
        for row in log:
            if turn_of(row) != turn or row.get("tool") != "end_turn":
                continue
            for m in re.finditer(r"Your ([^\n(]+) \((UNIT_[A-Z_]+)\) took (\d+) damage", str(row.get("result") or "")):
                print(f"  T{turn}: {m.group(2)} took {m.group(3)}")

    print()
    print("=== claims that CANNOT be replayed from these records ===")
    print("  garrisoned_units / cities_over_garrison : the archive has no city coordinates")
    print("  local_superiority / siege_exposed       : needs live positions; the attack results")
    print("                                            give dist per attacker only")
    print("  unused_attacks                          : only on turns with a get_units call,")
    print(f"                                            and only as hint counts {hints}")
    print(f"  unit orders recorded per turn           : {orders}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
