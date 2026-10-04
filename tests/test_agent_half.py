"""Whose move is it? The answer is derived from the board, and these pin the whole rule.

The `-HumanMilitary` division is a sequence - the agent moves first every turn, the human commands
the military units, the Great Generals and the Great Admirals after it - so the human needs one
fact the loop never gave them: "can I start yet?". `end_turn`'s units blocker cannot supply it,
because `ENDTURN_BLOCKING_UNITS` is raised while *any* unit still has moves and is therefore up at
the start of nearly every turn regardless of whose move it is.

`civ_mcp.agent_half` derives the split instead. It is recomputed on every `get_notifications`
(the call a waiting session makes), appended to that tool's answer as `WHOSE MOVE|`, and written as
`agent-half.txt` in the run directory for the human to read.

The case that matters most is the third test below: a Great General and a Builder both holding
movement. The blocker is up, the session must not wait on the human, and a report that only counted
movement - or that treated every unit as the human's - would have told the human "your move" while
one of the session's own builders was still un-ordered.
"""

from __future__ import annotations

import asyncio
import importlib.util
import pathlib

import pytest

from civ_mcp import agent_half

ROOT = pathlib.Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "wait_for_human_shared", ROOT / ".tools" / "wait-for-human.py"
)
wait_for_human = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wait_for_human)


class Unit:
    """A `UnitInfo` with only the fields this module reads."""

    def __init__(
        self,
        unit_type: str,
        *,
        combat_strength: int = 0,
        moves_remaining: float = 2.0,
        ready_to_move: bool = True,
        activity: str = "ACTIVITY_AWAKE",
        unit_index: int = 1,
        x: int = 5,
        y: int = 5,
    ) -> None:
        self.unit_type = unit_type
        self.combat_strength = combat_strength
        self.moves_remaining = moves_remaining
        self.ready_to_move = ready_to_move
        self.activity = activity
        self.unit_index = unit_index
        self.x = x
        self.y = y


class FakeConn:
    def __init__(self, turn: int | None) -> None:
        self._turn = turn

    async def execute_write(self, lua: str) -> list[str]:
        if self._turn is None:
            return ["---END---"]
        return [f"TURN|{self._turn}", "---END---"]


class FakeGameState:
    def __init__(self, units: list[Unit], turn: int | None = 351) -> None:
        self._units = units
        self.conn = FakeConn(turn)

    async def get_units(self) -> list[Unit]:
        return self._units


class BrokenGameState:
    async def get_units(self) -> list[Unit]:
        raise RuntimeError("the tuner went away")


def general(**kwargs) -> Unit:
    return Unit("UNIT_GREAT_GENERAL", combat_strength=0, **kwargs)


def builder(**kwargs) -> Unit:
    return Unit("UNIT_BUILDER", combat_strength=0, **kwargs)


def armor(**kwargs) -> Unit:
    return Unit("UNIT_MODERN_ARMOR", combat_strength=95, **kwargs)


# --- the predicate is the division ---------------------------------------------------------------


def test_a_military_unit_is_the_humans() -> None:
    assert agent_half.is_the_humans(armor()) is True


@pytest.mark.parametrize("unit_type", ["UNIT_GREAT_GENERAL", "UNIT_GREAT_ADMIRAL"])
def test_a_commander_is_the_humans_despite_no_combat_strength(unit_type: str) -> None:
    """The trap: a general has `combat_strength == 0`, so the combat test alone misses it."""
    assert agent_half.is_the_humans(Unit(unit_type)) is True


@pytest.mark.parametrize(
    "unit_type",
    ["UNIT_BUILDER", "UNIT_SETTLER", "UNIT_TRADER", "UNIT_GREAT_SCIENTIST", "UNIT_GREAT_MERCHANT"],
)
def test_everything_else_is_the_agents(unit_type: str) -> None:
    assert agent_half.is_the_humans(Unit(unit_type)) is False


@pytest.mark.parametrize(
    "activity", ["ACTIVITY_HOLD", "ACTIVITY_SENTRY", "ACTIVITY_OPERATION", "ACTIVITY_SLEEP"]
)
def test_a_unit_that_already_has_its_order_can_no_longer_act(activity: str) -> None:
    """Movement is kept across turns, so `moves_remaining > 0` is not the test. Measured: 10 units
    had movement and 9 of them could not act."""
    parked = armor(moves_remaining=2.0, ready_to_move=False, activity=activity)
    assert agent_half.can_still_act(parked) is False


def test_the_wait_tool_and_the_server_share_one_predicate() -> None:
    """Two copies of "whose unit is this" would drift; the tool imports the module's."""
    assert wait_for_human.is_the_humans is agent_half.is_the_humans
    assert wait_for_human.can_still_act is agent_half.can_still_act


