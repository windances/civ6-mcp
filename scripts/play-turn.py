"""Play a turn through `GameState`, when the MCP server is not the thing driving the game.

A session that talks to the game through the adapter directly — as this one did, because the MCP
server that owns the tool surface was not in the loop — needs a way to issue one order or read one
scan. This is that, deliberately small:

  play-turn.py units                          every unit with its index, type, tile and moves
  play-turn.py move <type-or-index> <x> <y>   order a move, then print where the unit ended up
  play-turn.py march TYPE:X,Y ...             one unit per order, screen first, siege last
  play-turn.py attack <type-or-index> <x> <y> attack a tile (a city tile resolves as the city)
  play-turn.py diplo | respond <pid> <POSITIVE|NEGATIVE>
  play-turn.py scan <x> <y> [radius]          enemy cities in reach + the narrated map
  play-turn.py end [--force]                  end the turn, with two guards (below)

`move` prints the *actual* position read back after the order, because moves are asynchronous: the
reply to a move names the destination tile, not the arrival, and a blocked move looks the same as a
successful one until the position is read.

Two guards exist because each one cost units before it existed (Moscow, T105-T120):

* **a legal attack that is unused refuses the end of the turn** (`unused_attacks`, the adapter's own
  one-query answer to `use-your-attacks`). A wounded Archer was left beside a Russian Scout while
  five of our units stood within two tiles; the turn was ended by ordering the volley the operator
  remembered and letting `skip_remaining_units` discard the rest.
* **every unit whose turn is discarded is named** with its type, tile and remaining moves. Three
  Warriors, a Horseman and a Battering Ram sat out the whole siege — the Ram was killed without ever
  attacking — because the only units this driver moves are the ones the caller names.

`--force` overrides the first guard; say why in the diary when you use it.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
# The diary directory is read from CIV_MCP_DATA_DIR at *import* time and the default
# (~/.civ6-mcp) is outside this sandbox. Without this, `end` cannot read the turn's diary row and
# reports four rules as "un-evaluable: metric(...) is not available this turn" - measured
# 2026-09-25 - while the same rules evaluate fine. Point it at the workspace, as the DSH overlay
# does for the MCP server.
os.environ.setdefault(
    "CIV_MCP_DATA_DIR", str(pathlib.Path(__file__).resolve().parents[1] / ".civ6-mcp-data")
)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402
from civ_mcp.lua._helpers import SENTINEL  # noqa: E402
from civ_mcp.narrate import narrate_map  # noqa: E402


def find(units, needle: str):
    """A unit by MCP index, or by type name (case-insensitive substring)."""
    if needle.isdigit():
        index = int(needle)
        return next((u for u in units if u.unit_index == index), None)
    needle = needle.upper().replace("UNIT_", "")
    matches = [u for u in units if needle in str(u.unit_type).upper()]
    return matches[0] if matches else None


def end_turn_blocker(unused_attacks: list[str], force: bool) -> str | None:
    """Why the turn must not end yet, or None when it may.

    Pure, so the rule that cost an Archer can be tested without a game: while a unit has a legal
    attack it has not used, ending the turn throws that attack away, and `--force` is the only way
    past it (with a reason in the diary).
    """
    if unused_attacks and not force:
        return "REFUSING to end the turn: a legal attack is still unused"
    return None


def format_skipped(units) -> list[str]:
    """One line per unit whose turn is about to be discarded, so nothing vanishes silently."""
    return [
        f"   [{unit.unit_index:>2}] {unit.unit_type:<24} ({unit.x},{unit.y}) mv{unit.moves_remaining}"
        for unit in units
    ]


# ---------------------------------------------------------------------------
# Posture: the formation, checked instead of remembered
#
# Five times in one campaign a unit stood in the wrong place because "who screens whom" was carried
# in the operator's head: two Archers died with the melee *behind* them, a Battering Ram was killed
# without ever attacking, a disengagement pulled the screen back and left a city's doorstep empty.
# The distances here come from `Map.GetPlotDistance` inside the game - hand-computed hex distances
# were wrong repeatedly - and the rules are pure functions below.
# ---------------------------------------------------------------------------

PAIR_SCAN_LUA = (
    "local me = Game.GetLocalPlayer() "
    "local diplo = Players[me]:GetDiplomacy() "
    "for _, u in Players[me]:GetUnits():Members() do "
    "  local ui = GameInfo.Units[u:GetType()] "
    "  if ui and ((ui.Combat or 0) > 0 or (ui.RangedCombat or 0) > 0 or (ui.Bombard or 0) > 0) then "
    "    for i = 0, 63 do "
    "      local q = Players[i] "
    "      if q and i ~= me and q:IsAlive() and diplo:IsAtWarWith(i) then "
    "        for _, e in q:GetUnits():Members() do "
    "          local d = Map.GetPlotDistance(u:GetX(), u:GetY(), e:GetX(), e:GetY()) "
    "          if d <= 4 then "
    "            local ei = GameInfo.Units[e:GetType()] "
    "            print('PAIR|' .. u:GetID() .. '|' .. ui.UnitType .. '|' .. u:GetX() .. ',' .. u:GetY() "
    "              .. '|' .. (u:GetMaxDamage() - u:GetDamage()) "
    "              .. '|' .. (ei and ei.UnitType or '?') .. '|' .. e:GetX() .. ',' .. e:GetY() "
    "              .. '|' .. d) "
    "          end "
    "        end "
    "      end "
    "    end "
    "  end "
    "end; "
    f'print("{SENTINEL}")'
)

_SCREEN = (
    "WARRIOR", "SWORDSMAN", "MAN_AT_ARMS", "MUSKETMAN", "INFANTRY", "SPEARMAN", "PIKEMAN",
    "AT_CREW", "HEAVY_CHARIOT", "KNIGHT", "HORSEMAN", "TANK", "MECHANICAL_INFANTRY", "CUIRASSIER",
)
_RANGED = ("SLINGER", "ARCHER", "CROSSBOWMAN", "FIELD_CANNON", "CROUCHING_TIGER")
_SIEGE = ("CATAPULT", "TREBUCHET", "BOMBARD", "ARTILLERY", "ROCKET_ARTILLERY")
_SUPPORT = ("BATTERING_RAM", "SIEGE_TOWER", "MILITARY_ENGINEER", "MEDIC")


def role(unit_type: str) -> str:
    """screen / ranged / siege / support / civilian - the class decides what a unit may do."""
    name = str(unit_type).upper().replace("UNIT_", "")
    if any(token in name for token in _SIEGE):
        return "siege"
    if any(token in name for token in _RANGED):
        return "ranged"
    if any(token in name for token in _SUPPORT):
        return "support"
    if any(token in name for token in _SCREEN):
        return "screen"
    return "civilian"


def screen_rule_failure(posture) -> str | None:
    """The doctrine's test on one siege unit: is something strictly closer to that enemy?

    `screen_enemy_distance >= enemy_distance` is the failure `screen-the-siege` reports; a screen
    that is exactly as close as the siege unit is a second target, not cover.
    """
    if posture.enemy_distance is None or posture.screen_enemy_distance is None:
        return f"{posture.unit_type}: no screen within reach of the nearest enemy"
    if posture.screen_enemy_distance >= posture.enemy_distance:
        return (
            f"{posture.unit_type} at ({posture.x},{posture.y}): the enemy is {posture.enemy_distance} "
            f"away and the nearest screen is no closer ({posture.screen_enemy_distance})"
        )
    return None


def parse_pairs(lines: list[str]) -> list[dict]:
    """Rows of `PAIR|unitID|type|x,y|hp|enemyType|ex,ey|distance` as dicts."""
    out = []
    for line in lines or ():
        if not isinstance(line, str) or not line.startswith("PAIR|"):
            continue
        parts = line.split("|")
        if len(parts) < 8:
            continue
        ux, uy = (int(v) for v in parts[3].split(","))
        ex, ey = (int(v) for v in parts[6].split(","))
        out.append(
            {
                "unit": parts[2],
                "unit_at": (ux, uy),
                "unit_hp": int(parts[4]),
                "enemy": parts[5],
                "enemy_at": (ex, ey),
                "distance": int(parts[7]),
            }
        )
    return out


def formation_violations(pairs: list[dict]) -> list[str]:
    """What the geometry says is wrong, in the doctrine's own terms.

    * **inverted**: every ranged or siege unit is at least as close to an enemy as every screen
      unit - the shooters are the front line, which is how two Archers were picked off while the
      melee stood behind them.
    * **bait**: a wounded unit (60 HP or less) inside a melee attacker's two-tile reach. A damaged
      unit attacks for less (manual, p.88) and dies to one blow from something stronger.
    """
    if not pairs:
        return []
    closest = {}
    for row in pairs:
        key = row["unit_at"]
        closest[key] = min(closest.get(key, 99), row["distance"])
    screens = [row for row in pairs if role(row["unit"]) == "screen"]
    shooters = [row for row in pairs if role(row["unit"]) in ("ranged", "siege")]
    violations = []
    if screens and shooters:
        nearest_screen = min(row["distance"] for row in screens)
        nearest_shooter = min(row["distance"] for row in shooters)
        if nearest_shooter <= nearest_screen:
            shooters_at = [f"{row['unit']}{row['unit_at']}" for row in shooters if row["distance"] == nearest_shooter]
            violations.append(
                f"INVERTED: {', '.join(sorted(set(shooters_at)))} at {nearest_shooter} from an enemy, "
                f"while the nearest screen ({screens[0]['unit']}) is {nearest_screen} - the shooters are the front line"
            )
    for row in pairs:
        if row["unit_hp"] <= 60 and row["distance"] <= 2:
            violations.append(
                f"BAIT: {row['unit']} at {row['unit_at']} has {row['unit_hp']} HP and "
                f"{row['enemy']} is {row['distance']} away - withdraw it or screen it"
            )
    return sorted(set(violations))


async def march(gs: GameState, orders: list[tuple[str, int, int]]) -> None:
    """Move one unit per order toward its tile, in the order given.

    An order names a type (`ARCHER:54,36`) and consumes the next unmoved unit of that type, so two
    orders send two different Archers to two different tiles; or it names an index (`11:55,34`) -
    which is the only way to be precise about *which* unit moves, and the reason is a live one:
    a type order for WARRIOR kept picking the 上海 garrison off its city tile, because that unit
    has the lowest index in the list. The engine walks a unit as far as its movement allows and
    stops, so the tile is a direction for this turn, not an order to arrive. Naming the screen
    first and the siege last is what keeps the column in formation.
    """
    used: set[int] = set()
    for kind, tx, ty in orders:
        for unit in await gs.get_units():
            if unit.unit_index in used or unit.moves_remaining <= 0:
                continue
            if kind.isdigit():
                if unit.unit_index != int(kind):
                    continue
            elif kind not in str(unit.unit_type).upper():
                continue
            if (unit.x, unit.y) == (tx, ty):
                used.add(unit.unit_index)
                break
            reply = await gs.move_unit(unit.unit_index, tx, ty)
            used.add(unit.unit_index)
            print(f"  [{unit.unit_index}] {unit.unit_type} ({unit.x},{unit.y}) -> ({tx},{ty})")
            print(f"    {reply}")
            break


async def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    verb = sys.argv[1]

    conn = GameConnection()
    await conn.connect()
    gs = GameState(conn)
    try:
        if verb == "units":
            for u in await gs.get_units():
                kinds = []
                if u.combat_strength:
                    kinds.append(f"cs{u.combat_strength}")
                if u.ranged_strength:
                    kinds.append(f"rs{u.ranged_strength}")
                print(
                    f"  [{u.unit_index:>2}] {u.unit_type:<24} ({u.x},{u.y}) "
                    f"hp{u.health} mv{u.moves_remaining} {' '.join(kinds)}"
                )
            return 0

        if verb == "move":
            needle, x, y = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
            units = await gs.get_units()
            unit = find(units, needle)
            if unit is None:
                print(f"no unit matching {needle!r}")
                return 1
            before = (unit.x, unit.y)
            reply = await gs.move_unit(unit.unit_index, x, y)
            print(f"order: {unit.unit_type} {before} -> ({x},{y})\n  {reply}")
            await asyncio.sleep(2.5)
            for u in await gs.get_units():
                if u.unit_index == unit.unit_index:
                    print(f"read back: {u.unit_type} now at ({u.x},{u.y}) hp{u.health} mv{u.moves_remaining}")
                    print(f"  moved {before} -> ({u.x},{u.y})")
            return 0

        if verb == "march":
            # march TYPE:X,Y ... -- melee and the ram first, then ranged, then siege.
            orders: list[tuple[str, int, int]] = []
            for arg in sys.argv[2:]:
                kind, _, tile = arg.partition(":")
                tx, ty = (int(v) for v in tile.split(","))
                orders.append((kind.upper(), tx, ty))
            await march(gs, orders)
            await asyncio.sleep(2.5)
            print("--- read back ---")
            for unit in await gs.get_units():
                if unit.combat_strength:
                    print(
                        f"  [{unit.unit_index:>2}] {unit.unit_type:<24} ({unit.x},{unit.y}) "
                        f"mv{unit.moves_remaining}"
                    )
            return 0

        if verb == "end":
            # The library-level end of turn: it runs the turn checks, the empire warnings, the
            # siege/capture/loyalty blocks and the 10-turn review, which is everything the MCP's
            # end_turn tool prints apart from the diary row (scripts/record-turn.py writes that).
            # Units still holding moves are skipped first, or the turn stops on a blocker.
            from civ_mcp import end_turn as end_turn_module

            leftover = await gs.unused_attacks()
            blocker = end_turn_blocker(leftover, force="--force" in sys.argv)
            if blocker:
                print(blocker)
                for line in leftover:
                    print("  ", line)
                print("  attack with them, or pass --force and say why in the diary")
                return 1

            pending = [u for u in await gs.get_units() if u.moves_remaining > 0]
            if pending:
                print(f"skipping {len(pending)} unit(s) with unspent moves:")
                for line in format_skipped(pending):
                    print(line)
                print("  " + await gs.skip_remaining_units())
            print(await end_turn_module.execute_end_turn(gs))
            return 0

        if verb == "attack":
            needle, x, y = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
            units = await gs.get_units()
            unit = find(units, needle)
            if unit is None:
                print(f"no unit matching {needle!r}")
                return 1
            print(f"attack: [{unit.unit_index}] {unit.unit_type} ({unit.x},{unit.y}) -> ({x},{y})")
            print("  " + await gs.attack_unit(unit.unit_index, x, y))
            return 0

        if verb == "diplo":
            sessions = await gs.get_diplomacy_sessions()
            if not sessions:
                print("no pending diplomacy session")
                return 0
            for session in sessions:
                print(f"--- session with player {session.other_player_id} ---")
                for field in ("leader_name", "message", "statement_type", "choices", "active"):
                    value = getattr(session, field, None)
                    if value not in (None, "", [], 0, False):
                        print(f"  {field}: {value}")
            return 0

        if verb == "respond":
            pid, response = int(sys.argv[2]), sys.argv[3].upper()
            print(await gs.diplomacy_respond(pid, response))
            return 0

        if verb == "posture":
            # Everything the formation decision needs, in one place, before anything is ordered.
            pairs = parse_pairs(await conn.execute_write(PAIR_SCAN_LUA))
            postures = await gs.siege_posture()
            unused = await gs.unused_attacks()

            print("=== our line by role (front first) ===")
            for unit in sorted(await gs.get_units(), key=lambda u: (role(u.unit_type), -(u.combat_strength or 0))):
                kind = role(unit.unit_type)
                if kind in ("civilian", "support"):
                    continue
                at = (unit.x, unit.y)
                nearest = min((row["distance"] for row in pairs if row["unit_at"] == at), default=None)
                print(
                    f"  {kind:<7} [{unit.unit_index:>2}] {unit.unit_type:<24} ({unit.x},{unit.y}) "
                    f"hp{unit.health:<4} mv{unit.moves_remaining}"
                    + (f" nearest enemy {nearest}" if nearest is not None else "")
                )

            print("=== siege rule (something must be strictly closer than the siege unit) ===")
            if not postures:
                print("  no siege unit in the field")
            for posture in postures:
                failure = screen_rule_failure(posture)
                print(f"  {'FAIL' if failure else 'ok  '} {failure or f'{posture.unit_type} at ({posture.x},{posture.y}) is screened'}")

            print("=== formation violations ===")
            problems = formation_violations(pairs) + [f for f in (screen_rule_failure(p) for p in postures) if f]
            for problem in problems or ["  none"]:
                print(f"  {problem}")

            print("=== attacks still unused ===")
            for line in unused or ["  none"]:
                print(f"  {line}")
            return 0 if not problems else 1

        if verb == "scan":
            x, y = int(sys.argv[2]), int(sys.argv[3])
            radius = int(sys.argv[4]) if len(sys.argv) > 4 else 3
            readiness = await gs.capture_readiness()
            print("=== enemy cities in reach (capture readiness) ===")
            for line in readiness:
                print("  ", line)
            print(f"=== map around ({x},{y}) radius {radius} ===")
            print(narrate_map(await gs.get_map_area(x, y, radius)))
            return 0

        print(f"unknown verb {verb!r}")
        return 2
    finally:
        await conn.disconnect()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
