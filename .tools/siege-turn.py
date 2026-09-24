"""Drive one turn of the Moscow siege, or report the board - the minimises-surprise half of the loop.

This session has no MCP tool bindings, so the same library the MCP server wraps is used directly
(`civ_mcp.game_state.GameState`). Every call is the implementation behind a documented tool:

    --board                       get_game_overview + get_units + capture readiness (read-only)
    --attacks X Y                 attack (X,Y) with every unit that can, one call each, printing
                                  each response - this is `attack` from the tool list
    --move UNIT X Y               `move`
    --end-turn                    `end_turn` (writes the next 0_MCP autosave)
    --skip-rest                   `skip_remaining_units`

Nothing is ordered unless a flag asks for it, and every response is printed verbatim so the
verification (CITY TAKEN, CAPTURE_MOVE, city HP deltas) is the game's own words.
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


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", action="store_true")
    ap.add_argument("--attacks", nargs=2, metavar=("X", "Y"))
    ap.add_argument("--attack", nargs=3, action="append", metavar=("UNIT_ID", "X", "Y"),
                    help="attack with one named unit (repeatable); city tiles never appear in a "
                         "unit's target list, so the choice has to be explicit")
    ap.add_argument("--move", nargs=3, metavar=("UNIT_ID", "X", "Y"))
    ap.add_argument("--end-turn", action="store_true")
    ap.add_argument("--skip-rest", action="store_true")
    ap.add_argument("--path", nargs=3, action="append", metavar=("UNIT_ID", "X", "Y"),
                    help="the game's own pathing estimate to a tile (read-only, repeatable)")
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    try:
        if args.board:
            ov = await gs.get_game_overview()
            print(f"=== T{ov.turn} {ov.civ_name}: cities {ov.num_cities}, units {ov.num_units}, "
                  f"score {ov.score}, gold {ov.gold:.0f} ({ov.gold_per_turn:+.1f}/turn), "
                  f"research {ov.current_research}, civic {ov.current_civic} ===")
            units = await gs.get_units()
            print(f"--- {len(units)} units ---")
            for u in units:
                print(f"  {u.unit_id:>8} {u.unit_type:<22} ({u.x},{u.y}) "
                      f"hp {u.health}/{u.max_health} moves {u.moves_remaining} "
                      f"targets {u.targets}")
            rows = await gs.capture_readiness()
            print(f"--- capture scan: {len(rows)} enemy cit(ies) ---")
            for r in rows:
                print(f"  {r.city_name}@({r.x},{r.y}) hp {r.hp}/{r.max_hp} walls {r.wall_hp}/"
                      f"{r.wall_max} adj {r.melee_adjacent} within2 {r.melee_within_2} "
                      f"supply {getattr(r, 'supply_covered', '?')}/{getattr(r, 'supply_total', '?')} "
                      f"takeable {r.takeable}")

        if args.attacks:
            x, y = int(args.attacks[0]), int(args.attacks[1])
            units = await gs.get_units()
            attackers = []
            for u in units:
                for t in (u.targets or []):
                    if str(t).startswith(f"({x},{y})") or f"@{x},{y}" in str(t):
                        attackers.append(u)
                        break
            print(f"=== {len(attackers)} unit(s) list ({x},{y}) as an attack target ===")
            for u in attackers:
                print(f"--- {u.unit_type} {u.unit_id} ({u.x},{u.y}) -> ({x},{y}) ---")
                print("  " + (await gs.attack_unit(u.unit_id, x, y)).replace("\n", "\n  "))

        if args.move:
            unit_id, x, y = (int(a) for a in args.move)
            print(f"=== move {unit_id} -> ({x},{y}) ===")
            print(await gs.move_unit(unit_id, x, y))

        if args.attack:
            for unit_id, x, y in ((int(a), int(b), int(c)) for a, b, c in args.attack):
                print(f"--- attack: {unit_id} -> ({x},{y}) ---")
                print("  " + (await gs.attack_unit(unit_id, x, y)).replace("\n", "\n  "))

        for unit_id, x, y in ((int(a), int(b), int(c)) for a, b, c in (args.path or [])):
            print(f"=== pathing {unit_id} -> ({x},{y}) ===")
            print(await gs.get_pathing_estimate(unit_id, x, y))

        if args.skip_rest:
            print("=== skip_remaining_units ===")
            print(await gs.skip_remaining_units())

        if args.end_turn:
            print("=== end_turn ===")
            print(await gs.end_turn())
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
