"""Hold the turn verifier to the distances the game printed, and to the failure it exists for.

`hex_distance` is the one piece of arithmetic here, and hand arithmetic on this grid has been wrong
four times in this repo, so it is pinned against six distances taken from a real `get_staging_plan`
reply for Tyre (26,11) in china--1894041591 - not against a re-derivation of the same formula.

The rest pins the classifier: which replies mean "the write did not take effect" and which mean "the
march leg ended normally", and then the whole verdict against the measured T291->T293 run, which
exited 0 while six units were ordered onto occupied tiles, two waypoints were water, three cities
went idle and a rule fired.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load():
    """`.tools/turn-verify.py` - a hyphen is not an importable name, so load it by path.

    It has to go into `sys.modules` *before* execution: `@dataclass` looks its own module up by
    `cls.__module__` to resolve the annotations, and an unregistered module makes that lookup
    return None.
    """
    path = ROOT / ".tools" / "turn-verify.py"
    spec = importlib.util.spec_from_file_location("turn_verify_tool", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["turn_verify_tool"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


tv = _load()

# (x, y) -> the distance `get_staging_plan(26, 11)` printed for a unit standing there.
GAME_PRINTED_DISTANCES = {
    (68, 21): 47,
    (50, 13): 25,
    (48, 13): 23,
    (48, 12): 22,
    (44, 24): 24,
}


@pytest.mark.parametrize("origin,expected", sorted(GAME_PRINTED_DISTANCES.items()))
def test_hex_distance_matches_the_game(origin, expected):
    assert tv.hex_distance(origin, (26, 11)) == expected


def test_hex_distance_is_symmetric_and_zero_on_the_same_tile():
    assert tv.hex_distance((26, 11), (68, 21)) == tv.hex_distance((68, 21), (26, 11))
    assert tv.hex_distance((26, 11), (26, 11)) == 0


def test_the_march_check_closes_distance_on_the_right_measure():
    """One tile west at y=11 is one tile closer; the check has to see that."""
    assert tv.hex_distance((30, 11), (26, 11)) < tv.hex_distance((31, 11), (26, 11))


class TestWhatCountsAsAFailedWrite:
    @pytest.mark.parametrize(
        "reply",
        [
            "Error: SILENT_FAILURE|BUILDING_MONUMENT appeared to set but the game engine did not "
            "persist it (NOT_SET|current=NONE|expected=BUILDING_MONUMENT)",
            "Error: MISSING_COORDS|DISTRICT_CAMPUS is a district and requires target_x/target_y",
            "Error: STACKING_CONFLICT|Friendly UNIT_FIELD_CANNON already on (43,17).",
            "Error: NO_MOVES|Unit has no movement points remaining this turn.",
            "CAPTURE_MOVE|33,15|from:48,13|now_at:48,13|BLOCKED (foreign territory (腓尼基))",
        ],
    )
    def test_hard_failures_are_recognised(self, reply):
        assert tv.is_hard_failure(reply)

    @pytest.mark.parametrize(
        "reply",
        [
            # The ordinary end of a march leg: the unit walked as far as its movement allowed.
            "MOVING_TO|65,21|from:70,21|now_at:69,21|(moved dx:-1 dy:+0)|STOPPED_MID_PATH "
            "(moves exhausted)",
            "MOVING_TO|60,21|from:61,22|now_at:60,21|(moved dx:-1 dy:-1)",
            "PRODUCING|BUILDING_WORKSHOP|3 turns",
            "RANGE_ATTACK|target:苏尔 (city) at (26,11)|pre_hp:200/200|city hp: 200/200, "
            "walls: 95/100",
        ],
    )
    def test_normal_results_are_not_failures(self, reply):
        assert not tv.is_hard_failure(reply), (
            "flagging these would mark every turn of a long march as broken"
        )


class TestWhatCountsAsAnAcceptedStop:
    def test_territory_we_may_not_enter_is_the_maps_business(self):
        assert tv.is_accepted_stop(
            "BLOCKED (foreign territory (腓尼基) - need Open Borders via propose_trade)"
        )
        assert tv.is_accepted_stop("BLOCKED (city-state territory (格拉纳达))")

    def test_water_is_our_own_bad_waypoint(self):
        """A waypoint on water is a target we chose wrongly, so it must NOT be accepted."""
        assert not tv.is_accepted_stop("BLOCKED (water tile (can embark))")


class TestParsingTheTurnResult:
    def test_check_failed_lines_are_named(self):
        text = (
            "  >> CHECK FAILED [finish-the-wounded]: An enemy within 2 tiles is at 20 HP or less\n"
            "  >> CHECK FAILED [use-your-attacks]: ...\n"
        )
        assert tv.check_failures(text) == ["finish-the-wounded", "use-your-attacks"]

    def test_blockers_are_named(self):
        text = (
            "Cannot end turn: diplomacy encounter pending with 印度 (甘地).\n"
            "  >> Research complete: 激光! Now: None.\n"
            "  >> 诺夫哥罗德 finished building DISTRICT_CAMPUS. Now: nothing.\n"
        )
        found = tv.blockers_in(text)
        assert "Cannot end turn" in found
        assert "Research complete" in found
        assert "Now: nothing" in found

    def test_a_clean_result_has_no_blockers(self):
        assert tv.blockers_in("Turn 292 -> 293 | Score: 1345") == []


class _City:
    def __init__(self, name, building, turns=5, pop=10, prod=20.0):
        self.name = name
        self.currently_building = building
        self.production_turns_left = turns
        self.population = pop
        self.production = prod


class TestTheMeasuredT291ToT293Run:
    """The run that exited 0 while all of this was true. Every problem must be named."""

    def _verdict(self):
        return tv.verdict_from(
            turn_before=291,
            turn_after=293,
            expected=293,
            engine_turn=293,
            save_name="0_MCP_0292",
            save_turn=293,
            cities=[
                _City("诺夫哥罗德", "NOTHING"),
                _City("阿拜多斯", "NOTHING"),
                _City("亚历山大", "NOTHING"),
                _City("西安", "BUILDING_WORKSHOP"),
            ],
            replies=[
                "Error: STACKING_CONFLICT|Friendly UNIT_FIELD_CANNON already on (43,17).",
                "Error: STACKING_CONFLICT|Friendly UNIT_RANGER already on (38,22).",
                "MOVING_TO|64,14|from:68,15|now_at:68,15|BLOCKED (water tile (can embark))",
                "MOVING_TO|44,18|from:46,21|now_at:43,17|(moved dx:-3 dy:-4)|STOPPED_MID_PATH",
            ],
            end_text=(
                "  >> Research complete: 激光! Now: None.\n"
                "  >> CHECK FAILED [finish-the-wounded]: An enemy within 2 tiles is at 20 HP\n"
            ),
            march=[
                (17, (46, 21), (44, 18), (43, 17), "STOPPED_MID_PATH (moves exhausted)"),
                (15, (68, 15), (64, 14), (68, 15), "BLOCKED (water tile (can embark))"),
            ],
        )

    def test_the_run_is_reported_as_failed(self):
        assert not self._verdict().ok, (
            "this run advanced 291 -> 293 and exited 0; the verifier exists to call it failed"
        )

    def test_every_problem_is_named_separately(self):
        problems = " | ".join(self._verdict().problems)
        assert "STACKING_CONFLICT" in problems
        assert "empty queue" in problems
        assert "Research complete" in problems
        assert "water" in problems

    def test_a_bad_check_line_is_reported_but_does_not_by_itself_fail_the_turn(self):
        """A failing rule is sometimes accepted deliberately; the report names it so the diary can
        say why. It is not the verifier's place to decide the doctrine."""
        verdict = self._verdict()
        assert verdict.checks_failed == ["finish-the-wounded"]
        assert "[finish-the-wounded]" not in " ".join(verdict.problems)


