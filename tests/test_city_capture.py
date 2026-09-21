"""Taking a city: the tile the game only gives up to a melee unit standing on it.

Two live failures, both from the same blind spot - `Map.GetUnitsAt(x, y)` sees units and nothing
else:

1. **A city with no garrison in it was not attackable.** Moscow was ground down to
   `city hp: 0/200` on T120; from then on every `attack` returned
   `ERR:NO_ENEMY|No hostile unit at (54,40)`, the city healed about twenty points a turn back to
   120/200 by T126, the Russian Swordsman killed the Battering Ram, and the assault was
   abandoned. The same city, same turn numbers, fell in four turns when a human attacked the
   tile from the game UI. `Cities.GetCityInPlot` is the API the UI itself uses.
2. **The capture move was not recognised as hostile either.** `build_move_unit` only set the
   ATTACK modifier when an enemy *unit* stood on the target tile, so moving a melee unit onto a
   broken city went out as a plain move and the game refused it ("enemy territory but movement
   still blocked"). A Battering Ram's attempt returned `CAPTURE_MOVE|...|BLOCKED` - and a
   support unit could not have taken the city anyway.

What has no damage number attached to it is that last step, so the turn result now carries a
`TAKE THE CITY` block and the `take-the-city` rule fires while a city at 0 HP is still standing
with a melee unit in reach of it.
"""

from __future__ import annotations

import asyncio
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.game_state import _extract_pre_hp  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402

MOSCOW = "CAPTURE_READY|Moscow|54,40|hp:0|max:200|walls:0/0|owner:1|melee_adjacent:1|melee_within_2:3|UNIT_SPEARMAN"
STPETERSBURG = (
    "CAPTURE_READY|St Petersburg|60,30|hp:150|max:200|walls:74/100|owner:1"
    "|melee_adjacent:0|melee_within_2:0|"
)


