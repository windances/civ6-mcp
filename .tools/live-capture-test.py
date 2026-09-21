"""Live test of the city-capture fix, against the running game.

Offline tests can only prove the shape of the Lua. This runs the real thing against FireTuner:

    python .tools/live-capture-test.py                 # status + what the turn result would say
    python .tools/live-capture-test.py --save AutoSave_0123   # load a save first (opt in)
    python .tools/live-capture-test.py --capture       # order the capture move if one is pending
    python .tools/live-capture-test.py --attack 1703949 54 40  # attack a city tile with no garrison

What it prints, in order: the game status, the capture scan (per visible enemy city: HP pool,
walls, melee-class units adjacent / within two), the check metrics the turn result uses, the
`TAKE THE CITY` block, and the rules that would fail this turn. With `--capture` it then finds
the adjacent melee unit, orders it onto the city tile and re-runs the scan to show the city is
gone from the enemy list.

Nothing here calls `end_turn`, so no autosave is written and the game's own save files are never
modified. Loading a save is the one change it can make, and only with --save.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import game_launcher as gl  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

CHECKS = pathlib.Path("prompts/checks/turn-checks.md")


def distances_lua(city_x: int, city_y: int) -> str:
    """The game's own distance from each of our units to one tile."""
    return f"""
local me = Game.GetLocalPlayer()
for _, u in Players[me]:GetUnits():Members() do
    local ux, uy = u:GetX(), u:GetY()
    if ux ~= -9999 then
        local e = GameInfo.Units[u:GetType()]
        print("UNIT_DIST|" .. u:GetID() .. "|" .. (e and e.UnitType or "?") .. "|" .. ux .. "," .. uy
            .. "|" .. Map.GetPlotDistance(ux, uy, {city_x}, {city_y})
            .. "|moves:" .. u:GetMovesRemaining())
    end
end
print("---END---")
"""


async def unit_distances(gs: GameState, city_x: int, city_y: int) -> list[dict]:
    lines = await gs.conn.execute_write(distances_lua(city_x, city_y))
    out = []
    for line in lines:
        if not line.startswith("UNIT_DIST|"):
            continue
        parts = line.split("|")
        try:
            x_str, y_str = parts[3].split(",")
            out.append(
                {
                    "id": int(parts[1]),
                    "type": parts[2],
                    "x": int(x_str),
                    "y": int(y_str),
                    "dist": int(parts[4]),
                    "moves": float(parts[5].split(":", 1)[1]),
                }
            )
        except (IndexError, ValueError):
            continue
    return out


def visible_cities_lua() -> str:
    """Every city we can see, whoever owns it, with its HP pool and garrison count."""
    return """
local me = Game.GetLocalPlayer()
local pVis = PlayersVisibility[me]
local pDiplo = Players[me]:GetDiplomacy()
for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
        local war = false
        pcall(function() war = pDiplo:IsAtWarWith(pid) end)
        pcall(function()
            for _, c in Players[pid]:GetCities():Members() do
                local cx, cy = c:GetX(), c:GetY()
                if pVis:IsVisible(cx, cy) then
                    local hp, maxhp = 0, 0
                    local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
                    for _, d in c:GetDistricts():Members() do
                        if d:GetType() == ccIdx then
                            maxhp = d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0
                            hp = maxhp - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                            break
                        end
                    end
                    local garrison = 0
                    local stack = Map.GetUnitsAt(cx, cy)
                    if stack then
                        for _ in stack:Units() do garrison = garrison + 1 end
                    end
                    local owner = "player " .. pid
                    pcall(function()
                        local cfg = PlayerConfigurations[pid]
                        owner = cfg and Locale.Lookup(cfg:GetCivilizationShortDescription()) or owner
                    end)
                    print("VISIBLE_CITY|" .. pid .. "|" .. owner .. "|" .. Locale.Lookup(c:GetName())
                        .. "|" .. cx .. "," .. cy .. "|hp:" .. hp .. "/" .. maxhp
                        .. "|garrison:" .. garrison .. "|war:" .. tostring(war))
                end
            end
        end)
    end
end
print("---END---")
"""


