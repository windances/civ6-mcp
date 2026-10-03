"""Every factor that is holding production down, measured across every city, ranked.

`production-recovery.py` answers "which queues are empty and which districts are pillaged". That is
two factors out of six. Measured 2026-10-04 in china--1894041591: after fixing those two the empire
still had **9 of its 12 power-demanding cities unpowered**, and only **one** of the nine was
unpowered because of pillage - the other eight had simply never been given a power source. A report
that names the one city it looked at is how the other eight go unnoticed.

So this measures all six, per city, and sorts by **how much production each city is losing** rather
than by how interesting its story is:

  1. **idle** - the queue is empty. The city produces nothing at all this turn.
  2. **pillaged** - a district or building is down. For an Industrial Zone that is the whole
     production chain, and the power it was supplying.
  3. **unpowered** - `power_required > 0` and nothing supplies it. A building that needs power
     yields nothing while it is unpowered, so this is the Research Lab, the Factory and the
     Stock Exchange silently switched off.
  4. **amenities** - `amenities - amenities_needed < 0`. Negative amenities apply a percentage
     penalty to *every* yield in the city, so it is a production loss like any other.
  5. **housing** - `housing - population <= 1`. Growth stops; growth is what buys district slots
     (`districts <= floor(pop / 3)`), so the loss is deferred rather than absent.
  6. **food** - `food_surplus <= 0`. Same mechanism, one step earlier.

    python .tools/production-audit.py            # the ranked bill
    python .tools/production-audit.py --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

IDLE = {"", "NONE", "NOTHING", "nothing"}

# Districts the game exempts from the `floor(pop / 3)` rule, and the ones that are pure
# production. Kept as names rather than indices because the save prints type names.
EXEMPT_DISTRICTS = {"DISTRICT_GOVERNMENT", "DISTRICT_AQUEDUCT"}
PRODUCTION_DISTRICTS = {
    "DISTRICT_INDUSTRIAL_ZONE",
    "DISTRICT_ENCAMPMENT",
    "DISTRICT_HARBOR",
    "DISTRICT_COMMERCIAL_HUB",
}
# Buildings that are production itself, or that need power and therefore yield nothing without it.
PRODUCTION_BUILDINGS = {
    "BUILDING_WORKSHOP",
    "BUILDING_FACTORY",
    "BUILDING_COAL_POWER_PLANT",
    "BUILDING_OIL_POWER_PLANT",
    "BUILDING_NUCLEAR_POWER_PLANT",
    "BUILDING_POWER_PLANT",
    "BUILDING_SHIPYARD",
    "BUILDING_SEAPORT",
    "BUILDING_STOCK_EXCHANGE",
    "BUILDING_BARRACKS",
    "BUILDING_ARMORY",
    "BUILDING_MILITARY_ACADEMY",
    "BUILDING_RESEARCH_LAB",
}


def short(name: str) -> str:
    return str(name).replace("DISTRICT_", "").replace("BUILDING_", "").replace("UNIT_", "")


@dataclass
class CityAudit:
    name: str
    x: int
    y: int
    pop: int
    production: float
    science: float
    gold: float
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    currently_building: str = ""
    production_turns_left: int = 0
    # The measure everything is ranked by: what this city's production is currently missing.
    production_at_risk: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.problems


def audit_city(city) -> CityAudit:
    row = CityAudit(
        name=city.name,
        x=city.x,
        y=city.y,
        pop=int(city.population),
        production=float(city.production),
        science=float(city.science),
        gold=float(city.gold),
        currently_building=str(getattr(city, "currently_building", "") or ""),
        production_turns_left=int(getattr(city, "production_turns_left", 0) or 0),
    )
    pills_d = [short(d) for d in (city.pillaged_districts or [])]
    pills_b = [short(b) for b in (city.pillaged_buildings or [])]

    # 1. An empty queue is total loss for the turn, and it is the largest single number here.
    building = str(getattr(city, "currently_building", "") or "").strip()
    turns_left = int(getattr(city, "production_turns_left", 0) or 0)
    if building in IDLE or turns_left <= 0:
        row.problems.append("idle: queue empty, producing nothing this turn")
        row.production_at_risk += row.production

    # 2. Pillaged. A down Industrial Zone takes the production district *and* the power with it.
    if pills_d or pills_b:
        detail = ", ".join(pills_d + pills_b)
        row.problems.append(f"pillaged: {detail}")
        lost = sum(
            1
            for b in (city.pillaged_buildings or [])
            if b in PRODUCTION_BUILDINGS or b.replace("BUILDING_", "BUILDING_") in PRODUCTION_BUILDINGS
        )
        row.production_at_risk += row.production * (0.25 * lost + (0.35 if pills_d else 0.0))

    # 3. Power. Only cities that demand it can lose anything to it.
    required = float(getattr(city, "power_required", -1) or -1)
    if required > 0 and str(getattr(city, "power_fully_powered", "")) != "yes":
        free = float(getattr(city, "power_free", 0) or 0)
        temp = float(getattr(city, "power_temporary", 0) or 0)
        row.problems.append(f"unpowered: needs {required}, has free {free} + temporary {temp}")
        # A powered building that cannot run yields nothing, so the loss scales with the demand.
        row.production_at_risk += row.production * min(0.5, 0.08 * required)
        row.notes.append("power")
    elif required > 0:
        row.notes.append(f"powered ({required})")

    # 4. Amenities: a percentage penalty on every yield in the city.
    amenities = int(getattr(city, "amenities", 0) or 0)
    needed = int(getattr(city, "amenities_needed", 0) or 0)
    if needed > 0 and amenities - needed < 0:
        gap = amenities - needed
        row.problems.append(f"amenities: {amenities} against a demand of {needed} ({gap:+d})")
        row.production_at_risk += row.production * min(0.30, 0.05 * abs(gap))

    # 5/6. Housing and food. Growth is the district plan, so a stalled city loses slots later.
    housing = float(getattr(city, "housing", 0) or 0)
    if housing - row.pop <= 1:
        row.problems.append(f"housing: {housing:.0f} against pop {row.pop} - growth stopped")
        row.production_at_risk += row.production * 0.08
    surplus = float(getattr(city, "food_surplus", 0) or 0)
    if surplus <= 0:
        row.problems.append(f"food: surplus {surplus:+.1f}/t - starving or stalled")
        row.production_at_risk += row.production * 0.08

    # District slots: a free slot nobody is using is a production multiplier not taken.
    districts = [d for d in (city.districts or []) if d not in EXEMPT_DISTRICTS]
    slots = max(0, row.pop // 3 - len(districts))
    if slots > 0:
        row.notes.append(f"{slots} free district slot(s)")
        row.production_at_risk += row.production * 0.05 * slots

    unimproved = list(getattr(city, "unimproved_resources", None) or [])
    broke = list(getattr(city, "pillaged_improvements", None) or [])
    if unimproved:
        row.notes.append(f"{len(unimproved)} unimproved resource tile(s)")
    if broke:
        row.notes.append(f"{len(broke)} pillaged improvement tile(s)")
    return row


POWER_BUILDINGS = (
    "BUILDING_COAL_POWER_PLANT",
    "BUILDING_OIL_POWER_PLANT",
    "BUILDING_NUCLEAR_POWER_PLANT",
    "BUILDING_POWER_PLANT",
)
HOUSING_BUILDINGS = ("BUILDING_SEWER", "BUILDING_GRANARY", "BUILDING_WATER_MILL")
HOUSING_DISTRICTS = ("DISTRICT_AQUEDUCT", "DISTRICT_NEIGHBORHOOD")
SLOT_DISTRICTS = (
    "DISTRICT_INDUSTRIAL_ZONE",
    "DISTRICT_ENCAMPMENT",
    "DISTRICT_COMMERCIAL_HUB",
    "DISTRICT_HARBOR",
    "DISTRICT_CAMPUS",
)


def choose_for(row: CityAudit, options: list):
    """The one item that answers a city's highest-ranked factor, or None.

    The order is the directive's: a repair first (the district or building is already ours and its
    yields are simply switched off), then power, then the growth factors - because a powered
    building that cannot run and a city that cannot grow are both production losses, and the
    growth one is the slower of the two to fix.
    """

    def pick(names):
        for name in names:
            found = next((o for o in options if o.item_name == name), None)
            if found is not None:
                return found
        return None

    problems = " ".join(row.problems)
    if "pillaged" in problems:
        repair = pick([o.item_name for o in options if o.is_repair])
        if repair is None:
            repair = next((o for o in options if o.is_repair), None)
        if repair is not None:
            return repair
    if "unpowered" in problems:
        found = pick(POWER_BUILDINGS) or pick(("DISTRICT_INDUSTRIAL_ZONE",))
        if found is not None:
            return found
    if "housing" in problems:
        found = pick(HOUSING_BUILDINGS) or pick(HOUSING_DISTRICTS)
        if found is not None:
            return found
    if "food" in problems:
        found = pick(("BUILDING_GRANARY", "BUILDING_WATER_MILL")) or pick(HOUSING_DISTRICTS)
        if found is not None:
            return found
    if any("free district slot" in n for n in row.notes):
        found = pick(SLOT_DISTRICTS)
        if found is not None:
            return found
    return None


def redirect_is_worth_it(row: CityAudit) -> bool:
    """Whether losing the hammers already in this city's queue is worth the fix.

    Only the two factors that switch yields **off right now** qualify: an unpowered building yields
    nothing, and a pillaged one yields nothing. Housing and food are *deferred* - a capped city
    stops growing, which costs district slots several turns from now - and they are not worth
    cancelling a build that is nearly finished, or a Campus that is a yield in its own right.

    Measured 2026-10-04, the first version of this rule ranked housing above everything but pillage
    and replaced, in five cities at once, a 3-turn Research Lab, a 3-turn Campus, a 38-turn Campus,
    a 30-turn Entertainment Complex and a 65-turn Campus with Granaries and Sewers. That is a
    science loss bought with nothing.
    """
    problems = " ".join(row.problems)
    if "unpowered" not in problems and "pillaged" not in problems:
        return False
    return row.production_turns_left > 3


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="queue, in every IDLE city, the item that answers its highest-ranked factor",
    )
    ap.add_argument(
        "--redirect",
        action="store_true",
        help="with --apply, also replace a queue whose current item answers none of the city's "
             "factors - the hammers in flight are the price of the fix",
    )
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    cities, _ = await gs.get_cities()
    rows = [audit_city(c) for c in cities]

    broken = sorted([r for r in rows if not r.ok], key=lambda r: -r.production_at_risk)
    clean = [r for r in rows if r.ok]

    print(f"=== {len(rows)} cities, {len(broken)} with something holding production down ===")
    for r in broken:
        print(f"\n  {r.name:<10} ({r.x},{r.y}) pop{r.pop:<3} prod {r.production:>5.1f} "
              f"sci {r.science:>5.1f}   at risk ~{r.production_at_risk:.1f}")
        print(f"      building  {r.currently_building} ({r.production_turns_left}t)")
        for p in r.problems:
            print(f"      - {p}")
        for n in r.notes:
            print(f"      . {n}")
    if clean:
        print(f"\n=== {len(clean)} city/cities with none of the six ===")
        for r in sorted(clean, key=lambda r: -r.production):
            print(f"  {r.name:<10} prod {r.production:>5.1f}   {', '.join(r.notes) or '-'}")

    # The empire-level bill, grouped by factor, which is how the work is actually batched.
    print("\n=== by factor ===")
    factors = {
        "idle queue": [r.name for r in rows if any(p.startswith("idle") for p in r.problems)],
        "pillaged": [r.name for r in rows if any(p.startswith("pillaged") for p in r.problems)],
        "unpowered": [r.name for r in rows if any(p.startswith("unpowered") for p in r.problems)],
        "amenities": [r.name for r in rows if any(p.startswith("amenities") for p in r.problems)],
        "housing": [r.name for r in rows if any(p.startswith("housing") for p in r.problems)],
        "food": [r.name for r in rows if any(p.startswith("food") for p in r.problems)],
        "free district slot": [r.name for r in rows if any("free district slot" in n for n in r.notes)],
    }
    for label, names in factors.items():
        print(f"  {label:<20} {len(names):>2}  {', '.join(names) if names else '-'}")

    if args.apply:
        by_name = {c.name: c for c in cities}
        print("\n=== applying: the top-ranked factor, in every idle city ===")
        for row in broken:
            city = by_name[row.name]
            building = str(getattr(city, "currently_building", "") or "").strip()
            turns_left = int(getattr(city, "production_turns_left", 0) or 0)
            if building not in IDLE and turns_left > 0 and not args.redirect:
                continue  # a useful build already in flight: do not throw its hammers away
            if args.redirect and not redirect_is_worth_it(row):
                continue
            options = await gs.list_city_production(city.city_id)
            pick = choose_for(row, options)
            if pick is None:
                print(f"  {row.name}: nothing on offer answers its factors - look by hand")
                continue
            if args.redirect and pick.item_name == building:
                continue  # already building the right thing
            out = await gs.set_city_production(
                city.city_id,
                pick.category,
                pick.item_name,
                target_x=pick.repair_x,
                target_y=pick.repair_y,
            )
            if "MISSING_COORDS" in str(out):
                print(f"  {row.name}: {pick.item_name} wants a tile ({str(out).splitlines()[0][:70]})")
                continue
            was = f"{building} ({turns_left}t)" if building not in IDLE else "idle"
            print(f"  {row.name:<10} {was:<32} -> {pick.item_name} ({pick.turns}t)   "
                  f"[{row.problems[0][:40]}]")

    if args.json:
        print(json.dumps(
            [
                {**r.__dict__, "ok": r.ok}
                for r in sorted(rows, key=lambda r: -r.production_at_risk)
            ],
            ensure_ascii=False,
            indent=2,
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
