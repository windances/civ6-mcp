"""Contact on the march: the rule "engage what is in the way, prefer the counter unit".

The human's instruction was behavioural, and the check engine can only enforce behaviour it
can measure. Two facts were missing from the check context and are added here:

* how close the nearest visible enemy is to **our units** (the threat scan already computed a
  distance, but against our units *and cities*, which answers a different question), and
* how many attacks were actually executed this turn.

`attacks_this_turn` is counted where the attack happens (`GameState.attack_unit`) and reset
after the checks have read it, so a blocker turn earlier in the same turn still sees the
attacks that were already made.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def threat(
    unit_type: str,
    x: int,
    y: int,
    *,
    promotion_class: str = "",
    unit_distance: int = 999,
    distance: int = 999,
    hp: int = 100,
) -> m.ThreatInfo:
    return m.ThreatInfo(
        unit_type=unit_type,
        x=x,
        y=y,
        hp=hp,
        max_hp=100,
        combat_strength=20,
        ranged_strength=0,
        distance=distance,
        promotion_class=promotion_class,
        unit_distance=unit_distance,
    )


class GS:
    """Only what the contact helpers touch."""

    def __init__(self, threats=(), attacks=0):
        self.threats = list(threats)
        self._attacks_this_turn = attacks
        self.conn = self

    async def execute_write(self, _lua):
        lines = []
        for t in self.threats:
            lines.append(
                f"THREAT|1|Russia|{t.unit_type}|{t.x},{t.y}|{t.hp}/100|CS:{t.combat_strength}"
                f"|RS:{t.ranged_strength}|dist:{t.distance}|cs:0|uid:{t.unit_id}"
                f"|pc:{t.promotion_class}|udist:{t.unit_distance}"
            )
        return lines or ["NO_THREATS"]


class TestContactMetrics:
    def test_an_empty_scan_leaves_the_rules_switched_off(self):
        metrics = asyncio.run(et._contact_metrics(GS(), 100, {}))
        assert metrics["enemies_within_2"] == 0
        assert metrics["attacks_this_turn"] == 0

    def test_distance_is_measured_to_our_units_not_to_our_cities(self):
        # 2 tiles from a city (dist:2) but 6 from the nearest unit: not contact on the march.
        metrics = asyncio.run(
            et._contact_metrics(GS([threat("UNIT_HORSEMAN", 10, 10, unit_distance=6, distance=2)]), 100, {})
        )
        assert metrics["enemies_within_2"] == 0

    def test_an_enemy_next_to_the_army_counts(self):
        metrics = asyncio.run(
            et._contact_metrics(
                GS([threat("UNIT_WARRIOR", 10, 10, promotion_class="PROMOTION_CLASS_MELEE", unit_distance=1)]),
                100,
                {},
            )
        )
        assert metrics["enemies_within_1"] == 1
        assert metrics["enemies_within_2"] == 1
        assert metrics["enemies_melee_within_2"] == 1

    def test_an_unknown_class_is_still_contact(self):
        metrics = asyncio.run(
            et._contact_metrics(GS([threat("UNIT_X", 10, 10, unit_distance=2)]), 100, {})
        )
        assert metrics["enemies_within_2"] == 1

    def test_the_unit_only_distance_falls_back_to_the_scan_distance(self):
        # No units on the map at all is the only case where a city distance is used.
        metrics = asyncio.run(
            et._contact_metrics(GS([threat("UNIT_WARRIOR", 10, 10, unit_distance=999, distance=2)]), 100, {})
        )
        assert metrics["enemies_within_2"] == 1

    @pytest.mark.parametrize(
        "promotion_class, key",
        [
            ("PROMOTION_CLASS_LIGHT_CAVALRY", "enemies_cavalry_within_2"),
            ("PROMOTION_CLASS_HEAVY_CAVALRY", "enemies_cavalry_within_2"),
            ("PROMOTION_CLASS_SIEGE", "enemies_siege_within_2"),
            ("PROMOTION_CLASS_RANGED", "enemies_ranged_within_2"),
            ("PROMOTION_CLASS_MELEE", "enemies_melee_within_2"),
            ("PROMOTION_CLASS_ANTI_CAVALRY", "enemies_anti_cavalry_within_2"),
        ],
    )
    def test_the_class_comes_from_the_game_itself(self, promotion_class, key):
        metrics = asyncio.run(
            et._contact_metrics(
                GS([threat("UNIT_X", 10, 10, promotion_class=promotion_class, unit_distance=2)]), 100, {}
            )
        )
        assert metrics[key] == 1

    def test_the_weakest_enemy_is_reported_so_it_can_be_finished(self):
        metrics = asyncio.run(
            et._contact_metrics(
                GS(
                    [
                        threat("UNIT_WARRIOR", 10, 10, unit_distance=1, hp=90),
                        threat("UNIT_SWORDSMAN", 11, 10, unit_distance=2, hp=26),
                        threat("UNIT_ARCHER", 12, 12, unit_distance=5, hp=10),
                    ]
                ),
                100,
                {},
            )
        )
        assert metrics["weakest_enemy_hp_within_2"] == 26, "the 10 hp archer is 5 tiles away"

    def test_more_than_two_tiles_away_is_tracked_but_not_contact(self):
        metrics = asyncio.run(
            et._contact_metrics(GS([threat("UNIT_WARRIOR", 10, 10, unit_distance=3)]), 100, {})
        )
        assert metrics["enemies_within_3"] == 1
        assert metrics["enemies_within_2"] == 0

    def test_the_scan_is_cached_for_the_turn(self):
        gs = GS([threat("UNIT_WARRIOR", 10, 10, unit_distance=1)])
        calls = 0
        real = gs.execute_write

        async def counted(lua):
            nonlocal calls
            calls += 1
            return await real(lua)

        gs.execute_write = counted
        asyncio.run(et._contact_metrics(gs, 100, {}))
        asyncio.run(et._contact_metrics(gs, 100, {}))
        assert calls == 1, "the check path can run several times a turn"

    def test_a_failed_scan_is_not_an_exception(self):
        class Broken(GS):
            async def execute_write(self, _lua):
                raise RuntimeError("tuner busy")

        metrics = asyncio.run(et._contact_metrics(Broken(), 100, {}))
        assert metrics["enemies_within_2"] == 0


class TestTheThreatLineCarriesTheNewFields:
    def test_round_trip_through_the_parser(self):
        from civ_mcp import lua as lq

        lines = [
            "THREAT|1|Russia|UNIT_HORSEMAN|54,40|62/100|CS:20|RS:0|dist:4|cs:0|uid:7"
            "|pc:PROMOTION_CLASS_LIGHT_CAVALRY|udist:2"
        ]
        parsed = lq.parse_threat_scan_response(lines)
        assert len(parsed) == 1
        t = parsed[0]
        assert t.promotion_class == "PROMOTION_CLASS_LIGHT_CAVALRY"
        assert t.unit_distance == 2
        assert t.distance == 4

    def test_an_old_line_without_the_new_fields_still_parses(self):
        from civ_mcp import lua as lq

        lines = ["THREAT|1|Russia|UNIT_WARRIOR|54,40|62/100|CS:20|RS:0|dist:1|cs:0|uid:7"]
        t = lq.parse_threat_scan_response(lines)[0]
        assert t.unit_distance == 999
        assert t.promotion_class == ""


class TestTheRules:
    FILE = pathlib.Path("prompts/checks/turn-checks.md")

    def context(self, **metrics):
        # Every metric a rule can read must be present: a missing one is reported as
        # un-evaluable, which the test would see as "failing" and mistake for the rule firing.
        base = {"wonders": 1, "districts": 30, "pop": 30, "improvements": 90, "cities": 5,
                "gold_per_turn": 30, "at_war": 1, "local_superiority": 0, "enemies_massed_on": 0,
                "siege_units": 0, "siege_exposed": 0, "damaged_this_turn": 0,
                "unused_attacks": 0, "cities_over_garrison": 0, "cities_guarded": 0,
                "weakest_enemy_hp_within_2": 0, "enemies_within_3": 0}
        base.update(metrics)
        return turn_checks.CheckContext(turn=100, units={}, metrics=base, researched=frozenset())

    def failing(self, **metrics) -> set[str]:
        text = self.FILE.read_text(encoding="utf-8")
        run = turn_checks.run_checks(text, self.context(**metrics))
        return run.failing_ids

    def test_the_contact_rule_that_could_not_see_this_case_is_gone(self):
        # `engage-the-screen` required "at least one attack this turn" and a turn of two
        # Catapults shelling a city satisfied it while a 7 HP enemy stood one tile away. The
        # replay of the T101-T116 siege is why it was retired; `use-your-attacks` asks the
        # question that actually discriminates.
        text = self.FILE.read_text(encoding="utf-8")
        assert "engage-the-screen" not in {c.check_id for c in turn_checks.parse_checks(text)}

    def test_an_enemy_in_the_way_and_no_legal_attack_used_is_quiet_for_the_mass_rule(self):
        # mass-on-contact is about concentration, not about whether we attacked.
        assert "mass-on-contact" not in self.failing(
            enemies_within_2=1, attacks_this_turn=1, local_superiority=2
        )

    def test_attacking_something_this_turn_clears_the_old_contact_case(self):
        ids = self.failing(enemies_within_2=1, attacks_this_turn=2, unused_attacks=0)
        assert "use-your-attacks" not in ids

    def test_cavalry_without_an_anti_cavalry_unit_fails(self):
        ids = self.failing(enemies_cavalry_within_2=1, enemies_within_2=1, attacks_this_turn=0)
        assert "counter-the-cavalry" in ids

    def test_engaging_the_cavalry_this_turn_clears_it(self):
        ids = self.failing(enemies_cavalry_within_2=1, enemies_within_2=1, attacks_this_turn=1)
        assert "counter-the-cavalry" not in ids

    def test_an_anti_cavalry_unit_clears_it(self):
        text = self.FILE.read_text(encoding="utf-8")
        context = self.context(
            enemies_cavalry_within_2=1, enemies_within_2=1, attacks_this_turn=0
        )
        context.units = {
            1: m.UnitInfo(
                unit_id=1, unit_index=1, name="spearman", unit_type="UNIT_SPEARMAN",
                x=0, y=0, moves_remaining=2, max_moves=2, health=100, max_health=100,
            )
        }
        run = turn_checks.run_checks(text, context)
        assert "counter-the-cavalry" not in run.failing_ids

    def test_a_historical_row_cannot_fire_the_contact_rules(self):
        # `_context_from_row` has no enemy positions or attack count; zeros must switch the
        # rules off rather than make the engine report them as un-evaluable.
        row = {
            "turn": 100, "is_agent": True, "unit_composition": {"WARRIOR": 2},
            "pop": 30, "districts": 30, "wonders": 1, "cities": 5, "improvements": 90,
            "gold_per_turn": 30,
        }
        context = et._context_from_row(row)
        assert context.metrics["enemies_within_2"] == 0
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), context)
        assert "engage-the-screen" not in run.failing_ids
        assert "counter-the-cavalry" not in run.failing_ids
        assert not [
            c for c, reason in run.failures if "un-evaluable" in reason
        ], "no rule may report itself un-evaluable on a historical row"


class TestTheAttackCounter:
    def test_an_attack_is_counted_where_it_happens(self):
        from civ_mcp.game_state import GameState

        gs = GameState.__new__(GameState)
        gs._local_player_id = 0
        gs._attacks_this_turn = 0

        class Conn:
            async def execute_write(self, _lua):
                return ["MELEE_ATTACK|target:UNIT_WARRIOR at (1,1)|pre_hp:100/100"]

        gs.conn = Conn()

        async def no_popup():
            return None

        gs.dismiss_popup = no_popup

        async def no_estimate(*_args):
            return None

        from civ_mcp import lua as lq

        original = lq.build_combat_estimate_query
        lq.build_combat_estimate_query = lambda *a: "nop"
        try:
            asyncio.run(gs.attack_unit(1, 1, 1))
        finally:
            lq.build_combat_estimate_query = original
        assert gs._attacks_this_turn == 1
        assert et._contact_metrics is not None
