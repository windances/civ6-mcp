"""One full re-orientation read of the live game, for a rollback or a cold start.

The orchestrator skill is explicit that after a rollback **every fact is stale** and has to be
rebuilt from the game before any action: cities, units, the map around both, tech and civics,
policies, diplomacy, resources, governors, routes. Doing that through five separate scripts is how
one of them gets skipped; this prints the whole canonical snapshot in one connection.

**Compact by default.** The raw dataclass dump is 20k+ characters per call (governor promotion
descriptions alone are worse than useless at this cadence), and a 100-turn session reads this many
times; `--full` prints the raw form when a field is genuinely in question.

Read-only. It issues no orders.

Usage:
  .venv\\Scripts\\python.exe .tools\\orient.py
  .venv\\Scripts\\python.exe .tools\\orient.py --only diplomacy,units
  .venv\\Scripts\\python.exe .tools\\orient.py --full --only governors
  .venv\\Scripts\\python.exe .tools\\orient.py --maps --radius 2
"""

from __future__ import annotations

import argparse
import asyncio
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("CIV_MCP_DATA_DIR", str(ROOT / ".civ6-mcp-data"))

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402
from civ_mcp.narrate import narrate_map  # noqa: E402

SECTIONS: list[tuple[str, str, str]] = [
    ("overview", "GAME OVERVIEW", "get_game_overview"),
    ("units", "UNITS", "get_units"),
    ("cities", "CITIES", "get_cities"),
    ("tech", "TECH / CIVICS", "get_tech_civics"),
    ("policies", "POLICIES", "get_policies"),
    ("diplomacy", "DIPLOMACY", "get_diplomacy"),
    ("resources", "EMPIRE RESOURCES", "get_empire_resources"),
    ("governors", "GOVERNORS", "get_governors"),
    ("routes", "TRADE ROUTES", "get_trade_routes"),
    ("builtasks", "BUILDER TASKS", "get_builder_tasks"),
    ("civstates", "CITY-STATES", "get_city_states"),
    ("victory", "VICTORY / DEMOGRAPHICS", "get_victory_progress"),
    ("religion", "RELIGION", "get_religion_status"),
    ("greatpeople", "GREAT PEOPLE", "get_great_people"),
    ("pantheon", "PANTHEON", "get_pantheon_status"),
    ("notifs", "NOTIFICATIONS", "get_notifications"),
]


def raw(label: str, value) -> None:
    """The old dump: every non-empty dataclass field. For when a number is in dispute."""
    print(f"\n=== {label} (raw) ===")
    items = value if isinstance(value, list) else [value]
    if not items:
        print("  (empty)")
    for item in items:
        if hasattr(item, "__dataclass_fields__"):
            for field in item.__dataclass_fields__:
                val = getattr(item, field, None)
                if val not in (None, [], {}, ""):
                    print(f"  {field}: {val}")
            print("  --")
        else:
            print(f"  {item}")


