"""The wait must read the game's own "can the turn end", not count units.

`wait-for-human.py` is the guard the `-HumanMilitary` division depends on, because `end_turn` does
not refuse while a unit has movement - an `ENDTURN_BLOCKING_UNITS` blocker is auto-resolved by
`_sweep_unmoved_units` (`src/civ_mcp/end_turn.py:3613-3643`), which fortifies and skips and advances
the turn.

Two wrong versions came before this one, and both are pinned below:

1. It waited on `moves_remaining > 0`. A unit parked by a skip (`ACTIVITY_HOLD`), one on alert
   (`ACTIVITY_SENTRY`), one asleep and one running an operation all keep their movement for the rest
   of the turn *and across turns* while the engine reports them as unable to act. Measured on the
   live match: 10 military units had movement and **9 of them could not act**, so the wait would
   never have returned.

2. It waited on a *recomputed* predicate at all. The game raises `ENDTURN_BLOCKING_UNITS` while any
   unit still has moves and drops it the moment the turn can end - what `get_notifications` prints
   as `Command Units -> Units have moves remaining`. Measured live on turn 335: the same session's
   first `get_notifications` carried that entry and its second did not, so the state is readable and
   flips exactly when the human finishes. `decide()` is that rule, and it is the only thing that
   decides.

**`UI.CanEndTurn()` looks like the same signal and is not.** Measured on turn 337, three consecutive
reads, all identical:

    TURN|337
    CANEND|ok=true|value=true
    BLOCKERS|count=1|ENDTURN_BLOCKING_UNITS

It is true *while* the units blocker is up, because it means "the End Turn button is pressable"
rather than "no unit has moves" - the MCP's own `end_turn` depends on that, logging
`UI.CanEndTurn()=true despite blockers ... proceeding` (`src/civ_mcp/end_turn.py:3697`). A wait built
on it would release immediately and hand the session back the silent sweep. The script reads it only
to report it, which is why `decide()` takes the blocker set and nothing else.
"""

from __future__ import annotations

import asyncio
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "wait_for_human", ROOT / ".tools" / "wait-for-human.py"
)
wait_for_human = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wait_for_human)

UNITS = "ENDTURN_BLOCKING_UNITS"


# --- the rule: the game's blocker decides -------------------------------------------------------


def test_no_blocker_means_the_turn_can_end() -> None:
    assert wait_for_human.decide({}) == "go"


def test_the_units_blocker_means_wait_for_the_human() -> None:
    assert wait_for_human.decide({UNITS: 1}) == "wait"


def test_another_blocker_alone_is_the_agents_own_work_not_a_reason_to_wait() -> None:
    """An empty queue is the agent's, so waiting on it would burn the whole timeout for nothing."""
    assert wait_for_human.decide({"ENDTURN_BLOCKING_PRODUCTION": 1}) == "agent"
    assert wait_for_human.decide({"ENDTURN_BLOCKING_UNIT_PROMOTION": 1}) == "agent"
    assert wait_for_human.decide({"ENDTURN_BLOCKING_GOVERNOR_IDLE": 1}) == "agent"


def test_the_units_blocker_dominates_when_other_blockers_are_also_up() -> None:
    """The human's units are the gate; the agent's own work does not turn 'wait' into 'agent'."""
    assert wait_for_human.decide({UNITS: 1, "ENDTURN_BLOCKING_PRODUCTION": 2}) == "wait"
    assert wait_for_human.decide({UNITS: 3, "ENDTURN_BLOCKING_UNIT_PROMOTION": 1}) == "wait"


def test_an_unknown_blocker_is_not_treated_as_units() -> None:
    """A blocker nobody has named yet is not evidence that the human has units."""
    assert wait_for_human.decide({"ENDTURN_BLOCKING_UNKNOWN": 1}) == "agent"


# --- the live readings, verbatim -----------------------------------------------------------------


def test_the_live_turn_335_pair_now_decides_correctly() -> None:
    """The exact pair measured on the live match: one with the units blocker, one without."""
    with_units = {UNITS: 1}
    without_units = {}
    assert wait_for_human.decide(with_units) == "wait", "turn could not end"
    assert wait_for_human.decide(without_units) == "go", "turn could end - the human was finished"


