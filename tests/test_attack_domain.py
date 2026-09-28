"""Melee attacks on a unit at sea: the refusal, the estimate, and the counter that watches for it.

The failure this pins, measured on this branch T222-T237: a **melee land unit cannot attack a unit at
sea** (`manual:723`, "MELEE UNITS ... They cannot attack enemies at sea"), but the engine accepted the
order, the tool printed `OK:MELEE_ATTACK` with `Est damage to defender: ~151`, and the target's HP never
moved - seven attacks, the Dutch hulls reading 57 and 100 for seventeen turns while the diary recorded
"four Caravels destroyed", and two of our units sunk in the water (Cavalry T226 at (74,27), Field Cannon
T233 at (74,29)) because the attack consumed the move that would have carried them out.

The same anomaly had been written down in three retired task files (018 at T216, 019 and 021 at T225)
and never became a refusal, so these tests hold three layers: the Lua refuses the order, the estimate
says why instead of printing a number, and a counter exists for a rule to watch.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import narrate  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402
from civ_mcp.lua import models as lm  # noqa: E402
from civ_mcp.lua import parse_combat_estimate  # noqa: E402
from civ_mcp.lua import units as lu  # noqa: E402

ATTACK_LUA = lu.build_attack_unit(3, 74, 27)
ESTIMATE_LUA = lu.build_combat_estimate_query(3, 74, 27)


class TestTheLuaRefusesTheOrder:
    def test_a_melee_land_unit_vs_a_unit_at_sea_is_refused_by_name(self):
        assert "ERR:MELEE_CANNOT_ATTACK_AT_SEA" in ATTACK_LUA
        assert "manual:723" in ATTACK_LUA, "the refusal must cite the rule it enforces"
        assert "DOMAIN_SEA" in ATTACK_LUA and "DOMAIN_LAND" in ATTACK_LUA, (
            "the refusal must be driven by the two domains, not by a unit-type list"
        )
        assert "manual:725" in ATTACK_LUA, "the way out (ranged fire) must be in the message"

    def test_the_guard_covers_the_ranged_fell_back_to_melee_path(self):
        """The bug's exact shape: `RANGE_ATTACK` is refused at distance 1, so it fell through to melee.

        The guard therefore has to sit *after* the ranged block's `isRanged = false` fallback, or the
        fall-through would still produce the no-op it was measured producing.
        """
        fallback = ATTACK_LUA.index("fall through to melee attack below")
        guard = ATTACK_LUA.index("ERR:MELEE_CANNOT_ATTACK_AT_SEA")
        assert fallback < guard

    def test_the_refusal_comes_before_the_melee_command_is_issued(self):
        guard = ATTACK_LUA.index("ERR:MELEE_CANNOT_ATTACK_AT_SEA")
        melee_request = ATTACK_LUA.index("UnitOperationTypes.MOVE_TO, params", guard)
        assert guard < melee_request

    def test_a_city_target_is_not_affected(self):
        # The domain is only known for a unit; a city attack has `enemy == nil` and enemyIsSea stays
        # false, so the guard cannot refuse an assault.
        assert "local enemyIsSea = false" in ATTACK_LUA
        assert 'if enemy ~= nil then' in ATTACK_LUA


class TestTheEstimateCarriesTheDefendersDomain:
    def test_the_estimate_line_prints_the_domain(self):
        assert "defDomain" in ESTIMATE_LUA
        assert ".. defDomain" in ESTIMATE_LUA

    def test_the_parser_reads_it(self):
        line = "ESTIMATE|Melee|UNIT_CARAVEL|79|55|0|none|6|57||DOMAIN_SEA"
        est = parse_combat_estimate([line], att_cs=79, def_cs=55)
        assert est is not None and est.defender_domain == "DOMAIN_SEA"

    def test_an_older_line_without_the_field_still_parses(self):
        line = "ESTIMATE|Melee|UNIT_CARAVEL|79|55|0|none|6|57|"
        est = parse_combat_estimate([line], att_cs=79, def_cs=55)
        assert est is not None and est.defender_domain == ""

    def test_a_city_estimate_carries_no_domain(self):
        line = "ESTIMATE|Melee|CITY_CENTER|65|0|0||74|200|乌得勒支|"
        est = parse_combat_estimate([line], att_cs=65, def_cs=0)
        assert est is not None and est.defender_domain == ""


def estimate(*, is_ranged: bool, domain: str) -> lm.CombatEstimate:
    return lm.CombatEstimate(
        attacker_type="UNIT_CAVALRY",
        defender_type="UNIT_CARAVEL",
        attacker_cs=79,
        defender_cs=55,
        is_ranged=is_ranged,
        modifiers=[],
        est_damage_to_defender=151,
        est_damage_to_attacker=0 if is_ranged else 4,
        defender_hp=57,
        attacker_hp=6,
        defender_domain=domain,
    )


class TestTheEstimateRefusesInsteadOfPrintingANumber:
    def test_melee_vs_a_unit_at_sea_prints_the_rule_not_a_damage(self):
        text = narrate.narrate_combat_estimate(estimate(is_ranged=False, domain="DOMAIN_SEA"))
        assert "manual:723" in text
        assert "Est damage to defender" not in text, "no damage number for a blow that cannot land"
        assert "~151" not in text and "~4" not in text
        assert "REFUSED BY THE RULES" in text

    def test_ranged_vs_a_unit_at_sea_still_gets_its_numbers(self):
        text = narrate.narrate_combat_estimate(estimate(is_ranged=True, domain="DOMAIN_SEA"))
        assert "Est damage to defender: ~151" in text
        assert "manual:723" not in text, "a ranged attack on a ship is legal (manual:725)"

    def test_melee_vs_a_land_unit_is_untouched(self):
        text = narrate.narrate_combat_estimate(estimate(is_ranged=False, domain="DOMAIN_LAND"))
        assert "Est damage to defender: ~151" in text
        assert "manual:723" not in text
        assert "-> LIKELY KILL" in text, "the pre-existing verdicts must survive the new branch"

    def test_a_doomed_land_attacker_still_gets_the_old_warning(self):
        doomed = estimate(is_ranged=False, domain="DOMAIN_LAND")
        doomed.defender_hp = 300          # nothing like a kill
        doomed.est_damage_to_attacker = 50  # and 6 HP cannot take it
        text = narrate.narrate_combat_estimate(doomed)
        assert "WARNING: attacker likely dies!" in text


class TestTheCounterAndTheRule:
    def test_a_melee_attack_on_a_sea_target_is_counted_and_warned(self):
        gs = GameState(connection=None)
        warning = gs.note_attack_result(
            "MELEE_ATTACK|target:UNIT_CARAVEL at (75,27)|enemy HP:57 -> 57/100|your HP:6 -> 6",
            estimate(is_ranged=False, domain="DOMAIN_SEA"),
        )
        assert "ATTACK LANDED NOTHING" in warning
        assert "manual:723" in warning
        assert gs._attacks_landed_nothing == 1

    def test_a_ranged_attack_is_not_counted(self):
        gs = GameState(connection=None)
        assert gs.note_attack_result("RANGE_ATTACK|target:UNIT_CARAVEL at (75,27)", estimate(
            is_ranged=True, domain="DOMAIN_SEA"
        )) == ""
        assert gs._attacks_landed_nothing == 0

    def test_a_melee_attack_on_land_is_not_counted(self):
        gs = GameState(connection=None)
        assert gs.note_attack_result("MELEE_ATTACK|target:UNIT_WARRIOR at (75,27)", estimate(
            is_ranged=False, domain="DOMAIN_LAND"
        )) == ""
        assert gs._attacks_landed_nothing == 0

    def test_the_turn_exposes_the_metric_the_rule_names(self):
        end_turn = (ROOT / "src" / "civ_mcp" / "end_turn.py").read_text(encoding="utf-8")
        assert '"attacks_landed_nothing"' in end_turn
        assert "gs._attacks_landed_nothing = 0" in end_turn, "the counter must reset with the turn"

    def test_the_rule_is_staged_until_a_server_computes_the_metric(self):
        from civ_mcp import turn_checks

        staged = (ROOT / "prompts" / "checks" / "pending" / "attacks-that-land-nothing.md").read_text(
            encoding="utf-8-sig"
        )
        assert "attacks-that-land-nothing" in staged
        assert "metric(attacks_landed_nothing) == 0" in staged
        assert "manual:723" in staged
        # It must not be live yet: the metric is new, and a live rule naming an uncomputed metric
        # reports `un-evaluable` every turn (prompts/checks/pending/README.md).
        live_text, _ = turn_checks.load_checks()
        assert "attacks-that-land-nothing" not in live_text
