"""A siege unit cannot attack a unit — the refusal that replaced a wasted turn.

`UNIT_CATAPULT` is CS 25 / RS 0 / **Bombard 35** / Range 2. `build_attack_unit` classifies the attack
from `RangedCombat` and only reads a Bombard as ranged when the target is a **city**
(`isRanged = (attRS > 0 or (attBombard > 0 and targetIsCity)) and dist <= attRange`). Order a Catapult
to attack a *unit* and that test is false, so the order fell through to the melee branch: the unit was
sent `MOVE_TO` + attack, walked toward the target and reported `STOPPED_SHORT` when its movement ran
out. Measured live T140 (game 13's T107 is the same trap): one whole turn lost, and the reply reads
like a movement problem rather than a wrong order.

The guard is placed **before** the attack-type classification and only fires when the resolved target
is a unit (`enemy ~= nil`), so a city tile is untouched - which is what a Catapult is for.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import lua as lq  # noqa: E402


def lua() -> str:
    return lq.build_attack_unit(2359300, 57, 39)


class TestTheRefusalExists:
    def test_it_names_the_refusal_and_the_right_unit(self):
        text = lua()
        assert "ERR:SIEGE_CANNOT_ATTACK_UNITS" in text
        assert "Crossbowman" in text

    def test_it_is_about_bombard_without_ranged_combat(self):
        text = lua()
        assert "attBombard > 0 and attRS == 0" in text

    def test_it_fires_before_the_attack_type_is_classified(self):
        text = lua()
        assert text.index("SIEGE_CANNOT_ATTACK_UNITS") < text.index("local isRanged")

    def test_it_only_fires_when_the_target_is_a_unit(self):
        # `enemy ~= nil` means a city tile (where enemy is cleared) still takes the normal path.
        text = lua()
        guard = text.split("SIEGE_CANNOT_ATTACK_UNITS", 1)[0]
        assert guard.rstrip().endswith("if enemy ~= nil and attBombard > 0 and attRS == 0 then") or (
            "if enemy ~= nil and attBombard > 0 and attRS == 0 then" in guard
        )


class TestNothingElseMoved:
    def test_the_city_branch_is_still_there(self):
        text = lua()
        assert "targetIsCity" in text
        assert "RANGE_ATTACK" in text
        assert "MELEE_ATTACK" in text

    def test_the_unit_info_is_read_once(self):
        # The guard needs the Bombard figures, so they moved up; a second declaration below would
        # shadow them and silently reintroduce the old behaviour in the classification.
        text = lua()
        assert text.count("local attBombard =") == 1
        assert text.count("local attRS =") == 1
