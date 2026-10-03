"""The unit row's activity columns: read them, and do not invent one when they are absent.

`UnitInfo` had no way to say what a unit was *doing*. A unit in `ACTIVITY_SLEEP` and a unit nobody
had ordered yet were the same record - full movement, no order, named by nothing - so the only way to
find a dormant unit was to notice across turns that it never moved.

The accessor and the vocabulary come from the game's own unit panel
(`Base/Assets/UI/Panels/UnitPanel.lua:4054-4062`), not from a guess:

    local activityType = UnitManager.GetActivityType(pUnit);
    if activityType == ActivityTypes.ACTIVITY_SLEEP then   -- sleeping
    elseif activityType == ActivityTypes.ACTIVITY_HOLD then -- holding
    elseif activityType ~= ActivityTypes.ACTIVITY_AWAKE and pUnit:GetFortifyTurns() > 0 then -- fortified

Two consequences are pinned here. **Fortified is not an activity** - it is `GetFortifyTurns() > 0`
with the activity not AWAKE - so one field could not have expressed it. And **an absent column must
read as unknown, never as awake**, because the whole point is to find units that are asleep and a
default of "awake" would hide exactly those.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp.lua.units import parse_units_response  # noqa: E402

# `unit_id|index|name|type|x,y|moves/max|hp/max|cs|rs|charges|targets|promo|canUp|upName|upCost|imps|religion|activity|fortify|ready`
BASE = "65536|0|Spearman|UNIT_SPEARMAN|10,20|2.0/2|100/100|25|0|0||0|0||0|||"


def test_a_sleeping_unit_is_named():
    unit = parse_units_response([BASE + "ACTIVITY_SLEEP|0|1"])[0]
    assert unit.activity == "ACTIVITY_SLEEP"
    assert unit.fortify_turns == 0
    assert unit.ready_to_move is True


def test_fortified_is_a_turn_count_and_not_an_activity():
    """The panel's own third branch: activity is not AWAKE *and* the fortify count is positive."""
    unit = parse_units_response([BASE + "ACTIVITY_FORTIFY|3|0"])[0]
    assert unit.fortify_turns == 3
    assert unit.ready_to_move is False
    assert unit.activity != "ACTIVITY_AWAKE"


def test_an_absent_column_reads_as_unknown_not_as_awake():
    """A log written before these columns must not make every unit look awake: unknown is the safe
    direction, because the units this exists to find are the ones that are not."""
    unit = parse_units_response([BASE.rstrip("|")])[0]
    assert unit.activity == ""
    assert unit.fortify_turns == 0
    # With no column there is nothing to report, so the permissive default applies to `ready`.
    assert unit.ready_to_move is True


def test_a_partial_column_does_not_raise():
    unit = parse_units_response([BASE + "ACTIVITY_HOLD"])[0]
    assert unit.activity == "ACTIVITY_HOLD"
    assert unit.fortify_turns == 0


def test_the_row_is_appended_after_religion_so_older_logs_still_parse():
    """Religion keeps its index: the three new columns go after it, not in front of it."""
    parts = BASE.split("|")
    parts[16] = "BUDDHISM"
    unit = parse_units_response(["|".join(parts[:17]) + "|ACTIVITY_SLEEP|0|1"])[0]
    assert unit.religion == "BUDDHISM"
    assert unit.activity == "ACTIVITY_SLEEP"
    assert unit.fortify_turns == 0
