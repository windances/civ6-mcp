"""Partial moves: the count, the metric, the turn-result line, and the staged rule.

Measured T228-T299: **232 `STOPPED_MID_PATH` results across 72 turns** (T257-T259 alone: 15, 17, 19;
T234 ordered eight units and took eight stops one to three tiles short), and every staging plan left
6-9 units unplaced (T254: 9 of 10). The plan assigns distinct tiles but said nothing about the order of
the *calls*, so a column ordered nearest-first queues behind itself. The count now exists, the turn
result names it, and the rule that enforces it is staged until a server computes the metric.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PENDING = ROOT / "prompts" / "checks" / "pending" / "issue-the-calls-furthest-first.md"
LIVE = ROOT / "prompts" / "checks" / "turn-checks.md"


class TestTheCount:
    """The metric counts **jams**, not movement budgets.

    Measured over the two experiment attempts (2026-09-29): A1 took 76 stops and A2 11, seven in ten of
    them `(moves exhausted)` - a mv2 unit crossing hills or forest - and not one named another unit. The
    rule that reads this metric (`issue-the-calls-furthest-first`) fired on A1 eight times and on A2's
    first half once, and A2's *bigger* army marching less read a lower rate, which is how a terrain meter
    behaves rather than a jam detector.
    """

    def test_a_move_the_terrain_explains_is_not_a_jam(self):
        gs = GameState(connection=None)
        for result in (
            "CAPTURE_MOVE|69,29|from:57,29|now_at:59,30|STOPPED_MID_PATH (moves exhausted)",
            "MOVE|1,2|STOPPED_MID_PATH (impassable mountain)",
            "MOVE|1,2|STOPPED_MID_PATH (water tile - land units need Shipbuilding tech to embark)",
        ):
            gs.note_move_stops(result)
        assert gs._move_stops_this_turn == 0

    def test_a_stop_with_no_reason_is_counted(self):
        # The tool could not say why the unit is not where it was sent: that is the case the rule is for.
        gs = GameState(connection=None)
        gs.note_move_stops("MOVE|1,2|STOPPED_SHORT")
        assert gs._move_stops_this_turn == 1

    def test_an_unexplained_or_suspicious_stop_is_counted(self):
        gs = GameState(connection=None)
        gs.note_move_stops("MOVE|1,2|STOPPED_MID_PATH (tile appears passable - path may be blocked by intermediate tiles)")
        gs.note_move_stops("MOVE|3,4|STOPPED_MID_PATH (blocked by friendly UNIT_WARRIOR at (3,4))")
        assert gs._move_stops_this_turn == 2

    def test_a_clean_result_and_a_blocked_one_are_not_stops(self):
        # `BLOCKED` is a refusal - the unit never set out - so it is a different failure.
        gs = GameState(connection=None)
        for result in ("MOVE|1,2|now_at:1,2", "MOVE|1,2|BLOCKED (tile is enemy territory)", "AT|1,2"):
            gs.note_move_stops(result)
        assert gs._move_stops_this_turn == 0


class TestTheMetricAndTheLine:
    def test_the_check_context_carries_the_key(self):
        assert "move_stops_this_turn" in et._CONTACT_METRIC_KEYS

    def test_a_quiet_turn_says_nothing(self):
        assert et._move_jam_event(0, 300) is None

    def test_one_or_two_stops_is_traffic(self):
        text = et._move_jam_event(2, 300)
        assert text and "MOVE JAMS (T300): 2 unit(s)" in text
        assert "queueing behind itself" not in text, "two stops is not a jam"

    def test_three_stops_names_the_order_and_the_measurement(self):
        text = et._move_jam_event(5, 300)
        assert "MOVE JAMS (T300): 5 unit(s)" in text
        assert "get_staging_plan" in text and "furthest ring tile first" in text
        assert "232" in text, "the line carries the measurement that produced it"


class TestTheRuleIsLive:
    """Cut in at T220: the session playing the T218 save runs the code that computes the metric."""

    def test_the_staged_file_is_gone(self):
        assert not PENDING.exists(), (
            "the rule moved up to turn-checks.md; a staged copy left behind is one fact in two places"
        )

    def test_it_is_in_the_live_file_with_its_measurement(self):
        live = LIVE.read_text(encoding="utf-8-sig")
        assert "id: issue-the-calls-furthest-first" in live
        assert "232 stops" in live, "the rule's message lost the measurement that produced it"
        assert "rolled back from" in live, (
            "the measurement is from the branch this save was rolled back from, and the rule has to "
            "say so: those turns are after this branch's present"
        )

    def test_the_engine_evaluates_it_in_this_build(self):
        checks = {
            check.check_id: check
            for check in turn_checks.parse_checks(LIVE.read_text(encoding="utf-8-sig"))
        }
        rule = checks["issue-the-calls-furthest-first"]
        jammed = turn_checks.CheckContext(
            turn=220, units={}, metrics={"move_stops_this_turn": 5}, researched=frozenset()
        )
        clear = turn_checks.CheckContext(
            turn=220, units={}, metrics={"move_stops_this_turn": 1}, researched=frozenset()
        )
        assert bool(turn_checks.evaluate(rule.when, jammed)) is True
        assert bool(turn_checks.evaluate(rule.require, jammed)) is False
        assert bool(turn_checks.evaluate(rule.require, clear)) is True