# --- the detail line: which units the human still has -------------------------------------------


class Unit:
    """A `UnitInfo` with only the fields this tool reads."""

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


class FakeGameState:
    def __init__(self, units: list[Unit]) -> None:
        self._units = units

    async def get_units(self) -> list[Unit]:
        return self._units


def holding(units: list[Unit]) -> list[Unit]:
    return asyncio.run(wait_for_human.holding(FakeGameState(units)))


@pytest.mark.parametrize(
    "activity",
    ["ACTIVITY_HOLD", "ACTIVITY_SENTRY", "ACTIVITY_OPERATION", "ACTIVITY_SLEEP"],
)
def test_a_unit_that_already_has_its_order_is_not_listed_as_the_humans(activity: str) -> None:
    """The first bug, kept as a regression: movement is kept, but the engine says it cannot act."""
    parked = Unit(
        "UNIT_FIELD_CANNON",
        combat_strength=50,
        moves_remaining=2.0,
        ready_to_move=False,
        activity=activity,
    )
    assert wait_for_human.can_still_act(parked) is False
    assert holding([parked]) == []


def test_the_live_ten_unit_reading_lists_one_unit_not_ten() -> None:
    units = [
        Unit("UNIT_SPEC_OPS", combat_strength=60, moves_remaining=0.5, ready_to_move=True),
        Unit("UNIT_FIELD_CANNON", combat_strength=50, moves_remaining=2.0, ready_to_move=False,
             activity="ACTIVITY_SENTRY"),
        Unit("UNIT_BOMBARD", combat_strength=60, moves_remaining=2.0, ready_to_move=False,
             activity="ACTIVITY_SENTRY"),
        Unit("UNIT_SPEARMAN", combat_strength=40, moves_remaining=2.0, ready_to_move=False,
             activity="ACTIVITY_SENTRY"),
        Unit("UNIT_MECHANIZED_INFANTRY", combat_strength=90, moves_remaining=4.0,
             ready_to_move=False, activity="ACTIVITY_OPERATION"),
        Unit("UNIT_CARAVEL", combat_strength=55, moves_remaining=5.0, ready_to_move=False,
             activity="ACTIVITY_OPERATION"),
        Unit("UNIT_RANGER", combat_strength=55, moves_remaining=3.0, ready_to_move=False,
             activity="ACTIVITY_HOLD"),
        Unit("UNIT_GREAT_ADMIRAL", moves_remaining=2.0, ready_to_move=False,
             activity="ACTIVITY_HOLD"),
        Unit("UNIT_GREAT_GENERAL", moves_remaining=2.25, ready_to_move=False,
             activity="ACTIVITY_HOLD"),
        Unit("UNIT_GREAT_GENERAL", moves_remaining=0.5, ready_to_move=False,
             activity="ACTIVITY_HOLD"),
    ]
    assert sum(1 for u in units if u.moves_remaining > 0) == 10, "the old, wrong predicate"
    waiting = holding(units)
    assert [u.unit_type for u in waiting] == ["UNIT_SPEC_OPS"]


def test_a_unit_that_can_still_act_is_listed() -> None:
    free = Unit("UNIT_TANK", combat_strength=85, moves_remaining=3.0, ready_to_move=True)
    assert holding([free]) == [free]


@pytest.mark.parametrize("unit_type", ["UNIT_GREAT_GENERAL", "UNIT_GREAT_ADMIRAL"])
def test_a_commander_is_the_humans_despite_no_combat_strength(unit_type: str) -> None:
    commander = Unit(unit_type, combat_strength=0, moves_remaining=6.0, ready_to_move=True)
    assert wait_for_human.is_the_humans(commander) is True


@pytest.mark.parametrize(
    "unit_type",
    ["UNIT_BUILDER", "UNIT_SETTLER", "UNIT_TRADER", "UNIT_SCIENTIST", "UNIT_PROPHET"],
)
def test_a_civilian_is_not_the_humans(unit_type: str) -> None:
    assert wait_for_human.is_the_humans(Unit(unit_type, combat_strength=0)) is False