class TestACleanTurn:
    def test_a_turn_that_did_everything_right_is_ok(self):
        verdict = tv.verdict_from(
            turn_before=293,
            turn_after=294,
            expected=294,
            engine_turn=294,
            save_name="0_MCP_0294",
            save_turn=294,
            cities=[_City("西安", "BUILDING_FACTORY"), _City("上海", "DISTRICT_INDUSTRIAL_ZONE")],
            replies=[
                "PRODUCING|BUILDING_FACTORY|2 turns",
                "MOVING_TO|40,18|from:46,21|now_at:41,18|(moved dx:-5 dy:-3)|STOPPED_MID_PATH",
            ],
            end_text="Turn 293 -> 294 | Score: 1350",
            march=[(17, (46, 21), (40, 18), (41, 18), "STOPPED_MID_PATH")],
        )
        assert verdict.ok, verdict.problems


class TestTheWitness:
    def test_one_source_is_not_a_witness(self):
        """The engine agreeing with itself proves nothing; the save file is the second opinion."""
        verdict = tv.verdict_from(
            turn_before=293, turn_after=294, expected=294, engine_turn=294,
            save_name=None, save_turn=None,
        )
        assert not verdict.witnessed
        assert any("not witnessed" in p for p in verdict.problems)

    def test_two_sources_that_disagree_are_reported(self):
        verdict = tv.verdict_from(
            turn_before=293, turn_after=294, expected=294, engine_turn=294,
            save_name="0_MCP_0293", save_turn=293,
        )
        assert not verdict.witnessed
        assert any("engine=294" in p and "save=0_MCP_0293=293" in p for p in verdict.problems)

    def test_two_sources_that_agree_are_a_witness(self):
        verdict = tv.verdict_from(
            turn_before=293, turn_after=294, expected=294, engine_turn=294,
            save_name="0_MCP_0294", save_turn=294,
        )
        assert verdict.witnessed
