"""The "every unit is at 0 moves" note in get_units.

A live session spent four minutes and five re-reads on this state on 2026-09-20 (T81): the
turn had advanced, no unit was granted movement points, and every action was refused with
NO_MOVES while the game's notification still claimed units had moves. The note tells the
next reader what it is and what clears it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import narrate  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def unit(unit_id: int, moves: float, max_moves: int = 2) -> m.UnitInfo:
    return m.UnitInfo(
        unit_id=unit_id,
        unit_index=unit_id,
        name=f"Unit{unit_id}",
        unit_type="UNIT_ARCHER",
        x=10,
        y=10,
        moves_remaining=moves,
        max_moves=max_moves,
        health=100,
        max_health=100,
    )


def test_every_unit_at_zero_moves_is_explained():
    text = narrate.narrate_units([unit(1, 0), unit(2, 0.0, max_moves=3)])
    assert "every unit is at 0 moves" in text
    assert "end the turn" in text
    assert "Do not restart the game" in text


def test_one_unit_with_moves_means_no_note():
    text = narrate.narrate_units([unit(1, 0), unit(2, 2)])
    assert "every unit is at 0 moves" not in text


def test_the_note_names_how_many_units_are_stuck():
    text = narrate.narrate_units([unit(i, 0) for i in range(1, 8)])
    assert "(7 units;" in text


def test_no_units_is_not_a_stuck_army():
    assert narrate.narrate_units([]) == "No units."
