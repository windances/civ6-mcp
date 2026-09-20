"""Goals retire themselves once achieved.

A reminder that has been dealt with must stop being a reminder, or the list becomes wallpaper
and the rules that still matter get lost in it. `once: true` marks a goal: the first turn its
requirement holds it is recorded (per game, in the data directory) and never evaluated again,
with one `CHECK ACHIEVED` line to close the loop. Standing rules - a district slot can go idle
again, a siege unit can die - carry no `once` and keep firing.
"""

from __future__ import annotations

import json
import pathlib
import sys
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


@pytest.fixture()
def state_dir(monkeypatch):
    """A scratch data directory, so retirement is exercised without touching the real game's
    state file (mkdtemp is not writable in this sandbox, hence the workspace path)."""
    path = pathlib.Path(".tools") / f"_check_state_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(path))
    yield path
    import shutil

    shutil.rmtree(path, ignore_errors=True)


def unit(uid: int, unit_type: str) -> m.UnitInfo:
    return m.UnitInfo(
        unit_id=uid,
        unit_index=uid,
        name=unit_type,
        unit_type=unit_type,
        x=0,
        y=0,
        moves_remaining=2,
        max_moves=2,
        health=100,
        max_health=100,
    )


def context(**metrics) -> turn_checks.CheckContext:
    base = {"wonders": 0, "districts": 0, "pop": 3, "gold_per_turn": 20,
            "improvements": 9, "cities": 3}
    base.update(metrics)
    return turn_checks.CheckContext(
        turn=60, units={1: unit(1, "UNIT_ARCHER")}, metrics=base, researched=frozenset()
    )


GOAL = """
<!-- check
id: build-a-ram
once: true
require: units(BATTERING_RAM) >= 1
message: build a ram
-->

<!-- check
id: keep-slots-filled
require: metric(districts) >= metric(pop) // 3
message: fill the district slots
-->
"""


class TestParsing:
    def test_once_is_read(self):
        checks = turn_checks.parse_checks(GOAL)
        by_id = {c.check_id: c for c in checks}
        assert by_id["build-a-ram"].once is True
        assert by_id["keep-slots-filled"].once is False

    @pytest.mark.parametrize("value", ["true", "True", "1", "yes", "on"])
    def test_truthy_spellings(self, value):
        text = f"<!-- check\nid: x\nonce: {value}\nrequire: 1 == 1\nmessage: m\n-->"
        assert turn_checks.parse_checks(text)[0].once is True

    @pytest.mark.parametrize("value", ["false", "0", "no", "", "maybe"])
    def test_everything_else_is_a_standing_rule(self, value):
        text = f"<!-- check\nid: x\nonce: {value}\nrequire: 1 == 1\nmessage: m\n-->"
        assert turn_checks.parse_checks(text)[0].once is False


class TestRunReports:
    def test_passed_and_skipped_are_kept_apart(self):
        # A rule whose `when` gate is false never applied; it must not look achieved.
        text = """
        <!-- check
        id: gated
        once: true
        when: turn() >= 90
        require: units(CATAPULT) >= 2
        message: m
        -->
        """
        run = turn_checks.run_checks(text, context())
        assert run.skipped == {"gated"}
        assert run.passed == set()
        assert run.failing_ids == set()

    def test_a_satisfied_rule_is_reported_as_passed(self):
        run = turn_checks.run_checks(GOAL, context(districts=1, pop=3))
        assert "keep-slots-filled" in run.passed
        assert "keep-slots-filled" not in run.failing_ids


