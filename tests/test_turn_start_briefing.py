"""The start-of-turn briefing: is the plan actually being executed?

`end_turn` can only say that a turn went by without progress. The briefing says it at the
start of the turn, while there is still one to change, and it answers the question a standing
rule cannot: the rules are recomputed for the last forty diary rows, so each failing rule
carries a streak ("failing for 21 turns") and a rule that has just been satisfied shows up as
cleared. With the last turn's measured output next to that, "the plan is not being executed"
stops being a feeling.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


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


class FakeSnapshot:
    def __init__(self, turn, units):
        self.turn = turn
        self.units = units


class FakeGameState:
    def __init__(self, turn, units):
        self.turn = turn
        self.units = units
        self._last_snapshot = FakeSnapshot(turn, units)
        self.snapshots_taken = 0

    async def get_game_identity(self):
        return ("china", -1894041591)

    async def _take_snapshot(self):
        self.snapshots_taken += 1
        return self._last_snapshot


def row(turn: int, **over) -> dict:
    base = {
        "turn": turn,
        "is_agent": True,
        "pid": 0,
        "science": 5.0 + turn * 0.1,
        "culture": 6.0,
        "gold_per_turn": 12.0,
        "military": 40,
        "pop": 12,
        "cities": 3,
        "districts": 2,
        "improvements": 6,
        "wonders": 0,
        "territory": 30,
        "techs_completed": 8,
        "civics_completed": 6,
        "unit_composition": {"ARCHER": 1, "WARRIOR": 1, "BUILDER": 1},
        "techs": [],
        "civics": [],
        "reflections": {},
    }
    base.update(over)
    return base


@pytest.fixture()
def diary(monkeypatch):
    """A diary whose rules never move, so the streak and the verdict are deterministic.

    The diary and the retirement state both live in a scratch directory of their own: an
    earlier version wrote the state into the shared `.tools/` directory, so the *second*
    consecutive test run started with the ram goal already achieved and failed.
    """
    import shutil

    scratch = pathlib.Path(".tools") / f"_briefing_{uuid.uuid4().hex}"
    scratch.mkdir(parents=True)
    path = scratch / "diary_test.jsonl"
    rows = [row(t) for t in range(45, 61)]
    # The governing plan for T60 is the one written while T59 was being played, so that is
    # where the fixture puts it - the same place a live diary would have it.
    rows[-2]["reflections"] = {
        "planning": "T59: builder mines (51,25), settler waits for the warrior to die",
        "hypothesis": "city 5 lands ~T62",
    }
    path.write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8"
    )
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(scratch))
    monkeypatch.setattr(et, "_agent_diary_rows", lambda gs: _rows(path))
    yield path
    shutil.rmtree(scratch, ignore_errors=True)


async def _rows(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_the_briefing_names_the_rules_and_their_streak(diary):
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER"), 2: unit(2, "UNIT_WARRIOR")})
    text = asyncio.run(et.turn_start_briefing(gs, 60))
    assert "TURN START (T60)" in text
    assert "[ram-tower-before-civil-engineering]" in text
    assert "failing for" in text
    # The army never had a wonder or a ram across the 45..60 rows, so the streaks are long.
    assert "failing for 16 turn(s)" in text


def test_it_quotes_the_plan_it_is_checking_against(diary):
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")})
    text = asyncio.run(et.turn_start_briefing(gs, 60))
    assert "builder mines (51,25)" in text
    assert "city 5 lands ~T62" in text


def test_it_shows_what_the_last_turn_bought(diary):
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")})
    text = asyncio.run(et.turn_start_briefing(gs, 60))
    assert "the last turn bought:" in text
    assert "science +0.1" in text


def test_a_stalled_plan_is_called_out(diary):
    # Same rules failing, nothing cleared, and the only movement is +0.1 science.
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")})
    text = asyncio.run(et.turn_start_briefing(gs, 60))
    assert "VERDICT" in text
    assert "Change one thing this turn" in text


def test_achieving_a_goal_is_reported_as_achieved(monkeypatch, diary):
    # The ram rule is a goal (`once: true`), so satisfying it retires the rule and the
    # briefing says so - rather than reporting it as merely "cleared".
    path = diary
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[-1]["unit_composition"] = {"ARCHER": 1, "BATTERING_RAM": 1}
    path.write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8"
    )
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER"), 2: unit(2, "UNIT_BATTERING_RAM")})
    text = asyncio.run(et.turn_start_briefing(gs, 60))
    assert "ACHIEVED this turn" in text and "ram-tower-before-civil-engineering" in text
    assert "the failing set is moving" in text


def test_a_standing_rule_that_is_fixed_shows_as_cleared(monkeypatch, diary):
    # idle-district-slot is standing: it can go idle again, so fixing it is progress, not
    # retirement. Both ends of the comparison must be inside the rule's gate (turn >= 60),
    # which is why this looks at T60 -> T61 rather than T59 -> T60.
    path = diary
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[-2]["districts"], rows[-2]["pop"] = 2, 12  # T59 - below the gate, not evaluated
    rows[-1]["districts"], rows[-1]["pop"] = 2, 12  # T60 - failing
    last = dict(rows[-1])
    last["turn"] = 61
    last["districts"] = 4  # T61 - 4 slots for pop 12 is exactly the allowance
    rows.append(last)
    path.write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8"
    )
    gs = FakeGameState(61, {1: unit(1, "UNIT_ARCHER")})
    text = asyncio.run(et.turn_start_briefing(gs, 61))
    assert "CLEARED since your last entry" in text
    assert "idle-district-slot" in text.split("CLEARED")[1]


def test_losing_an_army_is_not_progress(monkeypatch, diary):
    # A turn that lost 38 military and built nothing is not "the plan moving".
    path = diary
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[-1]["military"] = rows[-2]["military"] - 38
    rows[-1]["science"] = rows[-2]["science"] + 0.1
    path.write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8"
    )
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")})
    text = asyncio.run(et.turn_start_briefing(gs, 60))
    assert "military -38" in text
    assert "Change one thing this turn" in text


def test_a_plan_recorded_for_this_turn_is_quoted_too(diary):
    # A resumed or re-planned turn: the newer statement of intent is the current row's.
    path = diary
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[-1]["reflections"] = {"planning": "T60 revised: buy a builder with the 320 gold"}
    path.write_text(
        "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8"
    )
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")})
    text = asyncio.run(et.turn_start_briefing(gs, 60))
    assert "you planned this turn (planning): T60 revised" in text
    assert "you planned last turn (planning): T59:" in text


def test_it_reports_once_per_turn(diary):
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")})
    first = asyncio.run(et.turn_start_briefing(gs, 60))
    second = asyncio.run(et.turn_start_briefing(gs, 60))
    assert first and second == "", "a second call in the same turn must stay quiet"
    assert asyncio.run(et.turn_start_briefing(gs, 61)), "and the next turn speaks again"


def test_a_missing_check_file_is_silent(monkeypatch):
    monkeypatch.setenv("CIV_MCP_TURN_CHECKS", "does/not/exist.md")
    assert asyncio.run(et.turn_start_briefing(FakeGameState(60, {}), 60)) == ""
