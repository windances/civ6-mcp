"""Whittle the Free City of Moscow to 0 with ranged fire, then take it with a chariot.

The human's instruction for this run (T120, `AutoSave_0120` reloaded): *"the chariot is for
capturing - attack first with the other ranged units."* So:

* **capture units** (the two Heavy Chariots in the north) never attack while the city is above
  0-1 HP. One of them is already adjacent at (55,40) and on 4 HP - walking onto a broken city is
  not a fight, so a nearly dead unit can still be the one that takes it;
* **everything that can shoot** bombards the city tile instead: two Trebuchets and five Archers;
* when the city is at 0-1 HP and a capture unit can reach the tile this turn, that unit is ordered
  onto it - the call that used to go out without the ATTACK modifier and be refused - and the run
  stops on `CITY TAKEN`.

Which class may take a city is itself part of what this answers: the adapter's capture scan counts
only MELEE and ANTI_CAVALRY promotion classes and excludes CAVALRY, so if a Heavy Chariot takes
Moscow the scan has a false negative and the TAKE THE CITY block was staying silent next to a city
a chariot could have walked into.

    .venv\\Scripts\\python.exe .tools\\take-moscow.py --dry-run
    .venv\\Scripts\\python.exe .tools\\take-moscow.py
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

CITY = (54, 40)
# Heavy Chariots that can reach the city: the one already adjacent (4 HP) and the healthy one in
# St Petersburg. A third sits far north by the barbarians and is left out.
CAPTURE_UNITS = [2097157, 2031633]
MAX_TURNS = 10


def brief(text: str, limit: int = 3) -> str:
    """The lines of a response that carry the outcome, refusals included."""
    keep = [
        line.strip()
        for line in (text or "").splitlines()
        if line.strip().startswith(("OK", "ERR", "Error", "RANGE_ATTACK", "MELEE_ATTACK",
                                    "CITY TAKEN", "CAPTURE", "MOVING_TO", "Post-combat",
                                    "damage dealt", "city hp"))
    ]
    return " | ".join(keep[:limit]) or (text or "").strip()[:200]


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report the board, order nothing")
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    taken = False
    try:
        for round_no in range(1, MAX_TURNS + 1):
            ov = await gs.get_game_overview()
            rows = await gs.capture_readiness()
            moscow = next((r for r in rows if (r.x, r.y) == CITY), None)
            units = await gs.get_units()
            alive = {u.unit_id: u for u in units}
            print(f"\n[T{ov.turn}] round {round_no}: " + (
                f"moscow hp {moscow.hp}/{moscow.max_hp} walls {moscow.wall_hp}/{moscow.wall_max} "
                f"supply {getattr(moscow, 'supply_covered', '?')}/"
                f"{getattr(moscow, 'supply_total', '?')} melee_adjacent {moscow.melee_adjacent} "
                f"takeable {moscow.takeable}"
                if moscow else "Moscow is not an enemy city in the scan"))
            for cid in CAPTURE_UNITS:
                u = alive.get(cid)
                if u is None:
                    print(f"  capture unit {cid}: gone from the board")
                    continue
                pe = await gs.get_pathing_estimate(cid, *CITY)
                print(f"  capture unit {cid}: {u.unit_type} ({u.x},{u.y}) hp {u.health} "
                      f"moves {u.moves_remaining} -> pathing turns={pe.turns} tiles={pe.total_tiles}")
            if moscow is None:
                break
            if args.dry_run:
                return 0

            # 1. Ranged fire only: every unit that shoots, except the capture units.
            for u in units:
                if u.unit_id in CAPTURE_UNITS or u.moves_remaining <= 0:
                    continue
                if u.ranged_strength <= 0:
                    continue
                res = await gs.attack_unit(u.unit_id, *CITY)
                print(f"  fire {u.unit_type} {u.unit_id} -> {brief(res)}")
                if "CITY TAKEN" in (res or ""):
                    print("*** CITY TAKEN by ranged fire ***")
                    taken = True
                    break
            if taken:
                break

            rows = await gs.capture_readiness()
            moscow = next((r for r in rows if (r.x, r.y) == CITY), None)
            if moscow is None:
                print("  Moscow left the enemy list after the bombardment - stopping.")
                break
            print(f"  after the volley: hp {moscow.hp}/{moscow.max_hp}")

            # 2. The capture units: take it if it is broken and one of them is in reach, else march.
            for cid in CAPTURE_UNITS:
                u = alive.get(cid)
                if u is None:
                    continue
                pe = await gs.get_pathing_estimate(cid, *CITY)
                if pe.turns == 1 and moscow.hp <= 1:
                    res = await gs.move_unit(cid, *CITY)
                    print(f"  CAPTURE MOVE {u.unit_type} {cid} (hp {u.health}) -> {CITY}: {brief(res)}")
                    print(f"  raw: {(res or '').strip()[:300]}")
                    if "CITY TAKEN" in (res or ""):
                        print("*** CITY TAKEN ***")
                        taken = True
                        break
                    if "Error" in (res or "") or "ERR" in (res or ""):
                        print("  the capture move was refused - that answer is the point; stopping.")
                        return 0
                elif pe.turns == 1 and moscow.hp > 1:
                    # In reach but the city still stands: nothing to do this turn, keep it posted.
                    print(f"  {cid} is in reach; the city is at {moscow.hp} - holding fire, "
                          f"the chariot does not attack.")
                else:
                    path = await gs.get_pathing_estimate(cid, *CITY)
                    waypoints = [w for w in (path.waypoints or []) if w and w != "()"]
                    if len(waypoints) < 3:
                        print(f"  {cid}: no waypoint to march along ({waypoints})")
                        continue
                    dest = waypoints[min(2, len(waypoints) - 1)]
                    try:
                        dx, dy = (int(v) for v in dest.strip("()").split(","))
                    except ValueError:
                        print(f"  {cid}: unparseable waypoint {dest!r}")
                        continue
                    res = await gs.move_unit(cid, dx, dy)
                    print(f"  march {cid} along path to {dest}: {brief(res)}")
            if taken:
                break

            # 3. Everything else skipped, then the turn ends.
            await gs.skip_remaining_units()
            before = ov.turn
            result = await gs.end_turn()
            after = (await gs.get_game_overview()).turn
            print(f"  end_turn: {before} -> {after}")
            if after == before:
                print("  the turn did not advance; end_turn said:")
                print("  " + (result or "")[:1500].replace("\n", "\n  "))
                break
    finally:
        await conn.disconnect()

    print("\n=== capture verified: the game reported CITY TAKEN ===" if taken
          else "\n=== stopped without a capture (see the last lines above) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
