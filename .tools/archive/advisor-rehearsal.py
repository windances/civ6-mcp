"""Assemble the military advisor's brief for T111 of the abandoned siege line, from records.

This is the rehearsal harness for the Phase 2 contract: a canonical snapshot, the two tactic
files that match the situation, and the turn's judgement signals - exactly what the orchestrator
is now required to paste into the `civ_advisor` call. The output is written to
`.tools/_advisor-brief.md` for a fresh (isolated) context to answer as the worker.

    .venv\\Scripts\\python.exe .tools\\advisor-rehearsal.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

DATA = pathlib.Path(".civ6-mcp-data")
BRANCH = DATA / "branches" / "abandoned-T101-T116"
LOG = DATA / "log_china_-1894041591_stoic-amber-vineyard-98.jsonl"
TURN = 111


def load(path: pathlib.Path) -> list[dict]:
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


def unit_line(text: str) -> list[dict]:
    """The `get_units` block of our own units, as the tool printed it."""
    out = []
    for line in text.splitlines():
        m = re.search(
            r"(\S+) \((UNIT_[A-Z_]+)\) at \((\d+),(\d+)\)(?: — (.*))?", line
        )
        if not m or "Nearby threats" in line:
            continue
        name, unit_type, x, y, rest = m.groups()
        out.append(
            {
                "name": name,
                "type": unit_type,
                "x": int(x),
                "y": int(y),
                "detail": (rest or "").strip(),
            }
        )
    return out


def threats(text: str) -> list[dict]:
    out = []
    for m in re.finditer(
        r"(Barbarian|俄罗斯|埃及) \((\d+) units?\):((?:\n\s+UNIT_[^\n]+)+)", text
    ):
        owner = m.group(1)
        for line in m.group(3).splitlines():
            t = re.search(
                r"(UNIT_[A-Z_]+) at \((\d+),(\d+)\) — CS:(\d+)(?: RS:(\d+))? HP:(\d+)/(\d+) \((\d+) tiles away\)",
                line,
            )
            if t:
                out.append(
                    {
                        "owner": owner,
                        "type": t.group(1),
                        "x": int(t.group(2)),
                        "y": int(t.group(3)),
                        "cs": int(t.group(4)),
                        "rs": int(t.group(5) or 0),
                        "hp": int(t.group(6)),
                        "max_hp": int(t.group(7)),
                        "tiles_away": int(t.group(8)),
                    }
                )
    return out


def cities_from_log(log: list[dict], turn: int) -> list[dict]:
    """Our cities with their coordinates, as `get_cities` reported them on this turn.

    Without these the snapshot is ambiguous: Civ VI reports the units inside a city at the
    city's own tile, so "2 Archers + 1 Warrior at (57,29)" looks like an impossible stack until
    you know that (57,29) is Beijing. Both advisor rehearsals flagged it for exactly that
    reason, so the brief carries the city tiles.
    """
    for row in log:
        if row.get("tool") != "get_cities" or turn_of(row) != turn:
            continue
        out = []
        for match in re.finditer(
            r"^\s*(\S+) \(pop (\d+)\) at \((\d+),(\d+)\)", str(row.get("result") or ""), re.M
        ):
            out.append(
                {
                    "name": match.group(1),
                    "population": int(match.group(2)),
                    "x": int(match.group(3)),
                    "y": int(match.group(4)),
                }
            )
        if out:
            return out
    return []


def main() -> int:
    diary = {
        r["turn"]: r
        for r in load(BRANCH / "diary_future_T101_T116.jsonl")
        if r.get("is_agent") and isinstance(r.get("turn"), int)
    }
    row = diary.get(TURN, {})
    log = load(LOG)
    units_text = next(
        (str(r.get("result") or "") for r in log if r.get("tool") == "get_units" and turn_of(r) == TURN),
        "",
    )
    end_turn_text = "\n".join(
        str(r.get("result") or "") for r in log if r.get("tool") == "end_turn" and turn_of(r) == TURN
    )
    attacks = [
        (r.get("params") or {})
        for r in log
        if r.get("tool") == "unit_action"
        and (r.get("params") or {}).get("action") == "attack"
        and turn_of(r) == TURN
    ]
    failed = sorted(set(re.findall(r"CHECK FAILED \[([a-z-]+)\]", end_turn_text)))
    cities = cities_from_log(log, TURN)

    snapshot = {
        "version": 1,
        "gameId": "china_-1894041591",
        "turn": TURN,
        "overview": {
            "civ": "China",
            "leader": "Qin (Unifier)",
            "cities": row.get("cities"),
            "population": row.get("pop"),
            "military": row.get("military"),
            "science": row.get("science"),
            "culture": row.get("culture"),
            "gold": row.get("gold"),
            "gold_per_turn": row.get("gold_per_turn"),
            "score": row.get("score"),
            "current_research": row.get("current_research"),
            "current_civic": row.get("current_civic"),
        },
        "units": unit_line(units_text),
        "cities": cities,
        "map": {
            "target_city": {"name": "Moscow", "x": 54, "y": 40, "owner": "Russia"},
            "note": "terrain around the target is not in this record",
        },
        "diplomacy": [
            {"civ": "Russia", "state": "WAR", "state_index": 6, "grievances": -150,
             "military": 90, "cities": 3},
            {"civ": "Egypt", "state": "DECLARED_FRIEND", "state_index": 1},
        ],
        "victory": {"score_rank": 2, "science_rank": 2, "military_rank": 1},
        "blockers": [],
        "recentEvents": threats(units_text),
    }

    tactic_dir = pathlib.Path("prompts/tactics")
    tactics = {
        "prompts/tactics/02-contact-on-discovery.md": (tactic_dir / "02-contact-on-discovery.md").read_text(encoding="utf-8"),
        "prompts/tactics/05-formation-and-screening.md": (tactic_dir / "05-formation-and-screening.md").read_text(encoding="utf-8"),
    }
    # The orchestrator passes the role file as the worker's instructions (Phase 2: "the complete
    # canonical snapshot and its role instructions"), so a faithful brief carries it too.
    role = pathlib.Path("prompts/workers/military-map.md").read_text(encoding="utf-8")

    attacks_made = "\n".join(
        f"  - unit {a.get('unit_id')} attack -> ({a.get('target_x')},{a.get('target_y')})" for a in attacks
    )
    brief = f"""# Military advisor brief - turn {TURN} (rehearsal, reconstructed from telemetry)

