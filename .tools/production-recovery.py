"""Everything that is costing production right now, and the repairs that end it.

`state.py --cities` prints the queue, the pillaged *improvements* and the growth numbers, but not the
two things that actually stop a city producing: a queue that is **empty** (the city is doing nothing
at all) and a **pillaged district or building** (which for an Industrial Zone means a power and
production penalty across the whole empire, not one city's problem - measured T291, `城市供电不足`
four times while Xi'an queued a project instead of the repair).

    python .tools/production-recovery.py             # read only: the bill, worst first
    python .tools/production-recovery.py --apply     # queue the repairs, then read back

Read-only by default, and it issues no move orders, so it is safe to run mid-turn.
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

IDLE = "nothing"


def line(city) -> str:
    pills = list(getattr(city, "pillaged_districts", None) or [])
    pillb = list(getattr(city, "pillaged_buildings", None) or [])
    short = lambda xs: ",".join(x.replace("DISTRICT_", "").replace("BUILDING_", "") for x in xs)
    return (
        f"  {city.name:<10} ({city.x},{city.y}) pop{city.population:<3} prod {city.production:>5.1f} "
        f"queue {city.currently_building} ({city.production_turns_left}t)"
        f"  housing {city.housing:.0f}  food {city.food_surplus:+.1f}\n"
        f"      pillaged districts: {short(pills) or '-'}   buildings: {short(pillb) or '-'}"
        f"   power {city.power_required}/{city.power_free}/{city.power_temporary} {city.power_fully_powered}"
    )


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="queue the repairs, then read back")
    ap.add_argument(
        "--options",
        metavar="NAME,NAME",
        help="print the production options (REPAIRS first) for these cities",
    )
    ap.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="CITY:ITEM",
        help="queue one item in one city, e.g. --set <CITY>:DISTRICT_INDUSTRIAL_ZONE; repeatable",
    )
    ap.add_argument(
        "--place",
        action="append",
        default=[],
        metavar="CITY:DISTRICT",
        help="show the ranked tiles for a district, e.g. --place <CITY>:DISTRICT_INDUSTRIAL_ZONE",
    )
    ap.add_argument(
        "--fill",
        action="store_true",
        help="queue something in every idle city by rule (repair > cheapest building > builder)",
    )
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)

    cities, distances = await gs.get_cities()

    if args.options:
        wanted = [n.strip() for n in args.options.split(",") if n.strip()]
        by_name = {c.name: c for c in cities}
        for name in wanted:
            city = by_name.get(name)
            if city is None:
                print(f"=== {name}: no such city ===")
                continue
            options = await gs.list_city_production(city.city_id)
            print(
                f"=== {name} ({city.x},{city.y}) pop{city.population} prod {city.production} "
                f"queue {city.currently_building} ({city.production_turns_left}t) ==="
            )
            for option in sorted(options, key=lambda o: (not o.is_repair, o.turns, o.cost)):
                tag = "REPAIR" if option.is_repair else option.category
                where = (
                    f" @({option.repair_x},{option.repair_y})"
                    if option.repair_x is not None
                    else ""
                )
                gold = f" gold={option.gold_cost}" if option.gold_cost and option.gold_cost > 0 else ""
                print(
                    f"  {tag:<10} {option.item_name:<42} {option.turns:>3}t"
                    f" cost={option.cost}{gold}{where}"
                )
        return 0

    if args.place:
        by_name = {c.name: c for c in cities}
        for spec in args.place:
            name, _, district = spec.partition(":")
            city = by_name.get(name.strip())
            if city is None:
                print(f"=== {name}: no such city ===")
                continue
            placements = await gs.get_district_advisor(city.city_id, district.strip())
            print(f"=== {name} {district.strip()} ===")
            if isinstance(placements, str):
                print(f"  {placements}")
                continue
            for placement in placements[:6]:
                adj = ", ".join(f"{k}+{v}" for k, v in (placement.adjacency or {}).items())
                print(
                    f"  ({placement.x},{placement.y})  total +{placement.total_adjacency}"
                    f"  {placement.terrain_desc}  {adj}"
                )
        return 0

    if args.fill:
        # The treadmill: a city that finishes its build goes idle, an idle queue blocks
        # `end_turn`, and hand-picking one item per city costs a read and a write each time.
        # The rule here is the directive's own order of work, applied to whatever the city is
        # actually offered: a repair first (the tile is already ours), then the cheapest
        # building (growth and infrastructure before units), then a Builder - which the
        # directive calls the cheapest multiplier in the game - and only then the cheapest
        # remaining item. Units are last on purpose: production goes to the home front first.
        for city in sorted(cities, key=lambda c: -c.production):
            if city.currently_building != IDLE and city.production_turns_left > 0:
                continue
            options = await gs.list_city_production(city.city_id)
            if not options:
                print(f"  {city.name}: nothing offered at all - needs a look by hand")
                continue
            # Every category, in the directive's order of work, so the MISSING_COORDS skip below
            # can fall through to something that does not need a tile: an all-wonder building
            # list (measured in one match) used to exhaust the ranking and leave the queue empty.
            priority = {"BUILDING": 1, "PROJECT": 2, "UNIT": 3}
            ranked = sorted(
                options,
                key=lambda o: (
                    0 if o.is_repair else priority.get(o.category, 4),
                    o.cost,
                    o.turns,
                ),
            )
            # A wonder and a district both need a tile, and the cheapest building in a city is
            # often a wonder - so try the ranking in order and take the first item the game
            # accepts rather than failing the whole city on the first MISSING_COORDS.
            for pick in ranked:
                out = await gs.set_city_production(
                    city.city_id,
                    pick.category,
                    pick.item_name,
                    target_x=pick.repair_x,
                    target_y=pick.repair_y,
                )
                if "MISSING_COORDS" in str(out):
                    continue
                print(f"  {city.name}: {pick.item_name} ({pick.turns}t) -> {out}")
                break
            else:
                print(f"  {city.name}: every offered item wants a tile - needs a look by hand")
        return 0

    if args.set:
        by_name = {c.name: c for c in cities}
        for spec in args.set:
            name, _, item = spec.partition(":")
            item, _, coords = item.strip().partition("@")
            target_x = target_y = None
            if coords:
                xs, _, ys = coords.partition(",")
                target_x, target_y = int(xs), int(ys)
            city = by_name.get(name.strip())
            if city is None:
                print(f"  {name}: no such city")
                continue
            options = await gs.list_city_production(city.city_id)
            # A pillaged district is offered **twice** under the same item name - once as the
            # repair (which carries the tile in `repair_x`/`repair_y`) and once as a fresh build
            # (which carries nothing, because a new district needs a tile chosen for it). Taking
            # the first name match therefore picks the wrong one about half the time and the call
            # comes back MISSING_COORDS. Prefer the repair.
            named = [o for o in options if o.item_name == item]
            match = next((o for o in named if o.is_repair), None) or (named[0] if named else None)
            if match is None:
                print(f"  {name}: {item} is not offerable - read --options first")
                continue
            out = await gs.set_city_production(
                city.city_id,
                match.category,
                match.item_name,
                target_x=target_x if target_x is not None else match.repair_x,
                target_y=target_y if target_y is not None else match.repair_y,
            )
            where = f" @({target_x},{target_y})" if target_x is not None else ""
            print(f"  {name}: {match.item_name}{where} ({match.turns}t) -> {out}")
        print("\n=== read back (non-empty queues only) ===")
        cities, _ = await gs.get_cities()
        for city in cities:
            if city.currently_building != IDLE:
                print(
                    f"  {city.name:<10} {city.currently_building} "
                    f"({city.production_turns_left}t)"
                )
        for city in cities:
            if city.currently_building == IDLE:
                print(f"  STILL IDLE: {city.name} (pop{city.population}, prod {city.production})")
        return 0
    if distances:
        print(f"note: {distances}")

    idle, pillaged = [], []
    for city in cities:
        pills = list(getattr(city, "pillaged_districts", None) or [])
        pillb = list(getattr(city, "pillaged_buildings", None) or [])
        if city.currently_building == IDLE or city.production_turns_left <= 0:
            idle.append(city)
        if pills or pillb:
            pillaged.append(city)

    print(f"=== {len(idle)} idle queue(s) ===")
    for city in sorted(idle, key=lambda c: -c.production):
        print(line(city))
    if not idle:
        print("  (none)")

    print(f"\n=== {len(pillaged)} city/cities with a pillaged district or building ===")
    for city in sorted(pillaged, key=lambda c: -c.production):
        print(line(city))
    if not pillaged:
        print("  (none)")

    if not args.apply:
        return 0

    print("\n=== applying ===")
    for city in pillaged:
        options = await gs.list_city_production(city.city_id)
        repairs = [o for o in options if o.is_repair]
        if not repairs:
            print(f"  {city.name}: no REPAIRS entry offered - read the queue by hand")
            continue
        # Cheapest first: a pillaged Workshop is 1-2 turns and ends the power gap in that city
        # sooner than the district behind it.
        repairs.sort(key=lambda o: (o.turns, o.cost))
        for option in repairs[:1]:
            out = await gs.set_city_production(
                city.city_id,
                option.category,
                option.item_name,
                target_x=option.repair_x,
                target_y=option.repair_y,
            )
            print(f"  {city.name}: {option.item_name} ({option.turns}t) -> {out}")

    print("\n=== read back ===")
    cities, _ = await gs.get_cities()
    for city in cities:
        if city.currently_building == IDLE:
            print(f"  STILL IDLE: {city.name} (pop{city.population}, prod {city.production})")
    for city in cities:
        pills = list(getattr(city, "pillaged_districts", None) or [])
        pillb = list(getattr(city, "pillaged_buildings", None) or [])
        if pills or pillb:
            print(f"  still pillaged: {city.name} -> {pills + pillb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