class TestRetirement:
    def test_state_is_empty_to_begin_with(self, state_dir):
        assert turn_checks.load_retired("china_-1894041591") == {}

    def test_reaching_a_goal_retires_it_for_that_game(self, state_dir):
        turn_checks.retire("china_-1894041591", {"build-a-ram": 61})
        assert turn_checks.load_retired("china_-1894041591") == {"build-a-ram": 61}

    def test_another_game_starts_with_the_goal_open(self, state_dir):
        turn_checks.retire("china_-1894041591", {"build-a-ram": 61})
        assert turn_checks.load_retired("china_-1111111111") == {}

    def test_retiring_twice_merges_rather_than_replaces(self, state_dir):
        turn_checks.retire("game", {"a": 61})
        turn_checks.retire("game", {"b": 62})
        assert turn_checks.load_retired("game") == {"a": 61, "b": 62}

    def test_a_missing_state_file_is_not_an_error(self, state_dir):
        assert turn_checks.load_retired("anything") == {}
        path = state_dir / "turn-checks-state.json"
        path.write_text("not json at all", encoding="utf-8")
        assert turn_checks.load_retired("anything") == {}

    def test_the_file_is_written_atomically_and_reads_back(self, state_dir):
        turn_checks.retire("game", {"a": 61})
        raw = json.loads((state_dir / "turn-checks-state.json").read_text(encoding="utf-8"))
        assert raw == {"game": {"a": 61}}
        assert not list(state_dir.glob("*.tmp")), "the temp file is renamed, not left behind"


async def _no_rows():
    return []


class TestTheHookUsesIt:
    """The two callers must agree: what retires in end_turn must be quiet at turn start."""

    def _gs(self, units: dict, turn: int = 61):
        class Snap:
            def __init__(self):
                self.turn = turn
                self.units = units

        class GS:
            def __init__(self):
                self._last_snapshot = Snap()
                self._briefing_turn = None

            async def get_game_identity(self):
                return ("china", -1894041591)

            async def _take_snapshot(self):
                return self._last_snapshot

        return GS()

    def _wire(self, monkeypatch):
        from civ_mcp import end_turn as et

        monkeypatch.setattr(et, "_agent_diary_rows", lambda gs: _no_rows())
        # end_turn imports turn_checks inside the function, so patch the module itself.
        monkeypatch.setattr(
            turn_checks,
            "load_checks",
            lambda path=None: (GOAL, pathlib.Path("turn-checks.md")),
        )
        return et

    def test_a_goal_is_retired_and_reported_once(self, state_dir, monkeypatch):
        import asyncio

        et = self._wire(monkeypatch)
        gs = self._gs({1: unit(1, "UNIT_BATTERING_RAM")})

        events = asyncio.run(et._check_turn_checks(gs, 61, gs._last_snapshot.units, {}))
        messages = [e.message for e in events]
        assert any("CHECK ACHIEVED [build-a-ram]" in m for m in messages)
        assert not any("CHECK FAILED [build-a-ram]" in m for m in messages)
        assert turn_checks.load_retired("china_-1894041591") == {"build-a-ram": 61}

        # A later turn: the goal is silent, no failure and no second announcement.
        events2 = asyncio.run(et._check_turn_checks(gs, 62, gs._last_snapshot.units, {}))
        assert not any("build-a-ram" in e.message for e in events2)

    def test_a_standing_rule_keeps_firing_after_a_goal_retires(self, state_dir, monkeypatch):
        import asyncio

        et = self._wire(monkeypatch)
        # districts 0 for pop 3 -> the standing rule fails, and it must do so every turn.
        gs = self._gs({1: unit(1, "UNIT_BATTERING_RAM")})
        monkeypatch.setattr(et, "_latest_at_or_before", lambda rows, turn: {"pop": 3, "districts": 0})

        for turn in (61, 62, 63):
            events = asyncio.run(et._check_turn_checks(gs, turn, gs._last_snapshot.units, None))
            assert any(
                "CHECK FAILED [keep-slots-filled]" in e.message for e in events
            ), f"the standing rule went quiet at T{turn}"

    def test_the_briefing_stops_listing_a_retired_goal(self, state_dir, monkeypatch):
        import asyncio

        et = self._wire(monkeypatch)
        gs = self._gs({1: unit(1, "UNIT_BATTERING_RAM")})
        monkeypatch.setattr(
            et, "_latest_at_or_before", lambda rows, turn: {"pop": 3, "districts": 0}
        )

        first = asyncio.run(et.turn_start_briefing(gs, 61))
        assert "ACHIEVED this turn" in first and "build-a-ram" in first
        assert "[keep-slots-filled]" in first, "the standing rule is still listed"

        gs._briefing_turn = None  # next turn
        second = asyncio.run(et.turn_start_briefing(gs, 62))
        assert "build-a-ram" not in second, "an achieved goal is out of the way"
        assert "[keep-slots-filled]" in second
