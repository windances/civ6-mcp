"""`choose_pantheon` must not buy a pantheon the empire cannot pay for.

Measured 2026-09-29 on the fresh match, at turn 1 with a capital just founded and `faith_balance 0`:
a blind caller (the development runner, which asks for a pantheon every turn) founded 节庆女神, the
empire was left at **-16 faith**, and the attempt's position carried a free belief that every later
attempt loading the same save would not have - so the reload had to be thrown away and the position
restored from the save taken before it.

The guard reads the game's own threshold rather than a number written into the query:
`RELIGION_PANTHEON_MIN_FAITH` (`Base/Assets/Gameplay/Data/GlobalParameters.xml:475`, value 25).
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp.lua import religion  # noqa: E402


def test_the_query_refuses_below_the_games_own_threshold():
    lua = religion.build_choose_pantheon("BELIEF_GODDESS_OF_FESTIVALS")
    assert 'GameInfo.GlobalParameters["RELIGION_PANTHEON_MIN_FAITH"]' in lua, (
        "the threshold has to come from the game's parameters, not from a literal here"
    )
    assert "ERR:NOT_ENOUGH_FAITH" in lua
    assert lua.index("ERR:NOT_ENOUGH_FAITH") < lua.index("FOUND_PANTHEON"), (
        "the faith check must run before the operation is requested, or it guards nothing"
    )


def test_the_query_still_refuses_a_second_pantheon():
    lua = religion.build_choose_pantheon("BELIEF_GODDESS_OF_FESTIVALS")
    assert "ERR:ALREADY_HAS_PANTHEON" in lua
