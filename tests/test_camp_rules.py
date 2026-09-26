"""The camp metric, and the rule that stops a camp being ignored.

A barbarian camp is the one enemy asset the adapter could not see in a normal read: it is not a unit,
so no contact metric counts it, and the only detector in the codebase is the post-move visibility
probe - which announces a camp on the turn a unit first *reveals* the tile and never again. Measured
consequence on the T59 replay: the camp beside 北京 spawned the Spearman that forced a 160-gold
Warrior purchase at T65, and nothing in the turn result had mentioned a camp at all.

The human's instruction (2026-09-26) is that a camp is a `tactics/07` target. These tests pin the two
things that make that true mechanically: `_camps_within_3` finds camps through `get_map_area` (no new
Lua), and `answer-the-camp` fails while a camp is in range and nothing attacked.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks as tc  # noqa: E402
from civ_mcp.lua.models import TileInfo  # noqa: E402

RULE = """<!-- check
id: answer-the-camp
when: metric(camps_within_3) >= 1
require: metric(attacks_this_turn) >= 1
message: a camp is in range
-->
"""


class FakeCity:
    def __init__(self, name: str, x: int, y: int) -> None:
        self.name = name
        self.x = x
        self.y = y


class FakeArea:
    def __init__(self, tiles: list[TileInfo]) -> None:
        self.tiles = tiles


def tile(x: int, y: int, improvement: str | None = None) -> TileInfo:
    return TileInfo(
        x=x, y=y, terrain="TERRAIN_GRASS", feature=None, resource=None, is_hills=False,
        is_river=False, is_coastal=False, improvement=improvement, owner_id=-1,
    )


class FakeGameState:
    """`get_map_area` answers per city; anything else raises, as a dead scan would."""

    def __init__(self, areas: dict[tuple[int, int], list[TileInfo]]) -> None:
        self.areas = areas
        self.calls: list[tuple[int, int]] = []

    async def get_cities(self):
        return [FakeCity("北京", 57, 29), FakeCity("上海", 52, 24)], []

    async def get_map_area(self, x: int, y: int, radius: int = 1):
        self.calls.append((x, y))
        return FakeArea(self.areas.get((x, y), []))


class BrokenGameState(FakeGameState):
    async def get_cities(self):
        raise RuntimeError("no connection")


def run(coro):
    return asyncio.run(coro)


class TestTheCampScan:
    def test_a_camp_beside_a_city_is_counted(self):
        gs = FakeGameState({(57, 29): [tile(57, 29), tile(60, 30, "IMPROVEMENT_BARBARIAN_CAMP")]})
        assert run(et._camps_within_3(gs)) == 1

    def test_every_city_is_scanned(self):
        gs = FakeGameState(
            {
                (57, 29): [tile(60, 30, "IMPROVEMENT_BARBARIAN_CAMP")],
                (52, 24): [tile(50, 22, "IMPROVEMENT_BARBARIAN_CAMP")],
            }
        )
        assert run(et._camps_within_3(gs)) == 2
        assert gs.calls == [(57, 29), (52, 24)]

    def test_the_same_camp_seen_from_two_cities_is_counted_once(self):
        gs = FakeGameState(
            {
                (57, 29): [tile(60, 30, "IMPROVEMENT_BARBARIAN_CAMP")],
                (52, 24): [tile(60, 30, "IMPROVEMENT_BARBARIAN_CAMP")],
            }
        )
        assert run(et._camps_within_3(gs)) == 1

    def test_other_improvements_are_not_camps(self):
        gs = FakeGameState(
            {
                (57, 29): [
                    tile(55, 27, "IMPROVEMENT_CAMP"),        # a deer camp - ours
                    tile(51, 28, "IMPROVEMENT_LUMBER_MILL"),
                ]
            }
        )
        assert run(et._camps_within_3(gs)) == 0

    def test_a_dead_read_is_zero_not_an_exception(self):
        # Zero switches the rule off; raising would cost the whole check run.
        assert run(et._camps_within_3(BrokenGameState({}))) == 0

    def test_the_metric_is_in_the_fail_closed_key_list(self):
        # `_contact_metrics`' failure path zeroes exactly these keys.
        assert "camps_within_3" in et._CONTACT_METRIC_KEYS


class TestTheRule:
    def context(self, **metrics) -> tc.CheckContext:
        return tc.CheckContext(turn=70, units={}, metrics=metrics, researched=frozenset())

    def test_it_fails_while_a_camp_is_in_range_and_nothing_attacked(self):
        result = tc.run_checks(RULE, self.context(camps_within_3=1, attacks_this_turn=0))
        assert [check.check_id for check, _ in result.failures] == ["answer-the-camp"]

    def test_an_attack_answers_it(self):
        result = tc.run_checks(RULE, self.context(camps_within_3=1, attacks_this_turn=1))
        assert not result.failures
        assert "answer-the-camp" in result.passed

    def test_no_camp_switches_the_rule_off(self):
        result = tc.run_checks(RULE, self.context(camps_within_3=0, attacks_this_turn=0))
        assert not result.failures
        assert "answer-the-camp" in result.skipped

    def test_a_server_without_the_camp_metric_reports_rather_than_lies(self):
        # This is why the rule is staged rather than live: an older server raises on the unknown
        # key, and the check comes back as an un-evaluable *failure* - every turn, unfixable.
        result = tc.run_checks(RULE, self.context(attacks_this_turn=0))
        assert [check.check_id for check, _ in result.failures] == ["answer-the-camp"]
        assert "not available" in result.failures[0][1]

    def test_the_rule_is_live_now_that_the_server_computes_the_metric(self):
        # It shipped staged while an older server was playing: the rule file is re-read every turn,
        # but the metric set lives in the MCP process, so an unknown key turns the rule into an
        # un-evaluable failure every turn. The server that computes `camps_within_3` is the one the
        # block was cut into, so the staging folder must no longer hold it and the live file must.
        live, _ = tc.load_checks()
        assert "id: answer-the-camp" in live
        assert "camps_within_3" in live
        assert not (ROOT / "prompts" / "checks" / "pending" / "answer-the-camp.md").exists()

    def test_the_supply_rule_was_activated_in_the_same_batch(self):
        live, _ = tc.load_checks()
        assert "id: cut-the-supply" in live
        assert "enemy_supply_uncut_with_idle" in live
        assert "enemy_supply_uncut_with_idle" in et._CONTACT_METRIC_KEYS
        assert not (ROOT / "prompts" / "checks" / "pending" / "cut-the-supply.md").exists()