async def report(gs: GameState, turn: int) -> list:
    units = await et._units_for_checks(gs, turn)
    rows = await gs.capture_readiness()
    print(f"\n=== capture scan: {len(rows)} enemy cit(ies) in sight ===")
    for row in rows:
        state = "DOWN" if row.down else f"{row.hp}/{row.max_hp}"
        walls = f"walls {row.wall_hp}/{row.wall_max}" if row.wall_max else "walls none"
        print(
            f"  {row.city_name}@({row.x},{row.y}): {state}, {walls}, "
            f"melee adjacent {row.melee_adjacent} / within 2 {row.melee_within_2}"
            + (f" ({row.melee_unit})" if row.melee_unit else "")
            + (" <- TAKEABLE" if row.takeable else "")
        )
    if not rows:
        print("  (none: no enemy city is both visible and at war)")

    metrics = await et._contact_metrics(gs, turn, units)
    keys = ("enemy_cities_seen", "downed_enemy_cities", "capture_ready", "enemy_city_hp_min")
    print("=== check metrics (turn result) ===")
    print("  " + ", ".join(f"{k}={metrics.get(k)}" for k in keys))
    print(
        "  "
        + ", ".join(
            f"{k}={metrics.get(k)}"
            for k in ("siege_units", "siege_exposed", "enemies_within_2", "unused_attacks",
                      "attacks_this_turn", "garrisoned_units", "cities_over_garrison")
        )
    )

    print("=== TAKE THE CITY block ===")
    print(et._capture_event(rows, turn) or "  (not printed: no enemy city at 0 HP)")

    run = turn_checks.run_checks(
        CHECKS.read_text(encoding="utf-8"),
        turn_checks.CheckContext(turn=turn, units=units, metrics=metrics, researched=frozenset()),
    )
    print("=== rules failing this turn ===")
    print("  " + (", ".join(sorted(run.failing_ids)) or "none"))
    for check, _reason in run.failures:
        if check.check_id == "take-the-city":
            print("  take-the-city message: " + check.message.split(".")[0] + ".")
    return rows


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", default=None, help="load this save before testing (opt in)")
    ap.add_argument("--capture", action="store_true", help="order the capture move if one is pending")
    ap.add_argument("--attack", nargs=3, metavar=("UNIT_ID", "X", "Y"), default=None,
                    help="attack a tile (test the garrison-free city path)")
    ap.add_argument("--estimate", nargs=3, metavar=("UNIT_ID", "X", "Y"), default=None,
                    help="run the combat estimate for a target and print it (read-only)")
    ap.add_argument("--cities", action="store_true",
                    help="list every visible city (any owner) with its HP pool and garrison (read-only)")
    args = ap.parse_args()

    print("=== game status ===")
    print(gl.game_status())

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)

    if args.save:
        print(f"\n=== loading {args.save} ===")
        print(await gs.load_game_save(args.save))

    ov = await gs.get_game_overview()
    turn = int(ov.turn)
    print(f"\nin game: T{turn}, {ov.civ_name}, cities {ov.num_cities}, units {ov.num_units}, "
          f"military score {ov.score}")

    if args.cities:
        print("\n=== every visible city (any owner) - read-only ===")
        lines = await gs.conn.execute_write(visible_cities_lua())
        found = 0
        for line in lines:
            if line.startswith("VISIBLE_CITY|"):
                parts = line.split("|")
                print(
                    f"  {parts[1]:>3} {parts[2]:<12} {parts[3]:<18} {parts[4]:<9}"
                    f" {parts[5]:<12} {parts[6]:<10} {parts[7]}"
                )
                found += 1
        if not found:
            print("  (no city of another player is visible right now)")

    if args.estimate:
        unit_id, x, y = args.estimate
        print(f"\n=== estimate: unit {unit_id} vs ({x},{y}) - read-only, nothing is ordered ===")
        # The same builder `attack_unit` runs before every attack, sent on its own so the shared
        # path can be exercised without spending the attack.
        lines = await gs.conn.execute_write(
            lq.build_combat_estimate_query(int(unit_id), int(x), int(y))
        )
        print("  raw: " + " | ".join(line for line in lines if line not in ("---END---",)))
        est = lq.parse_combat_estimate(lines, 0, 0)
        if est is None:
            print("  parsed: none (the builder bailed, or no ESTIMATE line)")
        else:
            from civ_mcp.narrate import narrate_combat_estimate

            print(narrate_combat_estimate(est))

    if args.attack:
        unit_id, x, y = args.attack
        print(f"\n=== attack: unit {unit_id} -> ({x},{y}) ===")
        print(await gs.attack_unit(int(unit_id), int(x), int(y)))

    rows = await report(gs, turn)

    if args.capture:
        pending = [r for r in rows if r.takeable]
        if not pending:
            print("\n--capture: no takeable city this turn (nothing at 0 HP with a melee unit next to it)")
        for city in pending:
            print(f"\n=== capture: {city.city_name} at ({city.x},{city.y}) ===")
            near = [
                u for u in await unit_distances(gs, city.x, city.y)
                if u["dist"] <= 1 and u["type"] == (city.melee_unit or u["type"])
            ] or [u for u in await unit_distances(gs, city.x, city.y) if u["dist"] <= 1]
            if not near:
                print("  no unit found adjacent (the scan said otherwise - investigate)")
                continue
            unit = max(near, key=lambda u: u["moves"])
            print(f"  ordering {unit['type']} {unit['id']} at ({unit['x']},{unit['y']}), "
                  f"{unit['dist']} tile(s) from the city, moves {unit['moves']}")
            print("  " + (await gs.move_unit(unit["id"], city.x, city.y)).replace("\n", "\n  "))
            cities, _ = await gs.get_cities()
            names = [getattr(c, "name", "?") for c in cities]
            print(f"  our cities now: {names}")
            print("  re-scanning…")
            await report(gs, turn)

    await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
