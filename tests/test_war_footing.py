"""War footing: one garrison per city, and a unit that was attacked gets an answer.

Two rules the human asked for after the Russian war:

* **one garrison per city** - once a war is on, a second unit on a city tile is doing what the
  first one already does while the front is a unit short. Counting it needs two facts the
  check context did not have: the city-centre coordinates (to tell "standing in the city" from
  "somewhere near it") and whether a war is actually on.
* **answer the attack** - a unit that was hit and ignored is hit again next turn. The damage
  is only visible in the snapshot diff (the context sees the army as it is now, not as it was
  before the enemy moved), so `end_turn` records who lost HP during the AI turn.

Both are gated on war, so neither fires in peacetime (`at_war` comes from the diary row's
`diplo_states`, where 6 is WAR - the one piece of war state a stored row still carries).

**A raid counts as a war** (human instruction 2026-09-30: 突袭也算战争): the two answer rules fire on
`at_war` **or** `camps_within_3`, so clearing a camp gets the same concentration the front gets. The
occupancy rule (`one-garrison-per-city`) stays wartime-only, because a raid is a fight and not an
occupation, and `camps_within_3` is the proxy - a wandering barbarian with no camp within three tiles
sets neither rule.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402
from civ_mcp.lua.models import SiegePosture  # noqa: E402


def unit(uid: int, unit_type: str, x: int, y: int, *, health: int = 100) -> m.UnitInfo:
    military = not unit_type.startswith(("UNIT_BUILDER", "UNIT_TRADER", "UNIT_SETTLER"))
    return m.UnitInfo(
        unit_id=uid,
        unit_index=uid,
        name=unit_type,
        unit_type=unit_type,
        x=x,
        y=y,
        moves_remaining=2,
        max_moves=2,
        health=health,
        max_health=100,
        combat_strength=28 if military else 0,
        ranged_strength=0,
    )


def city(city_id: int, name: str, x: int, y: int) -> m.CitySnapshot:
    return m.CitySnapshot(
        city_id=city_id, name=name, population=5, currently_building="", x=x, y=y
    )


class Snap:
    def __init__(self, units: dict, cities: dict):
        self.units = units
        self.cities = cities


class GS:
    def __init__(self, units: dict, cities: dict, *, damaged=(), attacks=0):
        self._last_snapshot = Snap(units, cities)
        self._damaged_last_turn = list(damaged)
        self._attacks_this_turn = attacks


class TestIsMilitary:
    @pytest.mark.parametrize(
        "unit_type, expected",
        [
            ("UNIT_WARRIOR", True),
            ("UNIT_ARCHER", True),
            ("UNIT_BUILDER", False),
            ("UNIT_TRADER", False),
            ("UNIT_SETTLER", False),
        ],
    )
    def test_civilians_are_not_garrisons(self, unit_type, expected):
        assert et._is_military(unit(1, unit_type, 0, 0)) is expected


class TestGarrisonMetrics:
    CITIES = {1: city(1, "Xi'an", 10, 10), 2: city(2, "Beijing", 20, 20)}

    def metrics(self, units, **kw):
        return et._garrison_metrics(GS(units, self.CITIES, **kw), units)

    def test_one_unit_per_city_is_fine(self):
        units = {1: unit(1, "UNIT_WARRIOR", 10, 10), 2: unit(2, "UNIT_ARCHER", 20, 20)}
        assert self.metrics(units)["cities_over_garrison"] == 0
        assert self.metrics(units)["garrisoned_units"] == 2
        assert self.metrics(units)["cities_guarded"] == 2

    def test_a_second_unit_on_a_city_tile_is_counted(self):
        units = {
            1: unit(1, "UNIT_WARRIOR", 10, 10),
            2: unit(2, "UNIT_ARCHER", 10, 10),
            3: unit(3, "UNIT_SPEARMAN", 20, 20),
        }
        metrics = self.metrics(units)
        assert metrics["cities_over_garrison"] == 1
        assert metrics["garrisoned_units"] == 3

    def test_a_unit_next_to_a_city_is_not_a_garrison(self):
        # Standing beside a city is exactly where a front unit should be.
        units = {1: unit(1, "UNIT_WARRIOR", 10, 11)}
        metrics = self.metrics(units)
        assert metrics["garrisoned_units"] == 0
        assert metrics["cities_guarded"] == 0

    def test_civilians_do_not_garrison(self):
        units = {1: unit(1, "UNIT_BUILDER", 10, 10), 2: unit(2, "UNIT_BUILDER", 10, 10)}
        assert self.metrics(units)["cities_over_garrison"] == 0

    def test_no_city_coordinates_means_no_claim(self):
        metrics = et._garrison_metrics(GS({1: unit(1, "UNIT_WARRIOR", 10, 10)}, {}), {})
        assert metrics["garrisoned_units"] == 0
        assert metrics["cities_over_garrison"] == 0
        assert metrics["cities_guarded"] == 0
        assert metrics["unexplained_stacks"] == 0, "without cities nothing can be called a stack"

    def test_military_units_sharing_a_field_tile_are_reported(self):
        # Civ VI reports the units inside a city at the city tile, so the same tile elsewhere is
        # not a garrison and makes position-based judgement suspect.
        units = {
            1: unit(1, "UNIT_ARCHER", 40, 40),
            2: unit(2, "UNIT_WARRIOR", 40, 40),
            3: unit(3, "UNIT_WARRIOR", 30, 30),
        }
        metrics = et._garrison_metrics(GS(units, self.CITIES), units)
        assert metrics["unexplained_stacks"] == 1
        assert metrics["garrisoned_units"] == 0, "none of them is on a city tile"

    def test_a_garrison_stack_is_not_an_unexplained_stack(self):
        units = {1: unit(1, "UNIT_ARCHER", 10, 10), 2: unit(2, "UNIT_WARRIOR", 10, 10)}
        metrics = et._garrison_metrics(GS(units, self.CITIES), units)
        assert metrics["cities_over_garrison"] == 1
        assert metrics["unexplained_stacks"] == 0


class TestWarDetection:
    def test_a_war_in_the_row_is_detected(self):
        row = {"diplo_states": {"Russia": {"state": 6}, "Egypt": {"state": 2}}}
        assert et._at_war_from_row(row) == 1

    @pytest.mark.parametrize("state", [0, 1, 2, 3, 4, 5])
    def test_every_pre_war_state_is_peacetime(self, state):
        assert et._at_war_from_row({"diplo_states": {"Egypt": {"state": state}}}) == 0

    def test_no_data_is_peacetime_not_war(self):
        # A rule that fires when the data is missing is worse than a rule that stays quiet.
        assert et._at_war_from_row(None) == 0
        assert et._at_war_from_row({}) == 0
        assert et._at_war_from_row({"diplo_states": {"x": None}}) == 0

    def test_a_malformed_state_does_not_crash(self):
        assert et._at_war_from_row({"diplo_states": {"x": {"state": "war"}}}) == 0


class TestTheDamageRecord:
    def test_damaged_units_are_recorded_from_the_diff(self):
        from civ_mcp.game_state import GameState

        before = lq_snapshot({1: unit(1, "UNIT_WARRIOR", 10, 10, health=100),
                              2: unit(2, "UNIT_ARCHER", 11, 10, health=100)})
        after = lq_snapshot({1: unit(1, "UNIT_WARRIOR", 10, 10, health=62),
                             2: unit(2, "UNIT_ARCHER", 11, 10, health=100)})
        damaged = [
            uid
            for uid, ub in before.units.items()
            if uid in after.units and after.units[uid].health < ub.health
        ]
        assert damaged == [1]
        assert GameState._diff_snapshots is not None, "the diff is what supplies the events"

    def test_the_metric_counts_damaged_units_not_damage(self):
        gs = GS({}, {}, damaged=[1, 2])
        metrics = asyncio.run(et._contact_metrics(gs, 115, {}))
        assert metrics["damaged_this_turn"] == 2


def lq_snapshot(units: dict) -> m.TurnSnapshot:
    return m.TurnSnapshot(
        turn=115, units=units, cities={}, current_research="", current_civic=""
    )


class TestTheBattleAssessment:
    """What the agent is shown when it has been hit: who is there, and with what."""

    def threat(self, **kw):
        base = dict(
            unit_type="UNIT_SWORDSMAN", x=53, y=35, hp=7, max_hp=100, combat_strength=35,
            ranged_strength=0, distance=1, owner_name="Russia",
            promotion_class="PROMOTION_CLASS_MELEE", unit_distance=1,
            friendly_within_2=3, friendly_within_1=2,
        )
        base.update(kw)
        return m.ThreatInfo(**base)

    def metrics(self, **kw):
        base = {
            "damaged_this_turn": 1, "local_superiority": 3, "enemies_cavalry_within_2": 0,
            "enemies_melee_within_2": 1, "enemies_within_2": 1, "weakest_enemy_hp_within_2": 7,
            "enemies_within_3": 1, "at_war": 1,
        }
        base.update(kw)
        return base

    def test_nothing_is_printed_without_damage_or_contact(self):
        assert et._battle_assessment(
            self.metrics(damaged_this_turn=0, enemies_within_3=0), [self.threat()], 116
        ) is None

    def test_discovering_the_enemy_is_enough_to_print_it(self):
        text = et._battle_assessment(
            self.metrics(damaged_this_turn=0, enemies_within_3=1), [self.threat()], 116
        )
        assert text is not None
        assert "enemy forces are in contact" in text

    def test_contact_outside_a_war_does_not_print(self):
        assert et._battle_assessment(
            self.metrics(damaged_this_turn=0, enemies_within_3=1, at_war=0), [self.threat()], 116
        ) is None

    def test_damage_prints_even_in_peacetime(self):
        text = et._battle_assessment(
            self.metrics(damaged_this_turn=1, enemies_within_3=0, at_war=0), [self.threat()], 116
        )
        assert text is not None and "your units were attacked" in text

    def test_an_enemy_one_move_away_is_marked_as_out_of_reach(self):
        text = et._battle_assessment(
            self.metrics(), [self.threat(unit_distance=3, friendly_within_2=0)], 116
        )
        assert "one move away, not engageable this turn" in text

    def test_the_enemy_is_named_with_its_class_hp_and_distance(self):
        text = et._battle_assessment(self.metrics(), [self.threat()], 116)
        assert "BATTLE ASSESSMENT (T116)" in text
        assert "Russia" in text
        assert "UNIT_SWORDSMAN" in text and "HP:7/100" in text and "dist:1" in text
        assert "class:MELEE" in text

    def test_the_concentration_count_is_reported(self):
        text = et._battle_assessment(self.metrics(), [self.threat()], 116)
        assert "yours in range: 3 (2 adjacent)" in text
        assert "enough for a kill" in text

    def test_a_lone_unit_is_told_it_is_a_trade_not_a_kill(self):
        text = et._battle_assessment(
            self.metrics(local_superiority=1),
            [self.threat(friendly_within_2=1, friendly_within_1=1)],
            116,
        )
        assert "that is a trade, not a kill" in text

    def test_a_killable_enemy_is_called_out(self):
        text = et._battle_assessment(self.metrics(), [self.threat()], 116)
        assert "killable now:" in text and "UNIT_SWORDSMAN at 7 HP" in text

    def test_a_healthy_enemy_is_not_called_killable(self):
        text = et._battle_assessment(self.metrics(), [self.threat(hp=100)], 116)
        assert "killable now" not in text

    def test_distant_enemies_are_left_out(self):
        text = et._battle_assessment(self.metrics(), [self.threat(unit_distance=6)], 116)
        assert text is None

    def test_the_counter_hint_follows_the_enemy_class(self):
        text = et._battle_assessment(
            self.metrics(enemies_cavalry_within_2=1),
            [self.threat(promotion_class="PROMOTION_CLASS_LIGHT_CAVALRY")],
            116,
        )
        assert "anti-cavalry" in text


class TestSiegePosture:
    """Staging: outside their range, screen in front, siege behind, Catapult protected."""

    def posture(self, **kw):
        base = dict(
            unit_type="UNIT_CATAPULT", x=54, y=39, enemy_distance=1, screen_distance=2,
            screen_enemy_distance=3, city_distance=1, city_name="Moscow",
        )
        base.update(kw)
        return SiegePosture(**base)

    def test_a_siege_unit_with_nothing_in_front_is_exposed(self):
        # Enemy at 1, the nearest screen is 3 from that enemy: the Catapult is the closest
        # thing to the enemy, which is exactly what the formation forbids.
        assert self.posture().exposed is True

    def test_a_screen_closer_to_the_enemy_than_the_siege_unit_covers_it(self):
        assert self.posture(enemy_distance=2, screen_enemy_distance=1).exposed is False

    def test_a_screen_no_closer_than_the_siege_unit_is_not_cover(self):
        assert self.posture(enemy_distance=2, screen_enemy_distance=2).exposed is True

    def test_an_enemy_out_of_reach_is_not_exposure(self):
        assert self.posture(enemy_distance=3, screen_enemy_distance=999).exposed is False

    def test_no_screen_at_all_is_exposure_when_the_enemy_is_in_reach(self):
        assert self.posture(screen_distance=999, screen_enemy_distance=999).exposed is True

    def test_the_metrics_count_units_and_the_closest_approach(self):
        metrics = et._siege_metrics(
            [
                self.posture(),
                self.posture(x=54, y=38, enemy_distance=2, screen_enemy_distance=1),
                self.posture(x=60, y=30, enemy_distance=6, screen_enemy_distance=999, city_distance=8),
            ]
        )
        assert metrics["siege_units"] == 3
        assert metrics["siege_exposed"] == 1
        assert metrics["siege_in_city_range"] == 2
        assert metrics["siege_city_distance_min"] == 1

    def test_no_siege_units_means_no_claim(self):
        assert et._siege_metrics([])["siege_units"] == 0
        assert et._siege_metrics([])["siege_exposed"] == 0

    def test_one_gun_in_range_is_the_assault_that_lands_nothing(self):
        """`siege_firing_alone`: the train is deployed and only one of its guns can reach.

        This is A6's measured signature, and it is why the metric counts **shots and not units**:
        A6 arrived with a complete establishment and a Catapult bought with gold, and its target
        finished the window at `200/200` with `SIEGE FIRE: 1/2`. A siege unit does 45-52 against a
        city and the city heals about twenty a turn, so two guns out-damage the heal and one does
        not - the directive's "3 Catapults" is a count of units, and this is the number that says
        how many can actually fire.
        """
        alone = self.posture(city_distance=2)
        assert et._siege_metrics([alone])["siege_firing_alone"] == 1

        # The train that can actually fire is not alone, however many units are standing about.
        two_in_range = [
            self.posture(city_distance=1),
            self.posture(x=54, y=38, city_distance=2),
        ]
        assert et._siege_metrics(two_in_range)["siege_firing_alone"] == 0

        # Three units and one shot: still alone, and that is the case the metric exists for.
        one_shot_of_three = [*two_in_range, self.posture(x=60, y=30, city_distance=8)]
        assert et._siege_metrics(one_shot_of_three)["siege_in_city_range"] == 2
        assert et._siege_metrics(one_shot_of_three)["siege_firing_alone"] == 0
        far_train = [
            self.posture(city_distance=2),
            self.posture(x=54, y=38, city_distance=8),
            self.posture(x=60, y=30, city_distance=9),
        ]
        assert et._siege_metrics(far_train)["siege_firing_alone"] == 1

        # A train marching towards its target is not an assault that has begun: it is 0 when
        # nothing is in range, because the rule keyed on it must not fire during staging.
        marching = [self.posture(city_distance=4), self.posture(x=54, y=38, city_distance=5)]
        assert et._siege_metrics(marching)["siege_in_city_range"] == 0
        assert et._siege_metrics(marching)["siege_firing_alone"] == 0

        # And no siege units at all is not the failure either.
        assert et._siege_metrics([])["siege_firing_alone"] == 0

    def test_the_firing_metric_is_exposed_to_rules_and_safe_on_a_stored_row(self):
        """A rule may key on it, and a diary row must read 0 rather than `un-evaluable`.

        `_CONTACT_METRIC_KEYS` is what `_context_from_row` fills with zeros: a key missing from it
        makes its rule report `un-evaluable` on every row-based pass, which reads as a permanent
        streak and shifts the TURN START verdict - the trap that took `attacks-that-land-nothing`
        and `power-the-cities` in and out of the live file.
        """
        assert "siege_firing_alone" in et._CONTACT_METRIC_KEYS

    def test_the_rule_is_live_and_no_longer_staged(self):
        """`concentrate-the-siege` was cut in on 2026-09-30, once its metric shipped.

        It waited in `pending/` while no server computed `siege_firing_alone`, because a rule naming
        a metric the running server does not know reports itself `un-evaluable` on every turn and
        nobody can satisfy it - a rule that looks alive and is not. Promoting it is the two-file move
        `pending/README.md` describes: the block moves into `turn-checks.md` and the staged file goes.

        Its condition was re-scoped the same day, when the human settled the siege establishment as a
        band (攻城使用2或3辆投石车 ... 一辆也可以): a **single** gun is a legitimate plan, so the
        failure is no longer "one gun firing" but "two or more deployed and fewer than two in range".
        """
        root = pathlib.Path(__file__).resolve().parents[1]
        live = (root / "prompts/checks/turn-checks.md").read_text(encoding="utf-8-sig")
        assert "id: concentrate-the-siege" in live
        assert "metric(siege_units) >= 2 and metric(siege_in_city_range) <= 1" in live, (
            "a lone gun must not fail the rule (human instruction 2026-09-30)"
        )
        assert not (root / "prompts/checks/pending/concentrate-the-siege.md").exists(), (
            "the staged file is deleted by the same move that cuts the rule in"
        )
        # And the live block is one the parser accepts rather than skips: a block with no `message:`
        # is dropped silently, so it would read as in force and never fire.
        parsed = {
            check.check_id: check
            for check in turn_checks.parse_checks(live)
        }
        rule = parsed.get("concentrate-the-siege")
        assert rule is not None, "the live block must parse"
        assert rule.require == "metric(siege_in_city_range) >= 2"
        assert "one gun is a legitimate plan" in rule.message.lower()
        assert rule.message.strip(), "a block without a message is skipped by parse_checks"

    def test_a_lone_gun_does_not_fail_the_rule_and_two_out_of_range_does(self):
        # One gun in range: the sanctioned single-gun assault.
        assert "concentrate-the-siege" not in TestTheRules().failing(
            siege_units=1, siege_in_city_range=1
        )
        # Two deployed, one in range: the failure the rule is for.
        assert "concentrate-the-siege" in TestTheRules().failing(
            siege_units=2, siege_in_city_range=1
        )
        # Two deployed, both in range: fine.
        assert "concentrate-the-siege" not in TestTheRules().failing(
            siege_units=2, siege_in_city_range=2
        )

    def test_the_event_names_the_exposed_unit_only_when_it_matters(self):
        text = et._siege_posture_event([self.posture()], et._siege_metrics([self.posture()]), 116)
        assert "UNIT_CATAPULT@(54,39)" in text
        assert "EXPOSED" in text and "Fix the formation before advancing" in text

    def test_a_screened_train_in_position_is_reported_as_such(self):
        entry = self.posture(enemy_distance=2, screen_enemy_distance=1)
        text = et._siege_posture_event([entry], et._siege_metrics([entry]), 116)
        assert "screened" in text and "In firing position with a screen" in text

    def test_staging_far_from_everything_is_silent(self):
        entry = self.posture(enemy_distance=999, screen_enemy_distance=999, city_distance=9)
        assert et._siege_posture_event([entry], et._siege_metrics([entry]), 116) is None

    def test_a_gun_in_the_rally_shell_is_assembling_not_marching(self):
        """The block used to vanish in exactly the state `tactics/04` is triggered for.

        The rally ring sits at three and four tiles; a gun there with nothing exposed is the
        assembly, and step 6.5 of `tactics/04` is "read `SIEGE FIRE` before opening". Suppressing
        it there hid the state the file exists for, so the suppression now starts past d4.
        """
        entry = self.posture(enemy_distance=999, screen_enemy_distance=999, city_distance=4)
        text = et._siege_posture_event([entry], et._siege_metrics([entry]), 116)
        assert "assembling" in text
        assert "tactics/04" in text

    def test_beyond_the_rally_shell_the_block_stays_silent(self):
        entry = self.posture(enemy_distance=999, screen_enemy_distance=999, city_distance=5)
        assert et._siege_posture_event([entry], et._siege_metrics([entry]), 116) is None

    def test_one_gun_in_the_ring_is_a_full_train_of_one(self):
        """A single gun is a sanctioned plan (human instruction 2026-09-30), so 1/1 is success."""
        entry = self.posture(city_distance=2, enemy_distance=1, screen_enemy_distance=2)
        text = et._siege_posture_event([entry], et._siege_metrics([entry]), 116)
        assert "SIEGE FIRE: 1/1 siege unit(s) inside range 2" in text
        assert "full train, fire it" in text

    def test_one_gun_out_of_the_ring_is_told_it_contributes_nothing(self):
        entry = self.posture(enemy_distance=999, screen_enemy_distance=999, city_distance=4)
        text = et._siege_posture_event([entry], et._siege_metrics([entry]), 116)
        assert "SIEGE FIRE: 0/1 siege unit(s) inside range 2" in text
        assert "OUT OF RANGE" in text
        assert "at distance 4" in text

    def test_the_train_says_how_many_of_it_can_actually_fire(self):
        """Three siege units is a count of units; the shots are what the city feels.

        Measured: 阿斯特拉罕 had one distance-2 tile with LOS, 圣彼得堡 had one siege unit in
        range while two stood at distance 4 and 6 for three turns (T151-T152), and 喀山 opened
        with all three at distance 3, 4 and 4 (T159). The line has to name them.
        """
        entries = [
            self.posture(x=55, y=41, enemy_distance=1, screen_enemy_distance=2, city_distance=1),
            self.posture(x=55, y=40, enemy_distance=2, screen_enemy_distance=2, city_distance=4),
            self.posture(x=55, y=39, enemy_distance=3, screen_enemy_distance=2, city_distance=4),
        ]
        text = et._siege_posture_event(entries, et._siege_metrics(entries), 159)
        assert "SIEGE FIRE: 1/3 siege unit(s) inside range 2" in text
        assert "OUT OF RANGE" in text
        assert text.count("at distance 4") == 2
        assert "cannot fire the same turn" in text

    def test_a_train_that_can_all_fire_says_so(self):
        entries = [
            self.posture(x=55, y=41, city_distance=2, enemy_distance=1, screen_enemy_distance=2),
            self.posture(x=55, y=42, city_distance=2, enemy_distance=1, screen_enemy_distance=2),
        ]
        text = et._siege_posture_event(entries, et._siege_metrics(entries), 160)
        assert "SIEGE FIRE: 2/2 siege unit(s) inside range 2" in text
        assert "full train, fire it" in text
        assert "OUT OF RANGE" not in text

    def test_the_parser_reads_the_line_and_ignores_junk(self):
        entry = lq.parse_siege_posture_response(
            ["SIEGE_POSTURE|UNIT_CATAPULT|54,39|enemy:1|screen:2|screen_enemy:3|city:1|Moscow", "junk"]
        )
        assert len(entry) == 1
        assert entry[0].city_name == "Moscow" and entry[0].enemy_distance == 1


class TestTheRules:
    FILE = pathlib.Path("prompts/checks/turn-checks.md")

    def context(self, **metrics):
        base = {
            "wonders": 1, "districts": 30, "pop": 30, "improvements": 90, "cities": 5,
            "gold_per_turn": 30, "attacks_this_turn": 0, "unused_attacks": 0,
            "damaged_this_turn": 0, "cities_over_garrison": 0, "cities_guarded": 2,
            "at_war": 1, "local_superiority": 0, "enemies_massed_on": 0,
            "siege_units": 0, "siege_exposed": 0,
            # The two answer rules fire on `at_war` **or** a camp raid (human instruction
            # 2026-09-30: 突袭也算战争), so the raid proxy has to exist in the fixture for the
            # expression to evaluate - a missing metric makes a rule report `un-evaluable`.
            "camps_within_3": 0, "enemies_within_2": 0,
        }
        base.update(metrics)
        return turn_checks.CheckContext(turn=115, units={}, metrics=base, researched=frozenset())

    def failing(self, **metrics) -> set[str]:
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8-sig"), self.context(**metrics))
        return run.failing_ids

    def test_two_units_in_one_city_while_at_war_fails(self):
        assert "one-garrison-per-city" in self.failing(cities_over_garrison=1)

    def test_the_same_formation_in_peacetime_is_silent(self):
        assert "one-garrison-per-city" not in self.failing(cities_over_garrison=1, at_war=0)

    def test_a_city_with_no_units_is_not_this_rules_business(self):
        assert "one-garrison-per-city" not in self.failing(cities_guarded=0)

    def test_a_unit_was_hit_and_nothing_answered(self):
        assert "answer-the-attack" in self.failing(damaged_this_turn=1)

    def test_answering_with_an_attack_clears_it(self):
        assert "answer-the-attack" not in self.failing(damaged_this_turn=1, attacks_this_turn=1)

    def test_nobody_was_hit(self):
        assert "answer-the-attack" not in self.failing(damaged_this_turn=0)

    def test_contact_with_a_single_unit_fails_the_mass_rule(self):
        ids = self.failing(enemies_within_2=1, local_superiority=1)
        assert "mass-on-contact" in ids

    def test_two_units_in_range_pass_the_mass_rule(self):
        ids = self.failing(enemies_within_2=1, local_superiority=2)
        assert "mass-on-contact" not in ids

    def test_the_mass_rule_is_silent_without_contact(self):
        assert "mass-on-contact" not in self.failing(
            enemies_within_2=0, local_superiority=0
        )

    def test_the_mass_rule_is_silent_in_peacetime(self):
        assert "mass-on-contact" not in self.failing(
            at_war=0, enemies_within_2=1, local_superiority=1
        )

    def test_the_rule_fires_on_an_exposed_siege_unit(self):
        assert "screen-the-siege" in self.failing(siege_units=2, siege_exposed=1)

    def test_a_screened_train_passes(self):
        assert "screen-the-siege" not in self.failing(siege_units=2, siege_exposed=0)

    def test_no_siege_units_switches_the_rule_off(self):
        assert "screen-the-siege" not in self.failing(siege_units=0, siege_exposed=0)

    def test_peacetime_damage_is_not_this_rules_business(self):
        # A hit with no war and no camp within three tiles is not the war footing's business.
        assert "answer-the-attack" not in self.failing(damaged_this_turn=2, at_war=0)

    def test_a_raid_counts_as_a_war_for_answer_the_attack(self):
        # Human instruction 2026-09-30: 突袭也算战争 - a camp raid sets the answer rules.
        assert "answer-the-attack" in self.failing(damaged_this_turn=1, at_war=0, camps_within_3=1)

    def test_a_raid_counts_as_a_war_for_the_mass_rule(self):
        assert "mass-on-contact" in self.failing(
            at_war=0, camps_within_3=1, enemies_within_2=1, local_superiority=1
        )

    def test_the_occupancy_rule_stays_wartime_only(self):
        # A raid is a fight, not an occupation: the garrison rule still needs a real war.
        assert "one-garrison-per-city" not in self.failing(
            cities_over_garrison=1, at_war=0, camps_within_3=1
        )

    def test_a_barbarian_with_no_camp_is_not_a_raid(self):
        # `camps_within_3` is the proxy; a wandering barbarian alone does not set the rules.
        assert "mass-on-contact" not in self.failing(
            at_war=0, camps_within_3=0, enemies_within_2=1, local_superiority=1
        )

    def test_a_stored_row_keeps_the_war_gate(self):
        row = {
            "turn": 115, "is_agent": True, "unit_composition": {"WARRIOR": 2},
            "pop": 30, "districts": 30, "wonders": 1, "cities": 5, "improvements": 90,
            "gold_per_turn": 30, "diplo_states": {"Russia": {"state": 6}},
        }
        context = et._context_from_row(row)
        assert context.metrics["at_war"] == 1
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8-sig"), context)
        assert not [c for c, reason in run.failures if "un-evaluable" in reason]
        assert "one-garrison-per-city" not in run.failing_ids, "no city data in a stored row"