You are the `military-map` advisor. You are read-only: you hold **no tools and no filesystem**.
Everything you may use is in this message. Return only JSON matching
`contracts/worker-proposal.schema.json` with `worker: "military-map"`, `gameId`
`china_-1894041591`, `turn` {TURN}.

## What the orchestrator pasted for you

### 1. The canonical snapshot
```json
{json.dumps(snapshot, ensure_ascii=False, indent=1)}
```

### 2. The judgement signals from this turn's `end_turn`

```
CHECK FAILED (from the previous end_turn): {', '.join(failed) or 'none recorded'}

BATTLE ASSESSMENT (reconstructed from the threat scan of this turn; class comes from the game's PROMOTION_CLASS_*):
  Russia (2 units within 3 tiles), both engaged with our army:
    UNIT_WARRIOR   CS:20 HP:86/100 dist:1 class:MELEE  - yours in range: 2 (1 adjacent)  [garrison of Moscow, on the city tile]
    UNIT_SWORDSMAN CS:35 HP:53/100 dist:1 class:MELEE  - yours in range: 2 (1 adjacent)
    UNIT_ARCHER    CS:15 RS:25 HP:100/100 dist:2 class:RANGED - yours in range: 1
  concentration: 2 of your units are within 2 tiles of the closest enemy - enough for a kill
  killable now: UNIT_SWORDSMAN at 53 HP (2 of your units in range, 1 adjacent)

SIEGE POSTURE (reconstructed from this turn's positions):
  UNIT_CATAPULT@(54,39): enemy 1, screen none in range, city 1 (Moscow) - EXPOSED
  UNIT_CATAPULT@(54,38): enemy 2, screen none in range, city 2 (Moscow) - EXPOSED
  (no friendly melee, anti-cavalry or cavalry unit is closer to the enemy than the Catapults)

SIEGE PROGRESS: Moscow city hp was not reported by this build (the city has no walls); the
garrison Warrior has been rotating at 100 HP for several turns and the Swordsman went
100 -> 66 -> 53 across T109-T111.

UNUSED ATTACK (2 units had a legal attack and did not take it):
  UNIT_HEAVY_CHARIOT@53,36 -> UNIT_SWORDSMAN@53,35(53hp)
  UNIT_ARCHER@(53,34) -> UNIT_SWORDSMAN@53,35(53hp)

attacks actually made this turn:
{attacks_made or '  (none)'}
```

### 3. The tactic files that match this turn
{chr(10).join(f"#### {path}{chr(10)}{text}" for path, text in tactics.items())}

### 4. Your role instructions
{role}

## Your task in one paragraph

Say what the army should do this turn and where each unit should stand, as JSON. Name units that
appear in the snapshot and tiles that exist; put anything you cannot know from this brief in
`warnings` instead of assuming it. Start the `assessment` string with the tactic file you applied
and the decisive number.
"""
    out = pathlib.Path(".tools/_advisor-brief.md")
    out.write_text(brief, encoding="utf-8")
    snapshot_path = pathlib.Path(".tools/_advisor-snapshot.json")
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out} ({len(brief)} bytes) and {snapshot_path}")
    print(f"our units parsed: {len(snapshot['units'])}, threats: {len(snapshot['recentEvents'])}")
    print(f"CHECK FAILED replayed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