def compact(key: str, value) -> None:
    print(f"\n=== {dict((k, l) for k, l, _ in SECTIONS)[key]} ===")
    if value is None:
        print("  (none)")
        return

    if key == "overview":
        fields = ("turn", "gold", "gold_per_turn", "gold_income", "total_maintenance", "science_yield",
                  "culture_yield", "faith", "current_research", "current_civic", "num_cities",
                  "score", "era_name", "era_score", "era_dark_threshold", "era_golden_threshold",
                  "total_population", "diplomatic_favor", "favor_per_turn", "explored_land",
                  "total_land", "religions_founded", "religions_max", "unit_breakdown")
        print("  " + " | ".join(f"{f}={getattr(value, f)}" for f in fields
                                if getattr(value, f, None) is not None))
        return

    if key == "units":
        for u in value or []:
            bits = [f"[{u.unit_index}] {u.unit_type} ({u.x},{u.y})",
                    f"hp{u.health}/{u.max_health}", f"mv{u.moves_remaining}/{u.max_moves}"]
            if u.combat_strength:
                bits.append(f"cs{u.combat_strength}")
            if u.ranged_strength:
                bits.append(f"rs{u.ranged_strength}")
            if u.build_charges:
                bits.append(f"charges{u.build_charges}")
            if u.needs_promotion:
                bits.append("PROMOTION")
            if u.can_upgrade:
                bits.append(f"UPGRADE->{u.upgrade_cost}g")
            print("  " + " ".join(str(b) for b in bits))
        if not value:
            print("  (no units)")
        return

    if key == "cities":
        cities, notes = value
        for c in cities:
            # getattr with a default throughout: the CityInfo field set is not stable across reads
            # (a compact printer that assumed `amenities_needed` killed the whole cities section on
            # the first run), and a missing display field is not worth losing the section over.
            def field(name, default="-"):
                return getattr(c, name, default)

            print(f"  {field('name'):<5} ({field('x')},{field('y')}) pop{field('population')} "
                  f"prod{field('production')} food+{field('food_surplus')} "
                  f"grow{field('turns_to_grow')}t house{field('housing')} "
                  f"amen{field('amenities')} sci{field('science')} cul{field('culture')} "
                  f"gold{field('gold')} | {field('currently_building')} "
                  f"{field('production_turns_left')}t | loyal {field('loyalty')}/{field('loyalty_max')} "
                  f"{field('loyalty_outcome')}")
            if field("districts", []):
                print(f"        districts: {', '.join(str(d) for d in c.districts)}")
            if field("buildings", []):
                print(f"        buildings: {', '.join(str(b) for b in c.buildings)}")
            if field("pillaged_districts", []) or field("pillaged_buildings", []):
                print(f"        PILLAGED d: {field('pillaged_districts')} "
                      f"b: {field('pillaged_buildings')}")
            if field("attack_targets", []):
                print(f"        city strike targets: {field('attack_targets')}")
        for note in notes or []:
            if "tiles" in str(note):
                print(f"  {note}")
        return

    if key == "tech":
        print(f"  research: {value.current_research} {value.current_research_turns}t | "
              f"civic: {value.current_civic} {value.current_civic_turns}t | "
              f"done: {value.completed_tech_count} techs, {value.completed_civic_count} civics")
        print("  available techs: " + ", ".join(
            f"{t.tech_type.replace('TECH_','')}({t.turns}t{',boost' if t.boosted else ''})"
            for t in value.available_techs or []))
        print("  available civics: " + ", ".join(
            f"{c.civic_type.replace('CIVIC_','')}({c.turns}t{',boost' if c.boosted else ''})"
            for c in value.available_civics or []))
        return

    if key == "policies":
        print(f"  {value.government_name} ({value.government_type})")
        for slot in value.slots or []:
            print(f"    {slot.slot_type.replace('SLOT_',''):<10} {slot.current_policy_name or '-'}")
        print("  available: " + ", ".join(
            f"{p.name}[{p.slot_type.replace('SLOT_','')[:4]}]" for p in value.available_policies or []))
        return

    if key == "diplomacy":
        met = [d for d in value or [] if getattr(d, "has_met", False)]
        if not met:
            print(f"  no civilizations met (of {len(value or []) - 1} rivals)")
        for d in met:
            print(f"  p{d.player_id} {d.civ_name}/{d.leader_name} state={d.diplomatic_state} "
                  f"war={d.is_at_war} rel={d.relationship_score} griev={d.grievances} "
                  f"mil={d.military_strength} cities={d.num_cities}")
        return

    if key == "resources":
        stock, owned, nearby = value
        print("  stock: " + (", ".join(
            f"{s.name} {s.amount}/{s.cap}(+{s.per_turn})" for s in stock or []) or "none"))
        unimproved = [r for r in owned or [] if not r.improved]
        print("  owned unimproved: " + (", ".join(
            f"{r.name}@({r.x},{r.y})" for r in unimproved) or "none"))
        print(f"  owned improved: {sum(1 for r in owned or [] if r.improved)}")
        return

    if key == "governors":
        print(f"  titles available={value.points_available} spent={value.points_spent}")
        for g in value.appointed or []:
            promos = ", ".join(str(p.name) for p in getattr(g, "promotions", []) or [])
            offers = ", ".join(str(p.name) for p in g.available_promotions or [])
            print(f"  {g.name} -> {g.assigned_city_name} "
                  f"{'established' if g.is_established else f'{g.turns_to_establish}t to establish'}"
                  + (f" | has: {promos}" if promos else "")
                  + (f" | can take: {offers}" if offers else ""))
        if value.available_to_appoint:
            print("  can appoint: " + ", ".join(
                f"{g.name}({g.governor_type.replace('GOVERNOR_THE_','').lower()})"
                for g in value.available_to_appoint))
        return

    if key == "routes":
        print(f"  capacity={value.capacity} active={value.active_count} ghost={value.ghost_count}"
              + ("   <-- IDLE ROUTE" if value.capacity > value.active_count else ""))
        return

    if key == "builtasks":
        tasks, _ = value
        for t in tasks or []:
            res = f" [{t.resource}]" if t.resource else ""
            print(f"  {t.priority.upper():<6} {t.improvement.replace('IMPROVEMENT_',''):<12} "
                  f"({t.x},{t.y}) {t.city_name}{res}")
        return

    if key == "civstates":
        print(f"  envoy tokens={value.tokens_available}")
        for s in value.city_states or []:
            print(f"  {s.name} {s.city_state_type} envoys={s.envoys_sent} "
                  f"suzerain={s.suzerain_name}")
        return

    if key == "victory":
        for p in value.players or []:
            print(f"  p{p.player_id} {p.name} score={p.score} sci_vp={p.science_vp} "
                  f"dip_vp={p.diplomatic_vp} mil={p.military_strength} techs={p.techs_researched} "
                  f"civics={p.civics_completed} cities={p.num_cities} sci={p.science_yield} "
                  f"cul={p.culture_yield} gold={p.gold_yield}")
        print(f"  capitals held: {value.capitals_held} | religion majority: {value.religion_majority}")
        for name, entry in (value.demographics or {}).items():
            print(f"  {name:<12} rank {entry.rank} ours {entry.value} best {entry.best} "
                  f"avg {entry.average} worst {entry.worst}")
        print(f"  enabled: {sorted(value.enabled_victories or [])}")
        return

    if key == "religion":
        print(f"  summary: {value.summary}")
        print("  our cities: " + ", ".join(
            f"{c.city_name}={c.majority_religion}" for c in value.cities or []))
        return

    if key == "greatpeople":
        for g in value or []:
            print(f"  {g.class_name:<8} {g.individual_name:<14} pts {g.player_points}/{g.cost} "
                  f"{'CAN RECRUIT' if g.can_recruit else ''} gold {g.gold_cost} faith {g.faith_cost}")
        return

    if key == "pantheon":
        print(f"  has_pantheon={value.has_pantheon}")
        for field in value.__dataclass_fields__:
            if field == "has_pantheon":
                continue
            val = getattr(value, field, None)
            if val not in (None, [], {}, ""):
                print(f"  {field}: {val}")
        return

    if key == "notifs":
        for n in value or []:
            print(f"  {getattr(n, 'message', n)}")
        if not value:
            print("  (none)")
        return

    print(f"  {value}")


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--radius", type=int, default=1, help="map radius around cities and units")
    ap.add_argument("--only", help="comma-separated section keys")
    ap.add_argument("--full", action="store_true", help="raw dataclass dump instead of the summary")
    ap.add_argument("--maps", action="store_true", help="include the narrated map (verbose)")
    args = ap.parse_args()

    wanted = {part.strip() for part in args.only.split(",")} if args.only else None

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    try:
        for key, label, method in SECTIONS:
            if wanted and key not in wanted:
                continue
            try:
                result = await getattr(gs, method)()
            except Exception as exc:  # noqa: BLE001 - one dead query must not kill the read
                print(f"\n=== {label} ===\n  UNAVAILABLE: {type(exc).__name__}: {exc}")
                continue
            if args.full:
                raw(label, result)
            else:
                try:
                    compact(key, result)
                except Exception as exc:  # noqa: BLE001 - a printer bug must not hide the data
                    print(f"  SUMMARY FAILED ({type(exc).__name__}: {exc}); raw follows")
                    raw(label, result)

        if args.maps:
            anchors: list[tuple[int, int, str]] = []
            try:
                for city in (await gs.get_cities())[0]:
                    anchors.append((city.x, city.y, f"city {city.name}"))
            except Exception:  # noqa: BLE001
                pass
            try:
                for unit in await gs.get_units():
                    anchors.append((unit.x, unit.y, f"unit {unit.unit_type}"))
            except Exception:  # noqa: BLE001
                pass
            for x, y, label in anchors:
                try:
                    area = await gs.get_map_area(x, y, radius=args.radius)
                except Exception as exc:  # noqa: BLE001
                    print(f"\n=== MAP around {label} ({x},{y}) ===\n  UNAVAILABLE: {exc}")
                    continue
                print(f"\n=== MAP around {label} ({x},{y}) ===")
                try:
                    print(narrate_map(area))
                except Exception:  # noqa: BLE001 - the narration is a convenience
                    print(area)
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
