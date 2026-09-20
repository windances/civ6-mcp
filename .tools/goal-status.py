"""Goal execution status for the running game, rebuilt from the diary. Read-only.

Answers "how are we doing against our own goals" without the tuner: the diary has one row per
civilisation per turn, so the check file can be re-evaluated for every turn and each rule's
status, streak and clearing turn are measurable rather than remembered. Nothing here writes:
it calls ``run_checks`` directly instead of ``end_turn``'s ``_evaluate_checks``, so the rule
file is never swept.

    .venv\\Scripts\\python.exe .tools\\goal-status.py [--turns 40] [--seed -1894041591]

Sections: the directive's checkable rules (with streaks), the strategic milestones the rules
cannot see (siege train, target, rank), the ten-turn window, and the agent's own stated plan
for that window quoted back next to what actually moved.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# The console here is cp936; civ and city names are Chinese and would be mojibake without this.
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.end_turn import _context_from_row  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[1]
CHECKS = REPO / "prompts" / "checks" / "turn-checks.md"

SIEGE = ("CATAPULT", "TREBUCHET", "BOMBARD", "ARTILLERY")
RANGED = ("SLINGER", "ARCHER", "CROSSBOWMAN", "FIELD_CANNON", "CROUCHING_TIGER")
MELEE = ("WARRIOR", "SWORDSMAN", "MAN_AT_ARMS", "MUSKETEER", "MUSKETMAN", "INFANTRY", "PIKEMAN", "SPEARMAN")
WINDOW_METRICS = (
    ("cities", "cities", "{:+.0f}"),
    ("pop", "pop", "{:+.0f}"),
    ("science", "science", "{:+.1f}"),
    ("culture", "culture", "{:+.1f}"),
    ("gold_per_turn", "gold/turn", "{:+.1f}"),
    ("military", "military", "{:+.0f}"),
    ("districts", "districts", "{:+.0f}"),
    ("improvements", "improvements", "{:+.0f}"),
    ("wonders", "wonders", "{:+.0f}"),
    ("techs_completed", "techs", "{:+.0f}"),
    ("civics_completed", "civics", "{:+.0f}"),
)


def load_rows(seed: str) -> tuple[dict[int, dict], dict[int, dict[int, dict]]]:
    """(agent rows by turn, every civ's rows by turn)."""
    path = REPO / ".civ6-mcp-data" / f"diary_china_{seed}.jsonl"
    agent: dict[int, dict] = {}
    everyone: dict[int, dict[int, dict]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        turn = row.get("turn")
        if not isinstance(turn, int):
            continue
        everyone.setdefault(turn, {})[row.get("pid")] = row
        if row.get("is_agent"):
            agent[turn] = row  # later rows for the same turn win (a replayed turn)
    return agent, everyone


def counts(row: dict, kinds: tuple[str, ...]) -> int:
    comp = row.get("unit_composition") or {}
    return sum(int(comp.get(k, 0)) for k in kinds)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--seed", default="-1894041591")
    args = ap.parse_args()

    agent, everyone = load_rows(args.seed)
    turns = sorted(agent)
    if not turns:
        print("no agent rows in the diary")
        return 1
    now_turn = turns[-1]
    now = agent[now_turn]
    text = CHECKS.read_text(encoding="utf-8")
    rules = {c.check_id: c for c in turn_checks.parse_checks(text)}
    history = [t for t in turns if t > now_turn - args.turns]

    # --- per-rule status across the window ------------------------------------------------
    status: dict[str, dict] = {rid: {"fail": [], "pass": [], "skip": []} for rid in rules}
    broken: list[tuple[int, str]] = []
    for turn in history:
        ctx = _context_from_row(agent[turn])
        if ctx is None:
            continue
        try:
            run = turn_checks.run_checks(text, ctx)
        except turn_checks.CheckError as exc:
            broken.append((turn, str(exc)))
            continue
        for rid in status:
            if rid in run.failing_ids:
                status[rid]["fail"].append(turn)
            elif rid in run.skipped:
                status[rid]["skip"].append(turn)
            elif rid in run.passed:
                status[rid]["pass"].append(turn)

    print(f"=== goal execution at T{now_turn} (rules: {CHECKS.relative_to(REPO)}) ===")
    print(f"window: T{history[0]}..T{now_turn}  ({len(history)} agent rows)")
    if broken:
        print(f"!! {len(broken)} turn(s) had an unevaluable rule, e.g. T{broken[0][0]}: {broken[0][1]}")
    print()
    print(f"{'rule':<38} {'kind':<8} {'status':<12} streak  note")
    for rid, check in rules.items():
        st = status[rid]
        gate_off = bool(st["skip"]) and not st["pass"] and not st["fail"]
        if st["fail"] and st["fail"][-1] == now_turn:
            kind = "GOAL" if check.once else "standing"
            # streak = consecutive failing turns ending at the latest turn
            streak = 0
            for turn in reversed(history):
                if turn in st["fail"]:
                    streak += 1
                else:
                    break
            note = f"since T{st['fail'][-1 - streak + 1] if streak else now_turn}: {check.message.split('.')[0][:60]}"
            print(f"{rid:<38} {kind:<8} {'FAILING':<12} {streak:>5}t  {note}")
        elif st["pass"] and st["pass"][-1] == now_turn:
            kind = "GOAL" if check.once else "standing"
            extra = " -> ACHIEVED (should retire)" if check.once else ""
            print(f"{rid:<38} {kind:<8} {'PASSES':<12} {'':>6}  last failed T{st['fail'][-1] if st['fail'] else '-'}{extra}")
        elif gate_off:
            print(f"{rid:<38} {'goal' if check.once else 'standing':<8} {'gated off':<12} {'':>6}  {check.when}")
        else:
            print(f"{rid:<38} {'goal' if check.once else 'standing':<8} {'?':<12} {'':>6}")

    # --- the milestones the rules cannot see ----------------------------------------------
    print()
    print("=== strategic position (directive) ===")
    print(f"cities {now.get('cities')}  pop {now.get('pop')}  score {now.get('score')}  era {now.get('era')} / {now.get('age')}")
    print(f"science {now.get('science')}/t  culture {now.get('culture')}/t  gold {now.get('gold')} ({now.get('gold_per_turn')}/t)  faith {now.get('faith')}")
    print(f"military {now.get('military')}  districts {now.get('districts')}  improvements {now.get('improvements')}  wonders {now.get('wonders')}")
    print(f"army: {' '.join(f'{k}={v}' for k, v in sorted((now.get('unit_composition') or {}).items()))}")
    print(f"siege {counts(now, SIEGE)}/{2}   ranged {counts(now, RANGED)}/{4}   melee {counts(now, MELEE)}/{2}"
          f"   (directive's assault train for one city)")
    print(f"research {now.get('current_research')}  civic {now.get('current_civic')}")
    print(f"techs {len(now.get('techs') or [])}  civics {len(now.get('civics') or [])}")

    # rank among the 8 civs on this turn, and the strongest rival
    peers = [r for r in (everyone.get(now_turn) or {}).values() if r.get("pid") != 0]
    if peers:
        def rank(key):
            mine = now.get(key) or 0
            return 1 + sum(1 for p in peers if (p.get(key) or 0) > mine)
        best_sci = max(peers, key=lambda p: p.get("science") or 0)
        best_mil = max(peers, key=lambda p: p.get("military") or 0)
        best_score = max(peers, key=lambda p: p.get("score") or 0)
        print(f"rank of 8: score {rank('score')}  science {rank('science')}  military {rank('military')}  pop {rank('pop')}  cities {rank('cities')}")
        print(f"best rival: science {best_sci.get('science')} ({best_sci.get('civ')})  military {best_mil.get('military')} ({best_mil.get('civ')})  score {best_score.get('score')} ({best_score.get('civ')})")

    # --- the ten-turn window --------------------------------------------------------------
    past_turn = max((t for t in turns if t <= now_turn - 10), default=None)
    if past_turn is not None:
        past = agent[past_turn]
        print()
        print(f"=== window T{past_turn} -> T{now_turn} ===")
        for key, label, fmt in WINDOW_METRICS:
            before, after = past.get(key), now.get(key)
            if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                span = now_turn - past_turn
                delta = after - before
                print(f"  {label:<12} {before:>8} -> {after:>8}   {fmt.format(delta):>8}   {delta / span:+.2f}/t")

    # --- the agent's own plan, quoted back ------------------------------------------------
    for turn in (past_turn, now_turn):
        if turn is None:
            continue
        refl = agent[turn].get("reflections") or {}
        print()
        print(f"=== the agent's own plan stated at T{turn} ===")
        for key in ("planning", "hypothesis"):
            value = (refl.get(key) or "").strip()
            print(f"  {key}: {value[:700]}{'...' if len(value) > 700 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
