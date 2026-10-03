"""What the Tyre operation needs to know before another tile is marched.

Read-only. Prints the diplomatic state of every met civ (with the war flag and military strength),
every foreign city we can currently see with its walls and garrison, and the map around the target.

    python .tools/tyre-recon.py
    python .tools/tyre-recon.py --area 26,11 --radius 3
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

WAR_STATE = 6


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", metavar="X,Y", help="also read the map around this tile")
    ap.add_argument("--radius", type=int, default=3)
    ap.add_argument(
        "--staging",
        metavar="X,Y",
        help="the game's own staging plan for this target tile (ring, FIRE verdicts, arrival turns)",
    )
    ap.add_argument(
        "--path",
        action="append",
        default=[],
        metavar="INDEX:X,Y",
        help="pathing estimate for one of our units, e.g. --path 27:26,11",
    )
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)

    print("=== diplomacy ===")
    for civ in await gs.get_diplomacy():
        war = "  <== AT WAR" if getattr(civ, "is_at_war", False) else ""
        print(
            f"  p{civ.player_id} {civ.civ_name:<14} {civ.leader_name:<14} "
            f"met={civ.has_met} state={civ.diplomatic_state} "
            f"mil={civ.military_strength} cities={civ.num_cities} "
            f"rel={civ.relationship_score} grieve={civ.grievances} "
            f"pacts={civ.defensive_pacts or '-'} "
            f"alliance={civ.alliance_type or '-'}{war}"
        )

    print("\n=== foreign cities visible ===")
    sightings = await gs.visible_foreign_cities()
    if not sightings:
        print("  (none visible)")
    for city in sorted(sightings, key=lambda c: (c.x, c.y)):
        print(
            f"  ({city.x},{city.y}) {city.name:<16} owner p{getattr(city, 'owner', '?')} "
            f"{getattr(city, 'owner_name', '')} pop{getattr(city, 'population', '?')} "
            f"walls {getattr(city, 'wall_hp', '?')}/{getattr(city, 'wall_max_hp', '?')}"
        )

    if args.area:
        ax, ay = (int(v) for v in args.area.split(","))
        print(f"\n=== map around ({ax},{ay}) r{args.radius} ===")
        area = await gs.get_map_area(ax, ay, args.radius)
        tiles = getattr(area, "tiles", area) or []
        for tile in tiles:
            units = getattr(tile, "units", None) or []
            names = "; ".join(
                f"{getattr(u, 'unit_type', '?')}({getattr(u, 'owner_name', '')})"
                for u in units
            )
            print(
                f"  ({getattr(tile, 'x', '?')},{getattr(tile, 'y', '?')}) "
                f"{getattr(tile, 'terrain', '')} {getattr(tile, 'feature', '') or ''} "
                f"imp={getattr(tile, 'improvement', '') or '-'} "
                f"owner={getattr(tile, 'owner_name', '') or '-'} {names}"
            )
    if args.staging:
        sx, sy = (int(v) for v in args.staging.split(","))
        print(f"\n=== staging plan for ({sx},{sy}) ===")
        plan = await gs.staging_plan(sx, sy)
        print(plan if isinstance(plan, str) else repr(plan))
        return 0

    if args.path:
        units = {u.unit_index: u for u in await gs.get_units()}
        print("\n=== pathing ===")
        for spec in args.path:
            index, _, tile = spec.partition(":")
            tx, ty = (int(v) for v in tile.split(","))
            unit = units.get(int(index))
            if unit is None:
                print(f"  [{index}] no such unit")
                continue
            try:
                estimate = await gs.get_pathing_estimate(int(index), tx, ty)
            except Exception as exc:  # noqa: BLE001
                print(f"  [{index}] {unit.unit_type} ({unit.x},{unit.y}) -> {tx},{ty}: {exc}")
                continue
            print(
                f"  [{index}] {unit.unit_type} ({unit.x},{unit.y}) mv{unit.moves_remaining} "
                f"-> ({tx},{ty}): {estimate}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
