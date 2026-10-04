"""The wait on the human's half must not wait on units the human has already finished with.

`wait-for-human.py` is the guard the `-HumanMilitary` division depends on, because `end_turn` does
not refuse while a unit has movement - an `ENDTURN_BLOCKING_UNITS` blocker is auto-resolved by
`_sweep_unmoved_units` (`src/civ_mcp/end_turn.py:3613-3643`), which fortifies and skips and advances
the turn. So the session must not call `end_turn` until no military unit can still act.

The first version tested `moves_remaining > 0`. That is the set `end_turn` would sweep, but it is not
the set the human still owns: a unit parked by a skip (`ACTIVITY_HOLD`), one on sentry
(`ACTIVITY_SENTRY`) and one running an operation (`ACTIVITY_OPERATION`) all keep their movement for
the rest of the turn and across turns, while the engine reports them as unable to act. Measured on
the live match when this was fixed: **10 military units had movement and 9 of them had
`ready_to_move = False`**, so the wait would never have returned 0 - it would have blocked the
session for its full 30 minute timeout on every turn and then timed out.

The two cases that must keep working are the ones the division exists for: a unit that can still act
is waited on, and a Great General or Admiral is the human's even though it has no combat strength.
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


# --- the regression: a unit that already has its order is not the human's to finish -------------


@pytest.mark.parametrize(
    "activity",
    ["ACTIVITY_HOLD", "ACTIVITY_SENTRY", "ACTIVITY_OPERATION", "ACTIVITY_SLEEP"],
)
def test_a_unit_that_already_has_its_order_is_not_waited_on(activity: str) -> None:
    """The deadlock: movement is kept, but the engine says the unit cannot act.

    Each of these was present in the live reading that exposed the bug, all three with movement in
    hand. Before the fix this list was non-empty forever, so the wait never returned.
    """
    parked = Unit(
        "UNIT_FIELD_CANNON",
        combat_strength=50,
        moves_remaining=2.0,
        ready_to_move=False,
        activity=activity,
    )
    assert wait_for_human.can_still_act(parked) is False
    assert holding([parked]) == []


def test_the_live_reading_that_exposed_it_now_waits_on_one_unit_not_ten() -> None:
    """The measured case, in full: 10 with movement, 9 unable to act, 1 genuinely free."""
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
    assert waiting[0].moves_remaining == 0.5


@pytest.mark.parametrize(
    "activity", ["ACTIVITY_HOLD", "ACTIVITY_SENTRY", "ACTIVITY_OPERATION", "ACTIVITY_SLEEP"]
)
def test_a_commander_that_already_has_its_order_is_not_waited_on(activity: str) -> None:
    parked = Unit("UNIT_GREAT_GENERAL", moves_remaining=2.0, ready_to_move=False, activity=activity)
    assert holding([parked]) == []


# --- what must keep working ---------------------------------------------------------------------


def test_a_unit_that_can_still_act_is_waited_on() -> None:
    free = Unit("UNIT_TANK", combat_strength=85, moves_remaining=3.0, ready_to_move=True)
    assert holding([free]) == [free]


def test_a_unit_with_no_movement_is_never_waited_on() -> None:
    spent = Unit("UNIT_TANK", combat_strength=85, moves_remaining=0.0, ready_to_move=False)
    assert wait_for_human.can_still_act(spent) is False


def test_a_great_general_is_the_humans_despite_no_combat_strength() -> None:
    general = Unit("UNIT_GREAT_GENERAL", combat_strength=0, moves_remaining=6.0, ready_to_move=True)
    assert wait_for_human.is_the_humans(general) is True
    assert holding([general]) == [general]


def test_a_great_admiral_is_the_humans_despite_no_combat_strength() -> None:
    admiral = Unit("UNIT_GREAT_ADMIRAL", combat_strength=0, moves_remaining=1.0, ready_to_move=True)
    assert wait_for_human.is_the_humans(admiral) is True
    assert holding([admiral]) == [admiral]


@pytest.mark.parametrize(
    "unit_type",
    ["UNIT_BUILDER", "UNIT_SETTLER", "UNIT_TRADER", "UNIT_SCIENTIST", "UNIT_PROPHET"],
)
def test_a_civilian_is_not_the_humans(unit_type: str) -> None:
    """The division gives the session every unit that is not military - including other great people."""
    assert wait_for_human.is_the_humans(Unit(unit_type, combat_strength=0)) is False


def test_a_server_without_the_activity_column_falls_back_to_movement() -> None:
    """An old server reports no activity, so `ready_to_move` is its default and carries nothing.

    The fallback is the pre-existing movement test, which waits rather than advancing - the safe
    direction when the engine cannot be asked.
    """
    old = Unit("UNIT_FIELD_CANNON", combat_strength=50, moves_remaining=2.0, activity="")
    assert wait_for_human.can_still_act(old) is True
    spent = Unit("UNIT_FIELD_CANNON", combat_strength=50, moves_remaining=0.0, activity="")
    assert wait_for_human.can_still_act(spent) is False
