"""Tests for the two siege defects found by analysing the live Russia campaign.

1. ``city_attack`` rejected out-of-range targets with nothing to act on. Four of
   five calls in one game were rejected with "Target is 3 tiles away", each
   costing a full round trip.
2. The combat estimate against a city tile reported "Est damage to defender:
   ~0" whenever the tile's occupant had 0 combat strength (a Great Writer, a
   Missionary). On T167 of that game seven attacks read "~0" while the city
   walls went 13 -> 3, which reads as "this attack does nothing".
"""

from civ_mcp.lua.cities import build_city_attack
from civ_mcp.lua.models import CombatEstimate
from civ_mcp.lua.units import build_combat_estimate_query, parse_combat_estimate
from civ_mcp.narrate import narrate_combat_estimate


class TestCityAttackRangeMessage:
    def test_out_of_range_branch_is_present(self):
        lua = build_city_attack(65536, 49, 36)
        assert "if dist > 2 then" in lua

    def test_out_of_range_lists_in_range_targets(self):
        lua = build_city_attack(65536, 49, 36)
        # The hint must be built and appended to the error, not just the distance.
        assert "In-range hostile units: " in lua
        assert "No hostile unit is within range 2 of " in lua
        assert "local inRange = {}" in lua

    def test_hint_scans_only_tiles_within_range_two(self):
        lua = build_city_attack(65536, 49, 36)
        assert "if Map.GetPlotDistance(cx, cy, px, py) <= 2 then" in lua

    def test_error_still_reports_distance_and_city_position(self):
        lua = build_city_attack(65536, 49, 36)
        assert 'ERR:OUT_OF_RANGE|Target is ' in lua
        assert "city attack range is 2; city at " in lua


class TestEstimateKnowsAboutCities:
    def test_lua_probes_the_target_plot_for_a_city(self):
        lua = build_combat_estimate_query(0, 56, 43)
        assert "Cities.GetCityInPlot(56, 43)" in lua
        # The probe is guarded: a missing API must not break the estimate.
        assert "pcall(function() tCity = Cities.GetCityInPlot(56, 43) end)" in lua

    def test_estimate_line_carries_the_city_name(self):
        lua = build_combat_estimate_query(0, 56, 43)
        assert '.. "|" .. tCityName)' in lua

    def test_city_name_with_a_pipe_cannot_break_the_field_split(self):
        lua = build_combat_estimate_query(0, 56, 43)
        assert 'gsub("|", "/")' in lua


class TestParseCombatEstimateCityField:
    def test_ten_field_line_parses_the_city(self):
        line = "ESTIMATE|UNIT_CROSSBOWMAN|UNIT_GREAT_WRITER|62|0|1|none|100|100|St Petersburg"
        est = parse_combat_estimate([line], att_cs=0, def_cs=0)
        assert est is not None
        assert est.target_city == "St Petersburg"

    def test_nine_field_line_still_parses(self):
        # Backward compatible with lines produced before the city field existed.
        line = "ESTIMATE|UNIT_ARCHER|UNIT_WARRIOR|25|20|1||100|100"
        est = parse_combat_estimate([line], att_cs=25, def_cs=20)
        assert est is not None
        assert est.target_city == ""

    def test_empty_trailing_field_means_no_city(self):
        line = "ESTIMATE|UNIT_ARCHER|UNIT_WARRIOR|25|20|1||100|100|"
        est = parse_combat_estimate([line], att_cs=25, def_cs=20)
        assert est is not None
        assert est.target_city == ""


def _est(**kw):
    base = dict(
        attacker_type="UNIT_CROSSBOWMAN",
        defender_type="UNIT_WARRIOR",
        attacker_cs=25,
        defender_cs=20,
        is_ranged=True,
        modifiers=[],
        est_damage_to_defender=30,
        est_damage_to_attacker=0,
        defender_hp=100,
        attacker_hp=100,
        target_city="",
    )
    base.update(kw)
    return CombatEstimate(**base)


class TestNarrateCombatEstimate:
    def test_field_battle_is_unchanged(self):
        text = narrate_combat_estimate(_est())
        assert "Est damage to defender: ~30" in text
        assert "city" not in text.lower()

    def test_city_tile_with_non_combatant_suppresses_the_zero(self):
        text = narrate_combat_estimate(
            _est(defender_type="UNIT_GREAT_WRITER", defender_cs=0,
                 est_damage_to_defender=0, target_city="St Petersburg")
        )
        assert "Est damage to defender: ~0" not in text, "the misleading zero must go"
        assert "n/a" in text
        assert "St Petersburg" in text
        assert "city hp" in text

    def test_city_tile_with_a_real_garrison_still_warns(self):
        text = narrate_combat_estimate(
            _est(defender_type="UNIT_WARRIOR", defender_cs=20, target_city="St Petersburg")
        )
        # The estimate is kept (a real unit is present) but the city caveat stands.
        assert "Est damage to defender: ~30" in text
        assert "St Petersburg" in text
        assert "what takes damage is the CITY" in text

    def test_no_spurious_win_or_loss_call_on_a_city_target(self):
        text = narrate_combat_estimate(
            _est(
                defender_type="UNIT_GREAT_WRITER",
                defender_cs=0,
                est_damage_to_defender=0,
                defender_hp=0,
                target_city="St Petersburg",
            )
        )
        assert "LIKELY KILL" not in text, "0 vs 0 HP is not a kill"
