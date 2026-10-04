"""The unit roster must say what a unit is doing when that is not "waiting for an order".

`activity`, `fortify_turns` and `ready_to_move` were added to `UnitInfo` - and to the Lua roster row
(`lua/units.py:238`) - for one reason, in the code's own words: without them "a sleeping unit is
indistinguishable from a unit nobody has ordered yet: both report full movement and neither is named
by any report".

They were parsed and then read by nothing in `src/`: `narrate.py` mentioned `activity`,
`fortify_turns` and `ready_to_move` zero times, and no other non-Lua module mentioned "activit" at
all. So the roster a session actually reads could not answer the question the fields exist for -
"why is this unit not moving?" - and the only reader was the standalone `.tools/sleeping-units.py`.

Two live measurements sit behind this. Measured on the live match: of 10 military units holding
movement, 9 reported `ready_to_move = False` because they were in `ACTIVITY_HOLD`, `ACTIVITY_SENTRY`
or `ACTIVITY_OPERATION` - so a movement count treats a parked unit as a pending one. And at T341 a
Great Admiral read `moves 0/5 (no moves)` with no way to tell a parked commander from one that had
not been looked at.

The flags print only when they differ from the default, the way `charges` and the HP flag already do.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import narrate  # noqa: E402
from civ_mcp.lua.models import UnitInfo  # noqa: E402


def unit(name: str = "Gun", *, activity: str = "ACTIVITY_AWAKE", fortify_turns: int = 0,
         ready_to_move: bool = True, moves_remaining: float = 2.0) -> UnitInfo:
    return UnitInfo(
        unit_id=1, unit_index=1, name=name, unit_type="UNIT_FIELD_CANNON", x=5, y=5,
        moves_remaining=moves_remaining, max_moves=2.0, health=100, max_health=100,
        combat_strength=50, targets=[], valid_improvements=[],
        activity=activity, fortify_turns=fortify_turns, ready_to_move=ready_to_move,
    )


def line(u: UnitInfo) -> str:
    return next(l for l in narrate.narrate_units([u]).splitlines() if u.name in l)


def test_an_awake_unit_with_moves_gets_no_flag() -> None:
    """The quiet case: a healthy roster must not grow a flag on every row."""
    text = line(unit())
    for token in ("[AWAKE]", "[HOLD]", "[SENTRY]", "[cannot act]", "[fortified"):
        assert token not in text


def test_a_parked_unit_names_the_activity_that_parks_it() -> None:
    """The 9-of-10 case: movement in hand, and the engine says it cannot act."""
    text = line(unit("Held", activity="ACTIVITY_HOLD", ready_to_move=False))
    assert "[HOLD]" in text
    assert "[cannot act]" in text
    assert "moves 2/2" in text, "the movement is still reported - that is the trap"


def test_a_sentried_unit_shows_its_fortify_count_too() -> None:
    text = line(unit("Sentried", activity="ACTIVITY_SENTRY", fortify_turns=2, ready_to_move=False))
    assert "[SENTRY]" in text
    assert "[fortified 2]" in text


def test_an_operating_unit_is_named() -> None:
    text = line(unit("Operating", activity="ACTIVITY_OPERATION", ready_to_move=False))
    assert "[OPERATION]" in text


def test_a_unit_with_no_moves_is_not_flagged_as_cannot_act() -> None:
    """`(no moves)` already says it; a second flag for the same fact is noise."""
    text = line(unit("Spent", ready_to_move=False, moves_remaining=0.0))
    assert "(no moves)" in text
    assert "[cannot act]" not in text


def test_a_server_that_did_not_report_activity_gets_no_flag() -> None:
    """An empty activity means "unknown" - it must not be read as dormant."""
    text = line(unit("Unknown", activity=""))
    assert "[" not in text.split("at (5,5)")[1].split("[id:")[0]
