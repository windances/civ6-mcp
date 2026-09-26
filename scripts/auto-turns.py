"""Play the routine development turns unattended, and stop the moment a decision stops being routine.

Why this exists: the 100-turn replay has ~40 turns in which the doctrine's answer is "keep doing what
the plan says" - a Builder walks to the next task tile, a city refills its queue, a finished tech
takes the next one on the list. Playing those turn by turn costs an operator round trip each and
burns the session's context on turns that contain no decision, which is exactly the wrong place to
spend it. This runs them, in one connection, and writes the same diary rows the operator writes.

What it will do, and only this:

* dispatch every Builder with moves to the nearest task, URGENT before HIGH before NORMAL, and
  improve when it arrives - `get_builder_tasks` is the source of truth for where the tasks are;
* keep every city's queue non-empty from a fixed per-city list, and refill research/civics from a
  fixed priority list when one completes;
* take the pantheon and the era dedication when they are offered;
* promote Pingala's 研究员 Researcher and Magnus's 给养保障 Provision with governor titles;
* buy a Builder with gold when the treasury passes `--buy-at` (default 320) and one of the four
  cities is short of improvements - the directive's "gold above ~300 with unimproved tiles is
  wasted";
* fortify the military units that are not going anywhere and leave the Scout on automate.

What it will never do: attack, declare war, clear a barbarian camp, move a unit within reach of an
enemy, propose or accept peace, or change a government. **It stops and hands back the moment any
enemy unit is within three tiles of ours or of one of our cities, or `at_war` is true** - that is
where the tactics files apply and where a script has no business deciding.

Usage:
  .venv\\Scripts\\python.exe .tools\\auto-turns.py --turns 5 --dry-run     # orders nothing
  .venv\\Scripts\\python.exe .tools\\auto-turns.py --turns 20
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import importlib.util
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("CIV_MCP_DATA_DIR", str(ROOT / ".civ6-mcp-data"))

from civ_mcp import diary as diary_module  # noqa: E402
from civ_mcp import end_turn as end_turn_module  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

# Research and civics in the order this empire needs them. Eurekas/inspirations are China's ability,
# so a boosted item is preferred over a cheaper unboosted one.
RESEARCH_ORDER = [
    "TECH_MASONRY", "TECH_THE_WHEEL", "TECH_IRON_WORKING", "TECH_CURRENCY",
    "TECH_HORSEBACK_RIDING", "TECH_APPRENTICESHIP", "TECH_ENGINEERING", "TECH_CONSTRUCTION",
    "TECH_MATHEMATICS", "TECH_MACHINERY", "TECH_EDUCATION", "TECH_STIRRUPS",
    "TECH_MILITARY_ENGINEERING", "TECH_CASTLES", "TECH_SAILING",
]
CIVIC_ORDER = [
    "CIVIC_POLITICAL_PHILOSOPHY", "CIVIC_DRAMA_POETRY", "CIVIC_GAMES_RECREATION",
    "CIVIC_MILITARY_TRADITION", "CIVIC_MYSTICISM", "CIVIC_RECORDED_HISTORY", "CIVIC_THEOLOGY",
    "CIVIC_FEUDALISM", "CIVIC_CIVIL_SERVICE", "CIVIC_MERCENARIES", "CIVIC_MEDIEVAL_FAIRES",
    "CIVIC_GUILDS", "CIVIC_DIVINE_RIGHT", "CIVIC_MILITARY_TRAINING", "CIVIC_DEFENSIVE_TACTICS",
]
# Per city, in order. `produce` resolves the category itself; a refusal moves on to the next item.
CITY_PLAN = {
    "西安": ["UNIT_TRADER", "UNIT_BUILDER", "DISTRICT_CAMPUS", "BUILDING_GRANARY",
             "BUILDING_WATER_MILL", "UNIT_ARCHER"],
    "北京": ["BUILDING_GRANARY", "UNIT_BUILDER", "DISTRICT_CAMPUS", "BUILDING_WATER_MILL"],
    "上海": ["BUILDING_GRANARY", "UNIT_BUILDER", "BUILDING_WATER_MILL", "UNIT_ARCHER"],
    "长沙": ["BUILDING_MONUMENT", "UNIT_BUILDER", "BUILDING_GRANARY", "DISTRICT_CAMPUS"],
}
PRIORITY_RANK = {"urgent": 0, "high": 1, "normal": 2}
NEARBY_TILES = 4  # a Builder takes the best priority inside this radius before walking further
PANTHEON = "BELIEF_GODDESS_OF_FESTIVALS"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Runner:
    def __init__(self, gs: GameState, args) -> None:
        self.gs = gs
        self.args = args
        self.log: list[str] = []
        self.targets: dict[int, tuple[int, int]] = {}  # builder unit_index -> assigned task tile

    def say(self, message: str) -> None:
        print(message, flush=True)
        self.log.append(message)

    # --- reads ---------------------------------------------------------------------------------
    async def enemy_near(self) -> tuple[str | None, list[str]]:
        """(reason to hand back, barbarian notes).

        Barbarians are not a reason to hand back - they are always "at war", a galley two tiles off
        the coast cannot take a city, and the directive forbids clearing their camps anyway. A
        **major civilisation's or city-state's** unit inside three tiles is, because that is where
        the tactics files start to apply. Barbarians are still reported, and a barbarian within two
        tiles of a city is a defence decision and does hand back.
        """
        handback: list[str] = []
        notes: list[str] = []
        cities, _ = await self.gs.get_cities()
        city_tiles = {(c.x, c.y) for c in cities}
        try:
            rows = await self.gs.get_threat_scan()
        except Exception as exc:  # noqa: BLE001 - a dead scan must not read as "no enemy"
            return f"threat scan unavailable ({exc})", []
        for row in rows or []:
            owner = str(getattr(row, "owner_name", "") or "")
            barbarian = "arbarian" in owner or "蛮" in owner or getattr(row, "owner_id", 0) == 63
            distance = getattr(row, "distance", 99)
            where = f"{getattr(row, 'unit_type', '?')} ({owner}) at dist {distance}"
            if not barbarian:
                if distance <= 3:
                    handback.append(where)
                continue
            notes.append(where)
            naval = any(word in where.upper() for word in
                        ("GALLEY", "QUADRIREME", "CARAVEL", "FRIGATE", "IRONCLAD", "PRIVATEER",
                         "SHIP", "SUBMARINE", "DESTROYER", "BATTLESHIP"))
            if naval:
                # A barbarian galley can pillage a coastal tile but cannot take a land city, so it
                # is not a hand-back; measured T60-T64, three galleys have been off 上海's coast for
                # five turns doing nothing.
                continue
            if distance <= 2 and any(
                abs(getattr(row, "x", 0) - cx) + abs(getattr(row, "y", 0) - cy) <= 2
                for cx, cy in city_tiles
            ):
                handback.append(f"barbarian threatening a city: {where}")
        return ("; ".join(handback) if handback else None), notes

    # --- orders --------------------------------------------------------------------------------
    async def fill_queues(self, dry: bool) -> list[str]:
        done = []
        cities, _ = await self.gs.get_cities()
        for city in cities:
            if str(city.currently_building) not in ("nothing", "None"):
                continue
            options = await self.gs.list_city_production(city.city_id)
            names = [str(o.item_name) for o in options]
            plan = CITY_PLAN.get(str(city.name), ["UNIT_BUILDER", "BUILDING_GRANARY"])
            for item in plan:
                match = next((o for o in options if str(o.item_name) == item), None)
                if match is None:
                    continue
                if dry:
                    done.append(f"{city.name}: would set {item}")
                    break
                target = None
                if match.category == "DISTRICT":
                    placements = await self.gs.get_district_advisor(city.city_id, match.item_name)
                    spots = [p for p in placements if getattr(p, "x", None) is not None]
                    if not spots:
                        continue
                    target = (spots[0].x, spots[0].y)
                reply = await self.gs.set_city_production(
                    city.city_id, match.category, match.item_name,
                    target[0] if target else None, target[1] if target else None,
                )
                done.append(f"{city.name}: {item} {match.turns}t -> {reply}")
                break
            else:
                done.append(f"{city.name}: NO PLAN ITEM AVAILABLE from {names}")
        return done

    async def advance_research(self, dry: bool) -> list[str]:
        done = []
        tc = await self.gs.get_tech_civics()
        if not getattr(tc, "current_research", None):
            available = {t.tech_type: t for t in tc.available_techs or []}
            for tech in RESEARCH_ORDER:
                if tech in available:
                    done.append(f"research -> {tech}"
                                if dry else f"research -> {tech}: {await self.gs.set_research(tech)}")
                    break
            else:
                done.append(f"research: NOTHING ON THE LIST, available={sorted(available)}")
        if not getattr(tc, "current_civic", None):
            available = {c.civic_type: c for c in tc.available_civics or []}
            for civic in CIVIC_ORDER:
                if civic in available:
                    done.append(f"civic -> {civic}"
                                if dry else f"civic -> {civic}: {await self.gs.set_civic(civic)}")
                    break
            else:
                done.append(f"civic: NOTHING ON THE LIST, available={sorted(available)}")
        return done

    async def take_offers(self, dry: bool) -> list[str]:
        done = []
        try:
            status = await self.gs.get_pantheon_status()
            if not getattr(status, "has_pantheon", True):
                offered = {b.belief_type for b in getattr(status, "available_beliefs", []) or []}
                if PANTHEON in offered:
                    done.append(f"pantheon -> {PANTHEON}"
                                if dry else f"pantheon -> {PANTHEON}: "
                                f"{await self.gs.choose_pantheon(PANTHEON)}")
        except Exception as exc:  # noqa: BLE001
            done.append(f"pantheon read failed: {exc}")
        try:
            dedications = await self.gs.get_dedications()
            if getattr(dedications, "selections_allowed", 0):
                choice = next((c for c in dedications.choices or [] if "SCIENTIFIC" in c.name), None)
                if choice is not None:
                    done.append(f"dedication -> {choice.name}"
                                if dry else f"dedication -> {choice.name}: "
                                f"{await self.gs.choose_dedication(dedication_index=choice.index)}")
        except Exception as exc:  # noqa: BLE001
            done.append(f"dedication read failed: {exc}")
        try:
            govs = await self.gs.get_governors()
            if getattr(govs, "points_available", 0):
                for wanted in ("GOVERNOR_PROMOTION_EDUCATOR_RESEARCHER",
                               "GOVERNOR_PROMOTION_RESOURCE_MANAGER_EXPEDITION"):
                    for gov in govs.appointed or []:
                        options = {p.promotion_type for p in gov.available_promotions or []}
                        if wanted in options:
                            done.append(f"promote {gov.name} -> {wanted}"
                                        if dry else f"promote {gov.name} -> {wanted}: "
                                        f"{await self.gs.promote_governor(gov.governor_type, wanted)}")
                            return done
                if not any(g.governor_type == "GOVERNOR_THE_EDUCATOR" for g in govs.appointed or []):
                    done.append("appoint GOVERNOR_THE_EDUCATOR"
                                if dry else "appoint GOVERNOR_THE_EDUCATOR: "
                                f"{await self.gs.appoint_governor('GOVERNOR_THE_EDUCATOR')}")
        except Exception as exc:  # noqa: BLE001
            done.append(f"governor read failed: {exc}")
        return done

    async def run_builders(self, dry: bool) -> list[str]:
        done = []
        tasks, _ = await self.gs.get_builder_tasks()
        tasks = [t for t in tasks or [] if getattr(t, "x", None) is not None]
        units = await self.gs.get_units()
        builders = [u for u in units if "BUILDER" in str(u.unit_type)]
        if not tasks:
            return done
        for builder in builders:
            if builder.moves_remaining <= 0 or not builder.build_charges:
                continue
            here = next((t for t in tasks if (t.x, t.y) == (builder.x, builder.y)), None)
            if here is not None:
                if dry:
                    done.append(f"builder[{builder.unit_index}] would improve "
                                f"{here.improvement} at ({here.x},{here.y})")
                else:
                    reply = await self.gs.improve_tile(builder.unit_index, here.improvement)
                    done.append(f"builder[{builder.unit_index}] {here.improvement} "
                                f"({here.x},{here.y}) -> {reply}")
                self.targets.pop(builder.unit_index, None)
                continue
            assigned = self.targets.get(builder.unit_index)
            target = next((t for t in tasks if (t.x, t.y) == assigned), None)
            if target is None:
                # Priority decides WHAT gets done; distance decides WHO does it. Strict priority
                # first sent 西安's Builder nine tiles east to the URGENT HORSES pasture - a
                # strategic resource the empire already holds 20 of against a cap of 50 - while the
                # cocoa and banana plantations four tiles away are the tiles that unlock the capital's
                # pop-6 Campus. So: among tasks within NEARBY tiles take the best priority, and only
                # when nothing is near does the builder walk to the distant one. That keeps the
                # doctrine's rule (a Builder that sits idle is worse than one that walks a few turns)
                # without letting a resource-class label outrank the plan.
                claimed = set(self.targets.values())
                candidates = [t for t in tasks if (t.x, t.y) not in claimed]
                if not candidates:
                    continue

                def distance_to(task) -> int:
                    return abs(task.x - builder.x) + abs(task.y - builder.y)

                nearby = [t for t in candidates if distance_to(t) <= NEARBY_TILES]
                pool = nearby or candidates
                target = min(
                    pool,
                    key=lambda t: (
                        PRIORITY_RANK.get(str(t.priority).lower(), 3),
                        distance_to(t),
                    ),
                )
                self.targets[builder.unit_index] = (target.x, target.y)
            if dry:
                done.append(f"builder[{builder.unit_index}] would move toward "
                            f"{target.improvement} ({target.x},{target.y})")
            else:
                reply = await self.gs.move_unit(builder.unit_index, target.x, target.y)
                done.append(f"builder[{builder.unit_index}] -> ({target.x},{target.y}) {reply}")
        return done

    async def park_units(self, dry: bool) -> list[str]:
        done = []
        for unit in await self.gs.get_units():
            if unit.moves_remaining <= 0:
                continue
            kind = str(unit.unit_type)
            if "SCOUT" in kind:
                if not dry:
                    done.append(f"scout -> {await self.gs.automate_explore(unit.unit_index)}")
                continue
            if not unit.combat_strength:
                continue
            if dry:
                done.append(f"would fortify {kind} [{unit.unit_index}]")
            else:
                done.append(f"fortify {kind}: {await self.gs.fortify_unit(unit.unit_index)}")
        return done

    async def maybe_buy(self, dry: bool) -> list[str]:
        if self.args.buy_at <= 0:
            return []
        overview = await self.gs.get_game_overview()
        if (overview.gold or 0) < self.args.buy_at:
            return []
        cities, _ = await self.gs.get_cities()
        # The city with the fewest districts is the one short of tiles and queues.
        city = min(cities, key=lambda c: len(getattr(c, "districts", []) or []))
        if dry:
            return [f"gold {overview.gold:.0f} >= {self.args.buy_at}: would buy a Builder in {city.name}"]
        reply = await self.gs.purchase_item(city.city_id, "UNIT", "UNIT_BUILDER", "YIELD_GOLD")
        return [f"gold {overview.gold:.0f}: Builder in {city.name} -> {reply}"]

    # --- the turn ------------------------------------------------------------------------------
    async def one_turn(self, dry: bool) -> tuple[bool, str, list[str]]:
        """Returns (advanced, note, actions)."""
        overview = await self.gs.get_game_overview()
        turn = overview.turn
        self.say(f"--- T{turn} ---")
        contact, barbarians = await self.enemy_near()
        if barbarians:
            self.say(f"    barbarians in sight (not a hand-back): {'; '.join(barbarians)}")
        if contact:
            return False, f"contact at T{turn}: {contact}", []
        if getattr(overview, "at_war", False):
            return False, f"war at T{turn}", []

        actions: list[str] = []
        actions += await self.fill_queues(dry)
        actions += await self.advance_research(dry)
        actions += await self.take_offers(dry)
        actions += await self.run_builders(dry)
        actions += await self.park_units(dry)
        actions += await self.maybe_buy(dry)
        for line in actions:
            self.say(f"    {line}")

        if dry:
            return True, "dry run", actions

        blocker = await play.preflight_blocker(self.gs)
        if blocker:
            self.say(f"    PREFLIGHT: {blocker}")
        pending = [u for u in await self.gs.get_units() if u.moves_remaining > 0]
        if pending:
            self.say(f"    skip {len(pending)} unit(s) with unspent moves")
            # force=True is this runner's contract, not a shortcut: it never attacks and it
            # hands back the moment an enemy is within three tiles, so an attack left unused
            # here is a unit it has already refused to command. Without the flag the sweep
            # would refuse and the turn would stall.
            report = str(await self.gs.skip_remaining_units(force=True))
            if "UNUSED ATTACK" in report:
                self.say("    WARNING: an attack was discarded by the sweep (see above)")
        result = await end_turn_module.execute_end_turn(self.gs)
        head = str(result).strip().splitlines()[:1]
        self.say(f"    end: {head[0] if head else '(no output)'}")
        failed = [line.strip() for line in str(result).splitlines() if "CHECK FAILED" in line]
        for line in failed:
            self.say(f"    {line}")

        await self.write_diary(turn, actions, failed, overview)
        # `execute_end_turn` returns as soon as the AI phase is done, and the adapter's own read
        # lags inside that frame: measured T64, the end output said "Turn 64 -> 65" while a read
        # immediately afterwards still answered 64, which the runner took for a stall and stopped on.
        # Poll instead.
        after = await self.gs.get_game_overview()
        deadline = 15
        while after.turn == turn and deadline > 0:
            await asyncio.sleep(1.5)
            deadline -= 1
            after = await self.gs.get_game_overview()
        if after.turn == turn:
            return False, f"the turn did not advance past T{turn}", actions
        return True, f"T{turn} -> T{after.turn}", actions

    # --- diary ---------------------------------------------------------------------------------
    async def write_diary(self, turn: int, actions: list[str], failed: list[str], overview) -> None:
        """The same rows the MCP writes, from the same snapshot, with generated reflections.

        The five contract fields are factual here rather than interpretive - this runner writes the
        row for a turn whose decisions were made by the plan, and an interpretation of a turn nobody
        reasoned about would be worse than an inventory of it.
        """
        civ, seed = await self.gs.get_game_identity()
        path = diary_module.diary_path(civ, seed)
        cities_path = path.with_name(f"{path.stem}_cities.jsonl")
        snapshot = await self.gs.get_diary_snapshot()
        pid_line = await self.gs.execute_lua("print(Game.GetLocalPlayer())", "gamecore")
        local_pid = int(pid_line.strip().splitlines()[-1])
        game_id = f"{civ}_{seed}"
        stamp = datetime.now(timezone.utc).isoformat()
        cities, _ = await self.gs.get_cities()
        city_line = "; ".join(
            f"{c.name} pop{c.population} {c.currently_building}({c.production_turns_left}t)" for c in cities
        )
        reflections = {
            "tactical": f"T{turn} played by .tools/auto-turns.py (coarse development mode). "
                        + ("; ".join(actions) if actions else "no orders were needed this turn"),
            "strategic": f"T{turn}: {overview.num_cities} cities, pop {overview.total_population}, "
                         f"score {overview.score}, science {overview.science_yield}, culture "
                         f"{overview.culture_yield}, gold {overview.gold:.0f} "
                         f"({overview.gold_per_turn:+.1f}/t), faith {overview.faith}, military "
                         f"{len([u for u in await self.gs.get_units() if u.combat_strength])} units; "
                         f"{city_line}",
            "tooling": f"auto-turns.py turn {turn}: "
                       + ("no refusals" if not any("Error" in a or "CANNOT" in a for a in actions)
                          else "; ".join(a for a in actions if "Error" in a or "CANNOT" in a)),
            "planning": "Hold the development line: builders walk the task list URGENT -> HIGH -> "
                        "NORMAL, every city's queue stays filled from its plan, research follows "
                        "RESEARCH_ORDER and civics CIVIC_ORDER, a Builder is bought above "
                        f"{self.args.buy_at} gold. Science has to come from 西安's Campus at pop 6.",
            "hypothesis": "The runner hands back the moment an enemy is within three tiles or a war "
                          "starts, which is where the tactics files take over; until then the "
                          f"measurable expectation is that {PANTHEON} keeps culture rising and the "
                          "Campus in 西安 lands within ten turns of pop 6.",
        }
        rows: list[dict] = []
        for player in snapshot.players:
            row = dataclasses.asdict(player)
            row.update(v=1, turn=turn, game=game_id, timestamp=stamp)
            if player.pid == local_pid:
                agent = snapshot.agent
                row.update(
                    is_agent=True,
                    diplo_states=agent.diplo_states,
                    suzerainties=agent.suzerainties,
                    envoys_available=agent.envoys_available,
                    envoys_sent=agent.envoys_sent,
                    gp_points=agent.gp_points,
                    governors=agent.governors,
                    trade_routes={
                        "capacity": agent.trade_capacity,
                        "active": agent.trade_active,
                        "domestic": agent.trade_domestic,
                        "international": agent.trade_international,
                    },
                    reflections=reflections,
                    agent_client="script",
                    agent_model="auto-turns",
                )
            rows.append(row)
        city_rows = []
        for city in snapshot.cities:
            row = dataclasses.asdict(city)
            row.update(v=1, turn=turn, game=game_id, timestamp=stamp)
            city_rows.append(row)
        _append(path, rows)
        _append(cities_path, city_rows)


def _append(path: pathlib.Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n")


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--turns", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true", help="say what it would do, order nothing")
    ap.add_argument("--buy-at", type=float, default=320.0,
                    help="buy a Builder in the weakest city at or above this treasury (0 = never)")
    args = ap.parse_args()

    global play
    play = load_module("play_turn", "play-turn.py")

    conn = GameConnection()
    await conn.connect()
    gs = GameState(conn)
    runner = Runner(gs, args)
    try:
        for _ in range(args.turns):
            advanced, note, _ = await runner.one_turn(args.dry_run)
            runner.say(f"    {note}")
            if not advanced:
                break
    finally:
        await conn.disconnect()

    out = ROOT / ".tools" / "_auto-turns.log"
    out.write_text("\n".join(runner.log) + "\n", encoding="utf-8")
    print(f"\nwrote {out} ({len(runner.log)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
