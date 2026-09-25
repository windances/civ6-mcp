"""Siege units are ranged, and a city tile is attacked as a city.

Both defects were measured live on 2026-09-25, mid-assault, and both cost a whole turn of a war:

* `UNIT_CATAPULT` has `Combat 25, RangedCombat 0, Bombard 35, Range 2`. Anything that tests
  `RangedCombat` alone reads the Catapult as a melee unit: the estimate said "Melee", the attack
  path walked it toward Moscow and answered `STOPPED_SHORT ... Movement exhausted`, and the blow
  that did land was resolved as melee and took retaliation. It was also invisible to the target
  scan, so `get_units` showed it with no targets at all.
* An attack on a city tile resolved against the **garrison unit** standing in it. Two Archers and
  a Catapult fired at Moscow and put 76 points into the garrison Archer and 11 into the 200-point
  pool - while the doctrine says a garrison "takes no damage while the city is attacked and dies
  only with the city", i.e. it is never worth an attack.

These are string checks on the generated Lua: the queries are Lua fragments run in the game, so the
only thing a test can pin without a live game is that the fragment asks the right question.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import lua as lq  # noqa: E402


class TestTheUnitScan:
    def test_a_siege_units_bombard_puts_it_in_the_target_scan(self):
        lua = lq.build_units_query()
        assert "entry.Bombard" in lua
        assert "cs > 0 or rs > 0 or bomb > 0" in lua

    def test_its_range_comes_from_the_unit_definition(self):
        lua = lq.build_units_query()
        assert "(rs > 0 or bomb > 0) and (entry and entry.Range or 1)" in lua


class TestTheAttackPath:
    lua = lq.build_attack_unit(0, 54, 40)

    def test_a_siege_unit_with_a_bombard_strength_is_ranged(self):
        assert "unitInfo.Bombard" in self.lua
        assert "attBombard > 0 and targetIsCity" in self.lua

    def test_it_asks_the_engine_too(self):
        # The definition is the fast path; CanStartOperation stays the authority for everything
        # the table cannot express (promotions, embarked units, one-attack-per-turn).
        assert "CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK, nil, params)" in self.lua

    def test_the_city_is_resolved_before_the_unit(self):
        # Order matters: the city resolution must not be inside `if enemy == nil`.
        city_at = self.lua.index("Cities.GetCityInPlot(54, 40)")
        nullify_at = self.lua.index("if targetCity ~= nil then enemy = nil end")
        assert city_at < nullify_at

    def test_the_city_wins_only_on_its_own_tile(self):
        # A unit standing on a farm inside a city's territory must still be attackable as a unit.
        assert "c:GetX() == 54 and c:GetY() == 40" in self.lua


class TestTheEstimate:
    lua = lq.build_combat_estimate_query(0, 54, 40)

    def test_the_bombard_strength_is_what_a_siege_unit_attacks_a_city_with(self):
        assert "attBombard" in self.lua
        assert "isRanged and (attRS > 0 and attRS or attBombard) or attCS" in self.lua

    def test_a_garrisoned_city_is_estimated_as_a_city(self):
        assert "tCityOnTile" in self.lua
        assert "if tCityOnTile == nil then" in self.lua