# --- the verdict ---------------------------------------------------------------------------------


def test_only_the_humans_units_left_is_your_move() -> None:
    agent, human = agent_half.split([armor(moves_remaining=5.0), general(moves_remaining=4.0)])
    assert agent == []
    assert len(human) == 2
    assert agent_half.verdict(agent, human) == "your move"


def test_one_of_the_agents_own_units_left_is_agent_working() -> None:
    """The case the whole feature exists for: the blocker is up, and it is not the human's turn."""
    agent, human = agent_half.split([general(moves_remaining=4.0), builder(moves_remaining=1.5)])
    assert [u.unit_type for u in agent] == ["UNIT_BUILDER"]
    assert [u.unit_type for u in human] == ["UNIT_GREAT_GENERAL"]
    assert agent_half.verdict(agent, human) == "agent working"


def test_nobody_left_means_the_turn_can_end() -> None:
    agent, human = agent_half.split([armor(moves_remaining=0.0), builder(moves_remaining=0.0)])
    assert (agent, human) == ([], [])
    assert agent_half.verdict(agent, human) == "turn can end"


# --- what the human reads ------------------------------------------------------------------------


def test_the_file_says_your_move_and_lists_the_humans_units() -> None:
    text = agent_half.render(
        351,
        [armor(moves_remaining=6.0, x=20, y=17), general(moves_remaining=4.0, x=32, y=19)],
        when=0,
    )
    assert text.startswith("T351  YOUR MOVE")
    assert "every one of them is yours" in text
    assert "UNIT_MODERN_ARMOR" in text and "( 20, 17)" in text
    assert "UNIT_GREAT_GENERAL" in text
    assert "UNIT_BUILDER" not in text


def test_the_file_says_the_agent_is_still_working_and_names_its_own_unit() -> None:
    text = agent_half.render(
        351,
        [general(moves_remaining=4.0), builder(moves_remaining=1.5, x=61, y=43)],
        when=0,
    )
    assert text.startswith("T351  AGENT STILL WORKING")
    assert "its own, not yours" in text
    assert "UNIT_BUILDER" in text and "( 61, 43)" in text
    assert "nothing is waiting on you yet" in text


def test_the_file_says_the_turn_can_end_when_nobody_can_act() -> None:
    text = agent_half.render(351, [armor(moves_remaining=0.0)], when=0)
    assert "THE TURN CAN END" in text
    assert "the units blocker is down" in text


def test_the_summary_is_one_line_for_the_session() -> None:
    line = agent_half.summary(351, [builder(moves_remaining=1.5, x=61, y=43)])
    assert "\n" not in line
    assert line.startswith("WHOSE MOVE|agent working|T351:")
    assert "UNIT_BUILDER at (61,43)" in line

    line = agent_half.summary(351, [armor(moves_remaining=6.0)])
    assert line.startswith("WHOSE MOVE|your move|T351:")
    assert "wait for them" in line


# --- where it lands, and never failing the tool that carries it -----------------------------------


def test_the_report_lands_in_the_run_directory(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(tmp_path))
    path = agent_half.write("T351  YOUR MOVE\n")
    assert path == tmp_path / agent_half.REPORT_NAME
    assert path.read_text(encoding="utf-8") == "T351  YOUR MOVE\n"


def test_a_report_that_cannot_be_written_returns_none_instead_of_raising(monkeypatch, tmp_path) -> None:
    """A side-report must never turn a working `get_notifications` into a failure."""
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(blocker / "under-a-file"))
    assert agent_half.write("anything") is None


def test_report_for_writes_the_file_and_returns_the_line(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(tmp_path))
    line = asyncio.run(agent_half.report_for(FakeGameState([builder(moves_remaining=1.5)])))
    assert line.startswith("WHOSE MOVE|agent working|T351:")
    written = (tmp_path / agent_half.REPORT_NAME).read_text(encoding="utf-8")
    assert written.startswith("T351  AGENT STILL WORKING")
    assert "UNIT_BUILDER" in written


def test_report_for_survives_a_unit_read_that_fails() -> None:
    assert asyncio.run(agent_half.report_for(BrokenGameState())) == ""


def test_report_for_still_reports_whose_move_when_the_turn_is_unreadable(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(tmp_path))
    line = asyncio.run(agent_half.report_for(FakeGameState([armor()], turn=None)))
    assert line.startswith("WHOSE MOVE|your move|T?:")
    assert (tmp_path / agent_half.REPORT_NAME).read_text(encoding="utf-8").startswith("T?  YOUR MOVE")
