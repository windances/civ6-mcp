"""Play a turn through `GameState`, when the MCP server is not the thing driving the game.

A session that talks to the game through the adapter directly — as this one did, because the MCP
server that owns the tool surface was not in the loop — needs a way to issue one order or read one
scan. This is that, deliberately small:

  play-turn.py units                          every unit with its index, type, tile and moves
  play-turn.py move <type-or-index> <x> <y>   order a move, then print where the unit ended up
  play-turn.py march TYPE:X,Y ...             one unit per order, screen first, siege last
  play-turn.py attack <type-or-index> <x> <y> attack a tile (a city tile resolves as the city)
  play-turn.py diplo | respond <pid> <POSITIVE|NEGATIVE>
  play-turn.py dismiss                        clear the popup layer (disaster, invite, tech)
  play-turn.py scan <x> <y> [radius]          enemy cities in reach + the narrated map
  play-turn.py civic <CIVIC>                  start a civic (the end-of-turn blocker)
  play-turn.py produce <city> <ITEM> [X,Y]    set a city's production, category resolved for you
  play-turn.py purchase <city> [<ITEM>]       buy a unit or building with gold (--faith for faith);
                                              with no ITEM it lists what that city can buy and the price
  play-turn.py improve <type-or-index> <IMPROVEMENT>
  play-turn.py order <type-or-index|all> <fortify|heal|alert|sleep|skip|auto>
  play-turn.py end [--force]                  end the turn, with two guards (below)

`civic`, `produce` and `improve` exist because those three are end-turn **blockers** — the game
refuses to advance without them — and resolving a blocker through a one-off script each time is how
the same three decisions get re-derived every turn. Each prints what the game answered, and
`produce` resolves the category (UNIT/BUILDING/DISTRICT/PROJECT) from the city's own option list so
the caller only has to name the item. A district additionally needs a tile: with no `X,Y` it asks
`get_district_advisor` and uses the top-ranked placement, printing the rest so the choice is visible
rather than silent.

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

`dismiss` exists because a popup holds the turn and leaves no other trace. Measured live T96 on this
branch: `end` reported the same `Turn 95 -> 96` twice while the screen read `NATURAL DISASTER
OCCURRING`, and one dismissal cleared 23 popups (`cinematic_camera`, `NaturalDisasterPopup`,
`InvitePopup` x20) - after which the turn number settled. Measured again an hour later, on the turn
after that: `TechCivicCompletedPopup` plus twenty `InvitePopup`s were waiting. A normal MCP session
has `spectator.PopupWatcher` clearing these in the background; without the command, a session reads
the symptom as "the game will not advance" and reaches for the wrong tool.

Before the skip list, `end` also prints every ranged unit that still has movement and is within five
tiles of an enemy city. That warning exists because the skip list is twelve lines long and "the
Archers have not moved for four turns" does not stand out in it: measured T113-T117, three Archers
sat 4-6 tiles from 圣彼得堡 with a legal firing tile two turns away while the city was ground down by
two Catapults and free melee attacks, and the siege took a turn longer than it had to.
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
    """A unit by MCP index, by type name, or by the game's own localised name.

    The type is matched first because it is stable across languages. The localised name is the
    fallback, and it exists because this game runs in Chinese: every other output in the loop prints
    侦察兵, so that is the string an operator (or a note left for one) reaches for, and it used to
    answer "no unit matching".
    """
    if needle.isdigit():
        index = int(needle)
        return next((u for u in units if u.unit_index == index), None)
    upper = needle.upper().replace("UNIT_", "")
    matches = [u for u in units if upper in str(u.unit_type).upper()]
    if matches:
        return matches[0]
    return next((u for u in units if needle and needle in str(getattr(u, "name", ""))), None)


def preflight_message(sessions: list, deals: list) -> str | None:
    """Why the turn must not be *skipped* yet, or None when it may.

    Pure, so the ordering rule can be tested without a game. `skip_remaining_units` fortifies every
    unit holding moves and cannot be undone, so anything that will make `end_turn` refuse has to be
    found before it runs. `execute_end_turn` checks both of these at its own top
    (`end_turn.py:2129-2150`); this is the same check, moved to where it is still cheap.
    """
    if sessions:
        names = ", ".join(
            f"{getattr(s, 'other_civ_name', '?')} ({getattr(s, 'other_leader_name', '?')})"
            for s in sessions
        )
        return (
            f"Cannot end turn: diplomacy encounter pending with {names}.\n"
            "  answer it: `play-turn.py diplo`, then `play-turn.py respond <pid> "
            "<POSITIVE|NEGATIVE>`"
        )
    if deals:
        return f"Cannot end turn: {len(deals)} incoming trade deal(s) pending (respond_to_trade)."
    return None


async def preflight_blocker(gs) -> str | None:
    """The same question, asked of the live game."""
    sessions = await gs.get_diplomacy_sessions()
    try:
        deals = await gs.get_pending_deals()
    except Exception:  # noqa: BLE001 - a missing deals API must not block the turn
        deals = []
    return preflight_message(sessions, deals)


def parse_legal_targets(lines: list[str], unit_id: int) -> list[tuple[int, int]]:
    """The tiles a unit may legally attack, from the engine's own unused-attack scan.

    Rows are `UNUSED_ATTACK|<type>|<unitID>|<x>,<y>|<TYPE>@<tx>,<ty>(<hp>);...`, so the answer is
    the engine's own legality test (adjacency for melee, `CanStartOperation` LOS for ranged) rather
    than a re-derivation of it here.
    """
    for line in lines or ():
        if not isinstance(line, str) or not line.startswith("UNUSED_ATTACK|"):
            continue
        parts = line.split("|")
        if len(parts) < 5 or parts[2] != str(unit_id):
            continue
        out: list[tuple[int, int]] = []
        for hit in parts[4].split(";"):
            tile = hit.split("@")[-1].split("(")[0]
            try:
                tx, ty = (int(v) for v in tile.split(","))
            except ValueError:
                continue
            out.append((tx, ty))
        return out
    return []


# An enemy CITY is attackable even when nothing stands on its tile, and the unused-attack scan
# only ever reports units - so a city that has just lost its garrison reads as "no legal target"
# and the guard would refuse the shot that takes it. Measured live 2026-09-25: Moscow at 198/200
# with `garrison: none` was refused from both Catapults for exactly this reason.
CITY_AT_LUA = (
    "local me = Game.GetLocalPlayer() "
    "local c = Cities.GetCityInPlot({x}, {y}) "
    "if not c then print('CITY|none') else "
    "  local owner = c:GetOwner() "
    "  local war = (owner == 63) "
    "  if not war then pcall(function() war = Players[me]:GetDiplomacy():IsAtWarWith(owner) end) end "
    "  local nm = '?' "
    "  pcall(function() nm = Locale.Lookup(c:GetName()) end) "
    "  print('CITY|' .. tostring(owner) .. '|' .. tostring(war) .. '|' .. nm) "
    "end "
    'print("{sentinel}")'
)


async def enemy_city_at(gs, x: int, y: int) -> str | None:
    """The name of the enemy city on this tile, or None when there is not one.

    Read-only, and the same `Cities.GetCityInPlot` path `attack_unit` uses to resolve a city
    target - so the guard and the order agree on what is shootable.
    """
    from civ_mcp.lua._helpers import SENTINEL

    lua = CITY_AT_LUA.format(x=x, y=y, sentinel=SENTINEL)
    lines = await gs.conn.execute_write(lua)
    for line in lines or ():
        if isinstance(line, str) and line.startswith("CITY|"):
            parts = line.split("|")
            if len(parts) >= 3 and parts[2] == "true":
                return parts[3] if len(parts) > 3 else "city"
    return None


def attack_refusal(targets: list[tuple[int, int]], unit_at, target) -> str | None:
    """Why this attack must not be ordered, or None when the engine says it is legal.

    Pure, so the rule can be tested without a game. An illegal attack is not refused by the
    adapter: `attack_unit` walks the unit toward the target, runs it out of movement and answers
    `STOPPED_SHORT`, which costs the unit its whole turn. That happened twice in one session -
    measured 2026-09-25, the same Archer lost a turn to it at (54,36)->(52,38) and again at
    (53,35)->(52,37) - so the driver refuses before ordering, and names the tiles that would work.
    """
    if target in targets:
        return None
    legal = ", ".join(f"({x},{y})" for x, y in targets) or "none"
    return (
        f"REFUSING: no legal attack on {target} from {unit_at} - the engine would walk the unit "
        f"toward it and burn its turn (STOPPED_SHORT). Legal targets from here: {legal}"
    )


def usable_placements(placements) -> tuple[list, list[str]]:
    """Split the district advisor's answer into ranked tiles and prose.

    `get_district_advisor` returns placement objects when it has ranked tiles and a plain string when
    it does not (no legal plot, the city's district slots are full, or an error from the adapter).
    Measured live on 圣彼得堡 at T120, where the answer was a STRING: the driver iterated it, took the
    first character as the best tile, and died on `'str' object has no attribute 'x'`. A string is
    therefore one note, never a sequence of them. Pure, so the split is testable without a game.
    """
    if isinstance(placements, str):
        return [], [placements]
    spots = [p for p in placements or () if hasattr(p, "x") and hasattr(p, "y")]
    notes = [str(p) for p in placements or () if isinstance(p, str)]
    return spots, notes


def pick_production(options, item: str):
    """The production option this name means, or None.

    Exact name first, then a substring match that never mistakes a PROJECT for the thing it
    enhances: measured live on 圣彼得堡 at T120, `produce 圣彼得堡 DISTRICT_CAMPUS` matched
    `PROJECT_ENHANCE_DISTRICT_CAMPUS` (the city already had a Campus, so the district itself was not
    on the list) and queued a 9-turn project instead of reporting that the Campus was already there.
    Pure, so the precedence is testable without a game.
    """
    wanted = item.upper()
    options = list(options or ())
    for option in options:
        if str(option.item_name).upper() == wanted:
            return option
    for option in options:
        name = str(option.item_name).upper()
        if wanted in name and not (name.startswith("PROJECT_") and not wanted.startswith("PROJECT")):
            return option
    return None


def parse_tile_args(args: list[str]) -> tuple[int, int] | None:
    """Read a tile from the tail of a command line: `X,Y`, or `X Y`.

    `X,Y` is the documented form, and it is the one the tool output copies. Two tokens is what a
    hand-typed call tends to be, and it used to crash: `produce Chengdu BUILDING_ETEMENANKI 53 23`
    raised a bare `ValueError` out of the unpacking generator and printed a stack trace, from a
    command the caller could see in front of them. Both spellings work now, and anything else
    (one token with no comma, three tokens, a non-number) is `None`, which the caller reports as a
    usage line instead. Pure, so the accepted shapes are testable without a game.
    """
    pieces = args[0].split(",") if len(args) == 1 else args
    if len(pieces) != 2:
        return None
    try:
        return int(pieces[0]), int(pieces[1])
    except ValueError:
        return None


def parse_unused_places(lines: list[str]) -> list[tuple[str, tuple[int, int]]]:
    """`(unit_type, (x, y))` for each unused-attack line, which reads `UNIT_X@3,4 -> target`."""
    out = []
    for line in lines or ():
        if not isinstance(line, str) or "@" not in line:
            continue
        head = line.split("->")[0].strip()
        name, _, tile = head.partition("@")
        try:
            x, y = (int(v) for v in tile.strip().split(","))
        except ValueError:
            continue
        out.append((name.strip(), (x, y)))
    return out


def drop_stale_unused(lines: list[str], units) -> list[str]:
    """Unused-attack lines whose unit has no movement left, i.e. entries from before it acted.

    The adapter's Lua state lags inside a turn frame, so a unit that has just attacked is still
    reported as holding a legal attack. Measured live 2026-09-25 in the 阿斯特拉罕 siege: the
    driver attacked with the unit the guard named, called `end` again, and was refused with the
    SAME line - a loop that cannot be exited except with `--force`. The live unit list is the
    authority on whether the attack is still available, so a line is kept only when a unit of that
    type is standing on that tile with movement left: spent, moved away or dead are all turns that
    have already happened. A line that cannot be parsed is kept, because swallowing a real unused
    attack is worse than one extra refusal. Pure, so the rule is testable without a game.
    """
    live = {(str(u.unit_type), u.x, u.y): u.moves_remaining for u in units}
    kept = []
    for line in lines or ():
        places = parse_unused_places([line])
        if not places:
            kept.append(line)  # unreadable: never swallow something that might be real
            continue
        name, (x, y) = places[0]
        moves = live.get((name, x, y))
        if moves is not None and moves > 0:
            kept.append(line)
    return kept


def end_turn_blocker(unused_attacks: list[str], force: bool) -> str | None:
    """Why the turn must not end yet, or None when it may.

    Pure, so the rule that cost an Archer can be tested without a game: while a unit has a legal
    attack it has not used, ending the turn throws that attack away, and `--force` is the only way
    past it (with a reason in the diary).
    """
    if unused_attacks and not force:
        return "REFUSING to end the turn: a legal attack is still unused"
    return None


async def dismiss_popups(gs, attempts: int = 3) -> list[str]:
    """Clear the popup layer and report what each pass found.

    A popup holds the turn until somebody clears it, and this driver had no way to: measured live
    T96 on the running branch, `end` reported the same `Turn 95 -> 96` twice while the screen read
    `NATURAL DISASTER OCCURRING`, and one `dismiss_popup` cleared 23 popups (`cinematic_camera`,
    `NaturalDisasterPopup`, `InvitePopup` x20) - after which the turn number settled immediately.
    A normal MCP session has `spectator.PopupWatcher` doing this in the background; a direct session
    has only this verb.

    Bounded on purpose, and it stops at the first pass that found nothing: dismissing is safe, but
    re-dismissing in a tight loop during AI processing is the documented way to hang an AI turn
    (`end_turn.py`'s post-timeout block dismisses exactly once for that reason).
    """
    answers: list[str] = []
    for _ in range(max(1, attempts)):
        answer = str(await gs.dismiss_popup())
        answers.append(answer)
        if "Dismissed" not in answer:
            break
    return answers


def wounded_in_reach(pairs: list[dict]) -> list[str]:
    """The BAIT lines from the geometry: a wounded unit inside an enemy's two-tile reach.

    Pure, so the rule can be tested without a game. All three losses of the T103-T130 Russian war
    were this shape - a Barbarian Horseman at 9 HP ordered onto a 0/200 city, a Warrior at 23 HP and
    an Archer at 35 HP left adjacent to a CS 35 Swordsman - and the rule was in the doctrine the
    whole time. Printing it at the end of the turn is the mechanical version of the rule.
    """
    return [line for line in formation_violations(pairs) if line.startswith("BAIT")]


def format_skipped(units) -> list[str]:
    """One line per unit whose turn is about to be discarded, so nothing vanishes silently."""
    return [
        f"   [{unit.unit_index:>2}] {unit.unit_type:<24} ({unit.x},{unit.y}) mv{unit.moves_remaining}"
        for unit in units
    ]


# A unit with no order is fortified and does nothing, and the list of those units is twelve lines
# long by mid-game - so "forgot to move the Archers" is invisible in it. Measured, T113-T117: three
# Archers sat at distance 4-6 from 圣彼得堡 with a legal firing tile two turns away while the city
# was ground down by two Catapults and free melee attacks, and the siege finished a turn later than
# it had to. This query asks the game the one question that catches it: which of our ranged units
# still have movement AND are close enough to an enemy city to matter.
IDLE_RANGED_LUA = (
    "local me = Game.GetLocalPlayer() "
    "local diplo = Players[me]:GetDiplomacy() "
    "for _, u in Players[me]:GetUnits():Members() do "
    "  local x, y = u:GetX(), u:GetY() "
    "  if x ~= -9999 and u:GetMovesRemaining() > 0 then "
    "    local ui = GameInfo.Units[u:GetType()] "
    "    local shoots = ui and (((ui.RangedCombat or 0) > 0) or ((ui.Bombard or 0) > 0)) "
    "    if shoots then "
    "      local best, bname = 99, '' "
    "      for i = 0, 63 do "
    "        local q = Players[i] "
    "        if q and i ~= me and q:IsAlive() and not q:IsBarbarian() then "
    "          local war = false "
    "          pcall(function() war = diplo:IsAtWarWith(i) end) "
    "          if war then "
    "            for _, c in q:GetCities():Members() do "
    "              local d = Map.GetPlotDistance(x, y, c:GetX(), c:GetY()) "
    "              if d < best then best = d; bname = Locale.Lookup(c:GetName()) end "
    "            end "
    "          end "
    "        end "
    "      end "
    "      if best <= 5 then "
    "        print('IDLE_RANGED|' .. (ui and ui.UnitType or '?') .. '|' .. x .. ',' .. y "
    "          .. '|' .. best .. '|' .. bname) "
    "      end "
    "    end "
    "  end "
    "end; "
    f'print("{SENTINEL}")'
)


def parse_idle_ranged(lines: list[str]) -> list[dict]:
    """Rows of `IDLE_RANGED|<type>|<x>,<y>|<distance>|<city>` as dicts."""
    out = []
    for line in lines or ():
        if not isinstance(line, str) or not line.startswith("IDLE_RANGED|"):
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue
        ux, uy = (int(v) for v in parts[2].split(","))
        out.append(
            {"unit": parts[1], "unit_at": (ux, uy), "distance": int(parts[3]), "city": parts[4]}
        )
    return out


def idle_ranged_warning(rows: list[dict]) -> list[str]:
    """One line per ranged unit with unspent movement that is near a city it cannot hit yet.

    Pure, so the rule can be tested without a game. A unit with a legal attack is already covered by
    the unused-attack guard; this is about the ones that are close enough to matter and far enough
    that nothing complains - the state three Archers were in for four turns at 圣彼得堡.
    """
    return [
        f"   IDLE {row['unit']} at {row['unit_at']} is {row['distance']} from {row['city']} "
        "with movement unspent - move it into range or say why it stays"
        for row in sorted(rows, key=lambda r: r["distance"])
    ]


async def query_idle_ranged(gs) -> list[dict]:
    """The same question, asked of the live game (InGame: Cities and Locale both live there)."""
    lines = await gs.conn.execute_write(IDLE_RANGED_LUA)
    return parse_idle_ranged(lines)


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

    The rule only applies **inside an enemy's reach**: `screen-the-siege` itself is written as "a
    siege unit is within two tiles of an enemy with nothing in front of it", and the adapter's
    metric uses the same bound. Measured live 2026-09-25 (T132, at peace, staging with two Catapults
    six tiles from the nearest Nalanda unit): the driver flagged both Catapults `FAIL ... the enemy
    is 6 away`, which is a warning that can never be acted on and therefore trains the operator to
    ignore the block. Anything further than two tiles away is a future problem, not this turn's.
    """
    if posture.enemy_distance is not None and posture.enemy_distance > 2:
        return None
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
            # The same question `end` asks, asked where it can still be acted on: this list is the
            # first read of a turn, and a ranged unit standing near a city it cannot yet hit is the
            # one kind of idle that produces no complaint anywhere else.
            idle = idle_ranged_warning(await query_idle_ranged(gs))
            if idle:
                print("ranged units near an enemy city and not in range yet:")
                for line in idle:
                    print(line)
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
            #
            # Pre-flight FIRST, skip second. `skip_remaining_units` fortifies every unit with
            # moves, and it is irreversible - so a blocker discovered *after* the skip costs the
            # whole army its turn. Measured 2026-09-25: `end` skipped nine units and then hit
            # "Cannot end turn: diplomacy encounter pending with 俄罗斯", and every one of those
            # nine had its movement discarded for a turn that never advanced. `execute_end_turn`
            # checks diplomacy and deals at its own top (end_turn.py:2129-2150); this mirrors that
            # order instead of inverting it.
            from civ_mcp import end_turn as end_turn_module

            blocker = await preflight_blocker(gs)
            if blocker:
                print(blocker)
                print("  no unit's turn has been discarded; answer it, then end again")
                return 1

            leftover = await gs.unused_attacks()
            if leftover:
                # Drop entries the live board disagrees with before refusing: the adapter's Lua
                # state lags inside a turn frame, so a unit that has just attacked still appears
                # here and the refusal would repeat forever.
                current = await gs.get_units()
                stale = [line for line in leftover if line not in drop_stale_unused(leftover, current)]
                leftover = drop_stale_unused(leftover, current)
                for line in stale:
                    print(f"stale (unit has no moves left): {line}")
            blocker = end_turn_blocker(leftover, force="--force" in sys.argv)
            if blocker:
                print(blocker)
                for line in leftover:
                    print("  ", line)
                print("  attack with them, or pass --force and say why in the diary")
                return 1

            pending = [u for u in await gs.get_units() if u.moves_remaining > 0]
            idle = idle_ranged_warning(await query_idle_ranged(gs))
            if idle:
                print("ranged units with movement left near an enemy city (they will be fortified "
                      "and idle if nothing is ordered):")
                for line in idle:
                    print(line)
            bait = wounded_in_reach(parse_pairs(await conn.execute_write(PAIR_SCAN_LUA)))
            if bait:
                print("WOUNDED IN REACH (a unit at 60 HP or less inside an enemy's two-tile reach "
                      "- withdraw it or it dies):")
                for line in bait:
                    print("  ", line)
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
            from civ_mcp.lua import units as lq_units

            scan = await gs.conn.execute_write(lq_units.build_unused_attack_query())
            targets = parse_legal_targets(scan, unit.unit_id)
            refusal = attack_refusal(targets, (unit.x, unit.y), (x, y))
            if refusal:
                city = await enemy_city_at(gs, x, y)
                if city is None:
                    print(refusal)
                    return 1
                print(f"note: {city} is an enemy city with no unit on its tile - "
                      "attacking the city itself")
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

        if verb == "dismiss":
            # The popup layer, which is the one thing that can hold a turn without anything else
            # saying so - measured live T96 on this branch: `end` reported the same `Turn 95 -> 96`
            # twice while the screen read `NATURAL DISASTER OCCURRING`, and one dismissal cleared 23
            # popups (`cinematic_camera`, `NaturalDisasterPopup`, `InvitePopup` x20). A normal MCP
            # session has a background watcher for this (spectator.PopupWatcher); this driver has
            # nothing, so a direct session sits behind the stack and reads as "the turn will not
            # advance". `end` clears the layer once itself, but only after its AI-turn wait has
            # already timed out, which is why the command is separate.
            for answer in await dismiss_popups(gs):
                print(answer)
            return 0

        if verb == "respond":
            pid, response = int(sys.argv[2]), sys.argv[3].upper()
            print(await gs.diplomacy_respond(pid, response))
            return 0

        if verb == "civic":
            print(await gs.set_civic(sys.argv[2]))
            return 0

        if verb == "produce":
            city_name, item = sys.argv[2], sys.argv[3].upper()
            cities, _ = await gs.get_cities()
            city = next((c for c in cities if city_name in str(c.name)), None)
            if city is None:
                print(f"no city matching {city_name!r}; have: "
                      + ", ".join(str(c.name) for c in cities))
                return 1
            options = await gs.list_city_production(city.city_id)
            match = pick_production(options, item)
            if match is None:
                print(f"{city.name} cannot build {item}; options: "
                      + ", ".join(str(o.item_name) for o in options))
                return 1
            target_x = target_y = None
            if len(sys.argv) > 4:
                tile = parse_tile_args(sys.argv[4:])
                if tile is None:
                    print("usage: play-turn.py produce <city> <ITEM> [X,Y]  "
                          f"(could not read a tile from {' '.join(sys.argv[4:])!r})")
                    return 2
                target_x, target_y = tile
            elif "DISTRICT" in str(match.item_name).upper():
                placements = await gs.get_district_advisor(city.city_id, match.item_name)
                spots, notes = usable_placements(placements)
                for note in notes:
                    print(f"  {city.name}: advisor says {note}")
                if spots:
                    best = spots[0]
                    target_x, target_y = best.x, best.y
                    print(f"  {city.name}: district placement from the advisor -> "
                          f"({target_x},{target_y}) adjacency +{best.total_adjacency}; "
                          "alternatives: "
                          + ", ".join(f"({p.x},{p.y}) +{p.total_adjacency}"
                                      for p in spots[1:5]))
                else:
                    # The advisor answers with prose when it has no ranked tiles to offer - for a
                    # city with no legal plot, or one whose slots are full. That is not a crash, and
                    # it is not a placement either: say so and let the caller pass X,Y.
                    print(f"  {city.name}: the advisor offered no ranked tile for "
                          f"{match.item_name} - pass an explicit X,Y to place it")
            reply = await gs.set_city_production(
                city.city_id, match.category, match.item_name, target_x, target_y
            )
            print(f"{city.name}: {match.category} {match.item_name} ({match.turns}t) -> {reply}")
            return 0

        if verb == "order":
            # Phase 5 of the skill: no unit may leave the turn without an explicit order, and
            # `fortify` strictly beats `skip` for a unit that is staying where it is. Until this
            # verb existed the only orders available were move/march/attack/improve/clear, so a
            # garrison could not be told to fortify and the turn ended on `skip_remaining_units`.
            # `order all fortify` parks every unit that still has moves.
            needle, kind = sys.argv[2], sys.argv[3].lower()
            actions = {
                "fortify": gs.fortify_unit,
                "heal": gs.heal_unit,
                "alert": gs.alert_unit,
                "sleep": gs.sleep_unit,
                "skip": gs.skip_unit,
                "auto": gs.automate_explore,
            }
            action = actions.get(kind)
            if action is None:
                print(f"unknown order {kind!r}; use one of " + ", ".join(sorted(actions)))
                return 1
            units = await gs.get_units()
            targets = units if needle == "all" else [find(units, needle)]
            if not targets or targets[0] is None:
                print(f"no unit matching {needle!r}")
                return 1
            for unit in targets:
                print(f"order {kind}: [{unit.unit_index}] {unit.unit_type} ({unit.x},{unit.y}) "
                      f"-> {await action(unit.unit_index)}")
            return 0

        if verb == "governor":
            # A governor point is an end-turn blocker, and every part of the decision - appoint,
            # assign, promote - is a separate method with a separate name-modifier. `governor
            # status` prints the same one-line-per-governor summary the orient read does.
            sub = sys.argv[2].lower() if len(sys.argv) > 2 else "status"
            kind_of = {
                "victor": "GOVERNOR_THE_DEFENDER", "defender": "GOVERNOR_THE_DEFENDER",
                "magnus": "GOVERNOR_THE_RESOURCE_MANAGER", "resource": "GOVERNOR_THE_RESOURCE_MANAGER",
                "liang": "GOVERNOR_THE_BUILDER", "builder": "GOVERNOR_THE_BUILDER",
                "pingala": "GOVERNOR_THE_EDUCATOR", "educator": "GOVERNOR_THE_EDUCATOR",
                "amani": "GOVERNOR_THE_AMBASSADOR", "ambassador": "GOVERNOR_THE_AMBASSADOR",
                "mogsha": "GOVERNOR_THE_CARDINAL", "cardinal": "GOVERNOR_THE_CARDINAL",
                "reyna": "GOVERNOR_THE_MERCHANT", "merchant": "GOVERNOR_THE_MERCHANT",
            }

            def governor_type(token: str) -> str:
                if token.upper().startswith("GOVERNOR_"):
                    return token.upper()
                return kind_of.get(token.lower(), token.upper())

            if sub == "status":
                govs = await gs.get_governors()
                print(f"titles available={govs.points_available} spent={govs.points_spent}")
                for g in govs.appointed or []:
                    print(f"  {g.name} -> {g.assigned_city_name} "
                          f"{'established' if g.is_established else f'{g.turns_to_establish}t'}"
                          f" | can take: "
                          + ", ".join(f"{p.name}={p.promotion_type}" for p in g.available_promotions or []))
                return 0
            if sub in ("appoint", "assign", "promote"):
                if len(sys.argv) < 4:
                    print(f"governor {sub} needs a governor name")
                    return 1
                who = governor_type(sys.argv[3])
                if sub == "appoint":
                    print(f"appoint {who}: {await gs.appoint_governor(who)}")
                elif sub == "assign":
                    city_name = sys.argv[4]
                    cities, _ = await gs.get_cities()
                    city = next((c for c in cities if city_name in str(c.name)), None)
                    if city is None:
                        print(f"no city matching {city_name!r}")
                        return 1
                    print(f"assign {who} -> {city.name}: "
                          f"{await gs.assign_governor(who, city.city_id)}")
                else:
                    promotion = sys.argv[4]
                    print(f"promote {who} {promotion}: "
                          f"{await gs.promote_governor(who, promotion)}")
                return 0
            print("governor subcommands: status | appoint <name> | assign <name> <city> | "
                  "promote <name> <PROMOTION_TYPE>")
            return 1

        if verb == "dedication":
            # A new era's dedication is an end-turn blocker and was reachable only through a
            # one-off script. With no argument it lists the choices with their index numbers; with
            # an index it takes that one.
            status = await gs.get_dedications()
            print(f"age {getattr(status, 'age_type', '?')} era {getattr(status, 'era', '?')} "
                  f"era_score {getattr(status, 'era_score', '?')} "
                  f"(dark {getattr(status, 'dark_threshold', '?')}, "
                  f"golden {getattr(status, 'golden_threshold', '?')}) "
                  f"selections_allowed={getattr(status, 'selections_allowed', '?')} "
                  f"active={getattr(status, 'active', [])}")
            choices = getattr(status, "choices", []) or []
            for choice in choices:
                # The descriptions come back in the game's own encoding and print as mojibake on a
                # cp936 console, so print the enum name and let the caller look the effect up.
                print(f"  [{choice.index}] {choice.name}")
            if len(sys.argv) < 3:
                return 0
            index = int(sys.argv[2])
            print(f"choose dedication {index}: {await gs.choose_dedication(dedication_index=index)}")
            return 0

        if verb == "research":
            print(await gs.set_research(sys.argv[2]))
            return 0

        if verb == "pantheon":
            # Both halves of the blocker: with no argument, what is on offer and at what faith; with
            # one, take it. A completed pantheon and a completed tech are the two blockers that used
            # to be reachable only through a one-off script.
            status = await gs.get_pantheon_status()
            if len(sys.argv) < 3:
                print(f"faith {getattr(status, 'faith_balance', '?')} | "
                      f"has_pantheon={getattr(status, 'has_pantheon', '?')}")
                for belief in getattr(status, "available_beliefs", []) or []:
                    print(f"  {belief.belief_type:<38} {belief.name:<8} {belief.description}")
                return 0
            chosen = sys.argv[2]
            if not chosen.upper().startswith("BELIEF_"):
                match = next(
                    (b for b in getattr(status, "available_beliefs", []) or []
                     if chosen in str(b.name) or chosen.upper() in b.belief_type.upper()),
                    None,
                )
                if match is None:
                    print(f"no belief matching {chosen!r}")
                    return 1
                chosen = match.belief_type
            print(f"choose {chosen}: {await gs.choose_pantheon(chosen)}")
            return 0

        if verb == "purchase":
            # Gold above ~300 that is not saved for a named purchase is wasted (the directive), and
            # until this verb existed the only way to spend it was a one-off script per purchase -
            # which is how a treasury sits at 500 with fifteen unimproved tiles and no Builder.
            # `purchase <city>` with no item lists what that city can buy and for how much.
            city_name = sys.argv[2]
            item = sys.argv[3].upper() if len(sys.argv) > 3 else None
            yield_type = "YIELD_FAITH" if "--faith" in sys.argv else "YIELD_GOLD"
            cities, _ = await gs.get_cities()
            city = next((c for c in cities if city_name in str(c.name)), None)
            if city is None:
                print(f"no city matching {city_name!r}; have: "
                      + ", ".join(str(c.name) for c in cities))
                return 1
            options = await gs.list_city_production(city.city_id)
            purchasable = [
                o for o in options
                if getattr(o, "gold_cost", -1) and o.gold_cost > 0
                and o.category in ("UNIT", "BUILDING")
            ]
            if item is None:
                print(f"{city.name}: purchasable with {yield_type}")
                for option in sorted(purchasable, key=lambda o: o.gold_cost):
                    print(f"  {option.gold_cost:>5}g  {option.category:<9} {option.item_name}")
                if not purchasable:
                    print("  (nothing purchasable in this city)")
                return 0
            match = pick_production(purchasable, item)
            if match is None:
                # A district or a project is a legal production order and not a purchase: say which
                # it is instead of letting the engine answer ERR:INVALID_TYPE.
                elsewhere = pick_production(options, item)
                if elsewhere is not None:
                    print(f"{city.name}: {elsewhere.item_name} is {elsewhere.category} - it can only "
                          "be produced, not bought (districts and projects are production-only)")
                else:
                    print(f"{city.name} cannot buy {item}; purchasable: "
                          + ", ".join(f"{o.item_name}({o.gold_cost}g)" for o in purchasable))
                return 1
            reply = await gs.purchase_item(city.city_id, match.category, match.item_name, yield_type)
            print(f"{city.name}: buy {match.item_name} for {match.gold_cost}g -> {reply}")
            return 0

        if verb == "improve":
            needle, improvement = sys.argv[2], sys.argv[3].upper()
            if not improvement.startswith("IMPROVEMENT_"):
                improvement = "IMPROVEMENT_" + improvement
            unit = find(await gs.get_units(), needle)
            if unit is None:
                print(f"no unit matching {needle!r}")
                return 1
            print(f"improve: [{unit.unit_index}] {unit.unit_type} ({unit.x},{unit.y}) "
                  f"{improvement}")
            print("  " + await gs.improve_tile(unit.unit_index, improvement))
            return 0

        if verb == "clear":
            # A resource tile under forest or jungle cannot be improved until the feature is gone,
            # which is a separate order (and a separate charge) - measured at (59,28), where the
            # AMBER mine answered 'tile has FEATURE_JUNGLE (use remove_feature first)'.
            needle = sys.argv[2]
            unit = find(await gs.get_units(), needle)
            if unit is None:
                print(f"no unit matching {needle!r}")
                return 1
            print(f"clear: [{unit.unit_index}] {unit.unit_type} ({unit.x},{unit.y})")
            print("  " + await gs.remove_feature(unit.unit_index))
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
