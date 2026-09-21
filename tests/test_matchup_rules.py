"""Counting units is not matching them: the melee matchup, and the upgrade window.

Two rules with the same origin - a campaign where what we had was measured but not compared:

1. **`match-their-melee`.** T116-T119 (hand-played): an enemy Man-at-Arms (CS 45) took 11-20
   damage from each of our Archers, dealt 79 to a Spearman and 82 to an Archer in single blows,
   and was removed only by attrition. T101-T116 lost a Battering Ram and a Warrior to one
   Battlecry Swordsman. `melee-screen` counted our Warriors as a front line the whole time, and
   `enemies_melee_within_2` filed the enemy as "melee in contact" without ever saying the match
   was lost before the first blow.
2. **`upgrade-the-siege`.** T105-T121: Catapults fired from T106, Trebuchets only from T120 -
   eleven turns of 45 city damage where 55 was available, in a war that spent 64 attacks on
   three cities. `UnitInfo` already carries `can_upgrade`/`upgrade_target`/`upgrade_cost`; no
   rule looked.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402

MELEE = "PROMOTION_CLASS_MELEE"
ANTI_CAV = "PROMOTION_CLASS_ANTI_CAVALRY"
NAVAL_MELEE = "PROMOTION_CLASS_NAVAL_MELEE"
RANGED = "PROMOTION_CLASS_RANGED"


def unit(
    unit_id: int,
    unit_type: str,
    cs: int = 20,
    can_upgrade: bool = False,
    target: str = "",
    cost: int = 0,
) -> m.UnitInfo:
    return m.UnitInfo(
        unit_id=unit_id,
        unit_index=unit_id,
        name=unit_type,
        unit_type=unit_type,
        x=0,
        y=0,
        moves_remaining=2.0,
        max_moves=2.0,
        health=100,
        max_health=100,
        combat_strength=cs,
        can_upgrade=can_upgrade,
        upgrade_target=target,
        upgrade_cost=cost,
    )


def threat(
    unit_type: str, cs: int, klass: str, unit_distance: int = 1, hp: int = 100
) -> m.ThreatInfo:
    return m.ThreatInfo(
        unit_type=unit_type,
        x=1,
        y=1,
        hp=hp,
        max_hp=100,
        combat_strength=cs,
        ranged_strength=0,
        distance=unit_distance,
        unit_distance=unit_distance,
        promotion_class=klass,
    )


class TestTheMatchupMetric:
    def test_the_strongest_enemy_melee_in_reach_is_reported(self):
        threats = [
            threat("UNIT_MAN_AT_ARMS", 45, MELEE),
            threat("UNIT_SWORDSMAN", 35, MELEE, unit_distance=2),
            threat("UNIT_ARCHER", 25, RANGED),
        ]
        units = {1: unit(1, "UNIT_WARRIOR", 20)}
        metrics = et._matchup_metrics(threats, units)
        assert metrics["strongest_enemy_melee_cs"] == 45
        assert metrics["our_best_melee_cs"] == 20

    def test_anti_cavalry_is_front_line_too(self):
        metrics = et._matchup_metrics([threat("UNIT_SPEARMAN", 25, ANTI_CAV)], {})
        assert metrics["strongest_enemy_melee_cs"] == 25

    def test_a_naval_melee_unit_is_not_the_matchup(self):
        assert et._matchup_metrics([threat("UNIT_GALLEY", 30, NAVAL_MELEE)], {})[
            "strongest_enemy_melee_cs"
        ] == 0

    def test_a_melee_unit_far_from_the_army_is_not_the_matchup(self):
        assert et._matchup_metrics([threat("UNIT_MUSKETMAN", 55, MELEE, unit_distance=9)], {})[
            "strongest_enemy_melee_cs"
        ] == 0

    def test_our_best_melee_and_the_cheapest_upgrade(self):
        units = {
            1: unit(1, "UNIT_WARRIOR", 20, can_upgrade=True, target="UNIT_SWORDSMAN", cost=160),
            2: unit(2, "UNIT_SPEARMAN", 25, can_upgrade=True, target="UNIT_PIKEMAN", cost=250),
            3: unit(3, "UNIT_ARCHER", 15),
        }
        metrics = et._matchup_metrics([], units)
        assert metrics["our_best_melee_cs"] == 25
        assert metrics["melee_upgrades_available"] == 2
        assert metrics["min_melee_upgrade_cost"] == 160

    def test_nothing_in_sight_is_neutral(self):
        assert et._matchup_metrics([], None) == {
            "strongest_enemy_melee_cs": 0,
            "our_best_melee_cs": 0,
            "melee_upgrades_available": 0,
            "min_melee_upgrade_cost": 0,
        }


class TestTheSiegeUpgradeMetric:
    def test_a_catapult_that_can_become_a_trebuchet(self):
        units = {
            1: unit(1, "UNIT_CATAPULT", 25, can_upgrade=True, target="UNIT_TREBUCHET", cost=250),
            2: unit(2, "UNIT_TREBUCHET", 35),
        }
        metrics = et._siege_upgrade_metrics(units)
        assert metrics["siege_upgrades_available"] == 1
        assert metrics["min_siege_upgrade_cost"] == 250

    def test_an_archer_is_not_a_siege_upgrade(self):
        units = {1: unit(1, "UNIT_ARCHER", 15, can_upgrade=True, target="UNIT_CROSSBOWMAN", cost=250)}
        assert et._siege_upgrade_metrics(units)["siege_upgrades_available"] == 0


class TestTheUpgradeEvent:
    def test_it_names_the_unit_and_the_price(self):
        units = {
            1703949: unit(
                1703949, "UNIT_CATAPULT", 25, can_upgrade=True, target="UNIT_TREBUCHET", cost=250
            )
        }
        text = et._upgrade_event(units, 480.0, 121) or ""
        assert "UPGRADE AVAILABLE" in text
        assert "UNIT_CATAPULT 1703949 -> TREBUCHET (cost 250g)" in text

    def test_an_unaffordable_upgrade_is_left_out(self):
        units = {
            1: unit(1, "UNIT_CATAPULT", 25, can_upgrade=True, target="UNIT_TREBUCHET", cost=250)
        }
        assert et._upgrade_event(units, 40.0, 121) is None

    def test_unknown_gold_shows_everything_rather_than_nothing(self):
        units = {
            1: unit(1, "UNIT_CATAPULT", 25, can_upgrade=True, target="UNIT_TREBUCHET", cost=250)
        }
        assert et._upgrade_event(units, 0.0, 121) is not None

    def test_nothing_to_upgrade_says_nothing(self):
        assert et._upgrade_event({1: unit(1, "UNIT_WARRIOR", 20)}, 480.0, 121) is None


class TestTheAssessment:
    def _metrics(self, **over):
        base = {
            "damaged_this_turn": 1,
            "at_war": 1,
            "enemies_within_3": 1,
            "local_superiority": 2,
            "enemies_melee_within_2": 1,
            "enemies_cavalry_within_2": 0,
            "strongest_enemy_melee_cs": 45,
            "our_best_melee_cs": 20,
            "min_melee_upgrade_cost": 160,
        }
        base.update(over)
        return base

    def test_a_lost_matchup_is_stated_with_the_fix(self):
        text = et._battle_assessment(self._metrics(), [threat("UNIT_MAN_AT_ARMS", 45, MELEE)], 118) or ""
        assert "MATCHUP" in text
        assert "UNIT_MAN_AT_ARMS" in text
        assert "CS 45" in text and "CS 20" in text
        assert "160g" in text

    def test_an_even_matchup_says_nothing_extra(self):
        text = (
            et._battle_assessment(
                self._metrics(strongest_enemy_melee_cs=25),
                [threat("UNIT_SPEARMAN", 25, MELEE)],
                118,
            )
            or ""
        )
        assert "MATCHUP" not in text

    def test_the_battlecry_note_is_spelled_right(self):
        text = et._battle_assessment(self._metrics(), [threat("UNIT_MAN_AT_ARMS", 45, MELEE)], 118) or ""
        assert "Battlcry" not in text


class TestTheRules:
    FILE = pathlib.Path("prompts/checks/turn-checks.md")

    def context(self, **metrics):
        base = {
            "wonders": 1, "districts": 30, "pop": 30, "improvements": 90, "cities": 5,
            "gold_per_turn": 30, "attacks_this_turn": 0, "unused_attacks": 0,
            "capture_ready": 0, "downed_enemy_cities": 0, "enemy_city_hp_min": 999,
            "strongest_enemy_melee_cs": 0, "our_best_melee_cs": 0,
            "melee_upgrades_available": 0, "min_melee_upgrade_cost": 0,
            "siege_upgrades_available": 0, "min_siege_upgrade_cost": 0,
            "gold": 0, "at_war": 0,
        }
        base.update(metrics)
        return turn_checks.CheckContext(turn=118, units=metrics.pop("_units", {}),
                                        metrics=base, researched=frozenset())

    def failing(self, **metrics) -> set[str]:
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), self.context(**metrics))
        return run.failing_ids

    def test_their_upgraded_melee_against_our_warriors_fails(self):
        ids = self.failing(
            strongest_enemy_melee_cs=45,
            _units={1: unit(1, "UNIT_WARRIOR", 20), 2: unit(2, "UNIT_SPEARMAN", 25)},
        )
        assert "match-their-melee" in ids

    def test_one_of_our_own_upgraded_melee_clears_it(self):
        ids = self.failing(
            strongest_enemy_melee_cs=45, _units={1: unit(1, "UNIT_SWORDSMAN", 35)}
        )
        assert "match-their-melee" not in ids

    def test_engaging_it_this_turn_clears_it(self):
        ids = self.failing(
            strongest_enemy_melee_cs=45, attacks_this_turn=2,
            _units={1: unit(1, "UNIT_WARRIOR", 20)},
        )
        assert "match-their-melee" not in ids

    def test_no_upgraded_melee_in_sight_is_not_this_rules_business(self):
        ids = self.failing(strongest_enemy_melee_cs=25, _units={1: unit(1, "UNIT_WARRIOR", 20)})
        assert "match-their-melee" not in ids

    def test_an_affordable_siege_upgrade_during_a_war_fails(self):
        ids = self.failing(
            at_war=1, siege_upgrades_available=1, min_siege_upgrade_cost=250, gold=480
        )
        assert "upgrade-the-siege" in ids

    def test_no_upgrade_waiting_clears_it(self):
        ids = self.failing(
            at_war=1, siege_upgrades_available=0, min_siege_upgrade_cost=0, gold=480
        )
        assert "upgrade-the-siege" not in ids

    def test_at_peace_the_siege_rule_is_silent(self):
        ids = self.failing(
            at_war=0, siege_upgrades_available=1, min_siege_upgrade_cost=250, gold=480
        )
        assert "upgrade-the-siege" not in ids

    def test_an_unaffordable_upgrade_is_not_demanded(self):
        ids = self.failing(
            at_war=1, siege_upgrades_available=1, min_siege_upgrade_cost=250, gold=40
        )
        assert "upgrade-the-siege" not in ids

    def test_a_historical_row_reads_as_zero(self):
        row = {
            "turn": 118, "is_agent": True, "unit_composition": {"WARRIOR": 2},
            "pop": 30, "districts": 30, "wonders": 1, "cities": 5, "improvements": 90,
            "gold_per_turn": 30, "gold": 400,
        }
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), et._context_from_row(row))
        assert "match-their-melee" not in run.failing_ids
        assert "upgrade-the-siege" not in run.failing_ids
        assert not [c for c, reason in run.failures if "un-evaluable" in reason]
