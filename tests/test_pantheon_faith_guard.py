"""`choose_pantheon` must not buy a pantheon the empire cannot pay for - and must not refuse one
the game is already offering.

Measured 2026-09-29 on the fresh match, at turn 1 with a capital just founded and `faith_balance 0`:
a blind caller (the development runner, which asks for a pantheon every turn) founded 节庆女神, the
empire was left at **-16 faith**, and the attempt's position carried a free belief that every later
attempt loading the same save would not have - so the reload had to be thrown away and the position
restored from the save taken before it.

**The gate is the game's own availability test**, `PlayerReligion:CanCreatePantheon()`, which is what
the install's own interface uses (`Base/Assets/UI/LaunchBar.lua:138` shows the pantheon button on
`pReligion:GetPantheon() < 0 and pReligion:CanCreatePantheon()`). The flat
`RELIGION_PANTHEON_MIN_FAITH` (`Base/Assets/Gameplay/Data/GlobalParameters.xml:475`, value 25) is the
**standard-speed** cost, and using it as the gate refused pantheons the game had already offered -
measured twice: A4 was offered the game's `ENDTURN_BLOCKING_PANTHEON` at T19 and refused at T20 with
`faith 23 < 25`, and A3 was offered at T22 and refused at T23 with `faith 17`. The parameter survives
only as the fallback for a build where the accessor is missing.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp.lua import religion  # noqa: E402


def test_the_gate_is_the_games_own_availability_test():
    """The game answers "can this empire found a pantheon"; a second constant must not overrule it."""
    lua = religion.build_choose_pantheon("BELIEF_GODDESS_OF_FESTIVALS")
    assert "CanCreatePantheon" in lua, (
        "the gate has to be the game's own availability test - that is the measurement A3 and A4 "
        "produced, and it is what the install's own LaunchBar.lua uses"
    )
    assert "ERR:NOT_ENOUGH_FAITH" in lua
    assert lua.index("ERR:NOT_ENOUGH_FAITH") < lua.index("FOUND_PANTHEON"), (
        "the faith check must run before the operation is requested, or it guards nothing"
    )


def test_the_flat_threshold_survives_only_as_a_fallback():
    """A build without the accessor still needs a guard - so the comparison stays, gated on `nil`."""
    lua = religion.build_choose_pantheon("BELIEF_GODDESS_OF_FESTIVALS")
    assert 'GameInfo.GlobalParameters["RELIGION_PANTHEON_MIN_FAITH"]' in lua, (
        "the fallback threshold has to come from the game's parameters, not from a literal here"
    )
    assert "canCreate == nil and faith < minFaith" in lua, (
        "the flat threshold must only fire when the game's own test was unavailable - otherwise it "
        "is the gate again, and it refuses pantheons the game is offering"
    )
    # The probe must be guarded: an accessor missing from this build is not an exception.
    assert "pcall(function() canCreate = pReligion:CanCreatePantheon() end)" in lua


def test_the_query_still_refuses_a_second_pantheon():
    lua = religion.build_choose_pantheon("BELIEF_GODDESS_OF_FESTIVALS")
    assert "ERR:ALREADY_HAS_PANTHEON" in lua