def lua_blocks_balanced(lua: str) -> bool:
    """Crude but useful: count block openers against `end`/`until`, ignoring strings and comments.

    There is no Lua interpreter in this environment, so the generated chunks cannot be parsed for
    real; a missing `end` is the mistake that matters, and that one this catches. The scan is a
    single pass because the order of stripping matters: `print("---END---")` is a string that
    starts with a comment marker, and stripping comments first would eat the closing quote and
    then swallow live keywords as string content.
    """
    depth = 0
    last_kw = ""
    i, n = 0, len(lua)
    while i < n:
        if lua.startswith("--[[", i):
            end = lua.find("]]", i + 4)
            i = n if end < 0 else end + 2
            continue
        if lua.startswith("--", i):
            end = lua.find("\n", i)
            i = n if end < 0 else end + 1
            continue
        if lua.startswith("[[", i):
            end = lua.find("]]", i + 2)
            i = n if end < 0 else end + 2
            continue
        char = lua[i]
        if char in "\"'":
            quote, i = char, i + 1
            while i < n:
                if lua[i] == "\\":
                    i += 2
                    continue
                if lua[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if char.isalpha() or char == "_":
            j = i
            while j < n and (lua[j].isalnum() or lua[j] == "_"):
                j += 1
            word = lua[i:j]
            if word in ("function", "if", "for", "while", "repeat"):
                depth += 1
                last_kw = word
            elif word == "do":
                # `do` after `for`/`while` belongs to that block; on its own it opens one.
                if last_kw not in ("for", "while"):
                    depth += 1
                    last_kw = "do"
            elif word in ("end", "until"):
                depth -= 1
                last_kw = word
            i = j
            continue
        i += 1
    return depth == 0


class TestTheTargetCanBeACity:
    def test_a_city_with_no_garrison_is_a_target(self):
        lua = lq.build_attack_unit(1, 54, 40)
        assert "Cities.GetCityInPlot" in lua
        assert "No hostile unit or city at" in lua
        assert "ERR:NO_ENEMY|No hostile unit at (" not in lua, "an empty city must not bail"
        assert "targetIsCity = true" in lua

    def test_the_city_pool_is_the_number_reported(self):
        lua = lq.build_attack_unit(1, 54, 40)
        assert "DISTRICT_GARRISON" in lua, "the city's own HP pool, not the walls"
        assert '"city HP:"' in lua, "the melee report must say city, not enemy"

    def test_taking_the_city_is_stated(self):
        lua = lq.build_attack_unit(1, 54, 40)
        assert "CITY TAKEN" in lua

    def test_the_estimate_handles_an_empty_city(self):
        lua = lq.build_combat_estimate_query(1, 54, 40)
        assert "CITY_CENTER" in lua
        assert "No hostile unit or city at" in lua

    def test_moving_onto_an_enemy_city_counts_as_hostile(self):
        lua = lq.build_move_unit(1, 54, 40)
        assert "Cities.GetCityInPlot" in lua
        assert "UnitOperationMoveModifiers.ATTACK" in lua

    def test_a_city_strike_can_bombard_an_enemy_city(self):
        lua = lq.build_city_attack(1, 54, 40)
        assert "Cities.GetCityInPlot" in lua
        assert "No hostile unit or city at target tile" in lua

    def test_the_changed_builders_still_balance(self):
        for lua in (
            lq.build_attack_unit(1, 54, 40),
            lq.build_move_unit(1, 54, 40),
            lq.build_combat_estimate_query(1, 54, 40),
            lq.build_city_attack(1, 54, 40),
            lq.build_capture_check_query(),
        ):
            assert lua_blocks_balanced(lua)

    def test_the_balance_checker_is_not_vacuous(self):
        assert lua_blocks_balanced("if x then print(1) end")
        assert not lua_blocks_balanced("if x then print(1)")
        assert not lua_blocks_balanced("function f() --[[ end ]] return 1")


class TestTheScan:
    def test_it_parses_the_city_numbers(self):
        rows = lq.parse_capture_readiness_response([MOSCOW, STPETERSBURG])
        assert [r.city_name for r in rows] == ["Moscow", "St Petersburg"]
        assert rows[0].hp == 0 and rows[0].max_hp == 200
        assert rows[0].melee_adjacent == 1 and rows[0].melee_within_2 == 3
        assert rows[0].melee_unit == "UNIT_SPEARMAN"
        assert rows[1].wall_hp == 74 and rows[1].wall_max == 100
        assert rows[1].melee_adjacent == 0

    def test_a_short_or_foreign_line_is_skipped(self):
        assert lq.parse_capture_readiness_response(["CAPTURE_READY|X", "SENTINEL", ""]) == []

    def test_down_and_takeable_are_different_questions(self):
        down_and_adjacent = lq.parse_capture_readiness_response([MOSCOW])[0]
        assert down_and_adjacent.down and down_and_adjacent.takeable
        out_of_reach = lq.parse_capture_readiness_response(
            [MOSCOW.replace("melee_adjacent:1", "melee_adjacent:0")]
        )[0]
        assert out_of_reach.down and not out_of_reach.takeable
        healthy = lq.parse_capture_readiness_response([STPETERSBURG])[0]
        assert not healthy.down and not healthy.takeable

    def test_a_full_hp_city_is_not_down(self):
        assert not m.CaptureReadiness("X", 1, 1, hp=200, max_hp=200).down


class TestTheMetric:
    def test_a_downed_city_with_a_melee_unit_in_reach_is_ready(self):
        rows = lq.parse_capture_readiness_response([MOSCOW])
        metrics = et._capture_metrics(rows)
        assert metrics["capture_ready"] == 1
        assert metrics["downed_enemy_cities"] == 1
        assert metrics["enemy_city_hp_min"] == 0

    def test_a_downed_city_out_of_reach_is_still_counted(self):
        rows = lq.parse_capture_readiness_response(
            [MOSCOW.replace("melee_adjacent:1", "melee_adjacent:0")]
        )
        metrics = et._capture_metrics(rows)
        assert metrics["capture_ready"] == 0
        assert metrics["downed_enemy_cities"] == 1

    def test_the_lowest_city_hp_is_reported(self):
        rows = lq.parse_capture_readiness_response([MOSCOW, STPETERSBURG])
        assert et._capture_metrics(rows)["enemy_city_hp_min"] == 0

    def test_nothing_in_sight_is_neutral(self):
        metrics = et._capture_metrics([])
        assert metrics == {
            "enemy_cities_seen": 0,
            "downed_enemy_cities": 0,
            "capture_ready": 0,
            "enemy_city_hp_min": 999,
        }

    def test_the_contact_metrics_carry_them_and_scan_once(self):
        class FakeGS:
            def __init__(self):
                self.calls = 0

            async def capture_readiness(self):
                self.calls += 1
                return lq.parse_capture_readiness_response([MOSCOW])

        gs = FakeGS()
        first = asyncio.run(et._contact_metrics(gs, 124, {}))
        second = asyncio.run(et._contact_metrics(gs, 124, {}))
        assert first["capture_ready"] == 1 and second["capture_ready"] == 1
        assert gs.calls == 1, "the scan is cached for the turn"

    def test_a_failed_scan_is_not_an_exception(self):
        class Broken:
            async def capture_readiness(self):
                raise RuntimeError("tuner busy")

        assert asyncio.run(et._contact_metrics(Broken(), 124, {}))["capture_ready"] == 0

    def test_a_historical_row_reads_as_zero(self):
        row = {"turn": 124, "is_agent": True, "unit_composition": {"SPEARMAN": 1}}
        metrics = et._context_from_row(row).metrics
        assert metrics["capture_ready"] == 0
        assert metrics["downed_enemy_cities"] == 0


class TestTheReport:
    def _event(self, line: str, turn: int = 124) -> str | None:
        return et._capture_event(lq.parse_capture_readiness_response([line]), turn)

    def test_a_broken_city_with_a_melee_unit_adjacent_says_move_it_in(self):
        text = self._event(MOSCOW) or ""
        assert "TAKE THE CITY" in text
        assert "UNIT_SPEARMAN is adjacent" in text
        assert "MOVE IT ONTO THE CITY TILE" in text
        assert "target_x=54, target_y=40" in text

    def test_a_melee_unit_two_tiles_out_is_told_to_close(self):
        text = self._event(MOSCOW.replace("melee_adjacent:1", "melee_adjacent:0")) or ""
        assert "within two tiles but not adjacent" in text

    def test_a_broken_city_with_nobody_near_it_says_so(self):
        text = self._event(
            MOSCOW.replace("melee_adjacent:1", "melee_adjacent:0").replace(
                "melee_within_2:3", "melee_within_2:0"
            )
        ) or ""
        assert "no melee unit in reach" in text

    def test_a_city_that_is_still_standing_tall_says_nothing(self):
        assert self._event(STPETERSBURG) is None


class TestTheRule:
    FILE = pathlib.Path("prompts/checks/turn-checks.md")

    def context(self, **metrics):
        base = {
            "wonders": 1, "districts": 30, "pop": 30, "improvements": 90, "cities": 5,
            "gold_per_turn": 30, "attacks_this_turn": 0, "unused_attacks": 0,
            "capture_ready": 0, "downed_enemy_cities": 0, "enemy_city_hp_min": 999,
        }
        base.update(metrics)
        return turn_checks.CheckContext(turn=124, units={}, metrics=base, researched=frozenset())

    def failing(self, **metrics) -> set[str]:
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), self.context(**metrics))
        return run.failing_ids

    def test_a_takeable_city_left_standing_fails(self):
        ids = self.failing(capture_ready=1, downed_enemy_cities=1, enemy_city_hp_min=0)
        assert "take-the-city" in ids

    def test_taking_it_clears_the_rule(self):
        ids = self.failing(capture_ready=0, downed_enemy_cities=0, enemy_city_hp_min=999)
        assert "take-the-city" not in ids

    def test_a_downed_city_no_melee_can_reach_is_not_a_failure(self):
        # Out of reach is a plan, not a broken rule: the city may be on the other side of the map.
        ids = self.failing(capture_ready=0, downed_enemy_cities=1, enemy_city_hp_min=0)
        assert "take-the-city" not in ids

    def test_the_history_recomputes_without_the_new_metrics(self):
        row = {
            "turn": 124, "is_agent": True, "unit_composition": {"SPEARMAN": 1},
            "pop": 30, "districts": 30, "wonders": 1, "cities": 5, "improvements": 90,
            "gold_per_turn": 30,
        }
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), et._context_from_row(row))
        assert "take-the-city" not in run.failing_ids
        assert not [c for c, reason in run.failures if "un-evaluable" in reason]


class TestTheMeleeResultLine:
    def test_a_city_report_is_read_as_the_pre_attack_number(self):
        line = (
            "OK:MELEE_ATTACK|target:Moscow at (54,40)|city HP:0 -> 0/200"
            "|your HP:100 -> 72 CS:25|CITY TAKEN - resolve keep/raze with city_action"
        )
        assert _extract_pre_hp(line) == 0

    def test_a_unit_report_still_reads_as_before(self):
        assert _extract_pre_hp("OK:MELEE_ATTACK|target:X|enemy HP:100 -> 80/100|your HP:1") == 100
        assert _extract_pre_hp("OK:RANGE_ATTACK|target:X|pre_hp:66/100|your HP:100") == 66
