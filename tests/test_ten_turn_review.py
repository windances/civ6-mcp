"""The every-10-turns review.

The failure it exists for is invisible turn by turn: on 2026-09-20 the empire went from
T30 to T80 with science nearly flat (+6), no wonder at all until T100, three district
slots idle at T120 and no siege unit ever built - while each individual turn looked
reasonable. The MCP measures, the agent judges, and the diary is where the judgement is
recorded, so the review ends by requiring three answers in the turn's diary.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civ_mcp.end_turn import _ten_turn_review_text, _war_train_status  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def unit(uid: int, unit_type: str) -> m.UnitInfo:
    return m.UnitInfo(
        unit_id=uid,
        unit_index=uid,
        name=unit_type,
        unit_type=unit_type,
        x=10,
        y=10,
        moves_remaining=2,
        max_moves=2,
        health=100,
        max_health=100,
    )


def city(city_id: int, name: str, building: str) -> m.CityInfo:
    return m.CityInfo(
        city_id=city_id,
        name=name,
        x=10 + city_id,
        y=20,
        population=4,
        food=1.0,
        production=5.0,
        gold=0.0,
        science=1.0,
        culture=1.0,
        faith=0.0,
        housing=6.0,
        amenities=2,
        turns_to_grow=5,
        currently_building=building,
    )


def row(turn: int, **fields) -> dict:
    base = {
        "turn": turn,
        "is_agent": True,
        "science": 10.0,
        "culture": 10.0,
        "gold_per_turn": 12.0,
        "military": 40,
        "pop": 16,
        "cities": 4,
        "districts": 5,
        "improvements": 11,
        "wonders": 0,
        "territory": 43,
        "techs_completed": 11,
        "civics_completed": 7,
        "reflections": {},
    }
    base.update(fields)
    return base


class TestWarTrainStatus:
    """The train's counts, with siege as a **band** rather than a quota.

    Human instruction 2026-09-30 settled the siege row: two or three Catapults by the arithmetic,
    not hard-coded, and one is enough when the ground and the ranged line cover the wall pool. So
    the shortfall is measured against a floor of one and the row prints the band.
    """

    def test_counts_each_role_and_names_the_gap(self):
        units = {
            1: unit(1, "UNIT_ARCHER"),
            2: unit(2, "UNIT_WARRIOR"),
            3: unit(3, "UNIT_CATAPULT"),
        }
        train, missing = _war_train_status(units)
        assert "siege 1 (want 1-3 by the arithmetic)" in train
        assert "ranged 1/4" in train
        assert not any("siege" in item for item in missing), (
            "one gun is a complete siege plan; the floor is 1, not 3"
        )
        assert "3 ranged" in missing
        assert not any("ram" in item for item in missing), (
            "the train still asks for a ram or tower; human instructions 2026-09-26 and 2026-09-30"
        )

    def test_a_complete_train_reports_none_missing(self):
        # Three siege units is the top of the band, and every other role at its count - the
        # anti-cavalry slot included (human instruction 2026-10-02: it has its own row).
        units = {
            1: unit(1, "UNIT_CATAPULT"),
            2: unit(2, "UNIT_TREBUCHET"),
            3: unit(3, "UNIT_CATAPULT"),
            4: unit(4, "UNIT_WARRIOR"),
            5: unit(5, "UNIT_MAN_AT_ARMS"),
            6: unit(6, "UNIT_SPEARMAN"),
            7: unit(7, "UNIT_BATTERING_RAM"),
            8: unit(8, "UNIT_ARCHER"),
            9: unit(9, "UNIT_ARCHER"),
            10: unit(10, "UNIT_CROUCHING_TIGER"),
            11: unit(11, "UNIT_CROUCHING_TIGER"),
            12: unit(12, "UNIT_HORSEMAN"),
        }
        _, missing = _war_train_status(units)
        assert missing == []

    def test_two_siege_units_are_inside_the_band(self):
        # What the empire had at T110 (2 Catapults) is no longer one short: 2 is inside 1-3.
        train, missing = _war_train_status({1: unit(1, "UNIT_CATAPULT"), 2: unit(2, "UNIT_CATAPULT")})
        assert "siege 2 (want 1-3 by the arithmetic)" in train
        assert not any("siege" in item for item in missing)

    def test_no_siege_unit_at_all_is_the_shortfall(self):
        # One Catapult is the floor, and the rule `siege-train` enforces exactly that.
        train, missing = _war_train_status({1: unit(1, "UNIT_ARCHER")})
        assert "siege 0 (want 1-3 by the arithmetic)" in train
        assert "1 siege" in missing

    def test_a_battering_ram_is_not_a_role(self):
        # It is in the roster and it counts for nothing: the Catapult is the wall-breaker, and
        # since 2026-09-30 neither a ram nor a tower is built or fielded.
        train, missing = _war_train_status({1: unit(1, "UNIT_BATTERING_RAM")})
        assert "ram" not in train
        # siege, melee, anticav, ranged, cavalry - the ram answers none of them
        assert len(missing) == 5

    def test_no_units_is_not_a_crash(self):
        train, missing = _war_train_status({})
        assert "siege 0 (want 1-3 by the arithmetic)" in train and len(missing) == 5


class TestReviewText:
    def test_deltas_and_rates_come_from_the_two_rows(self):
        text = _ten_turn_review_text(
            90,
            row(80, science=10.7, military=39, wonders=0),
            row(90, science=19.8, military=58, wonders=1),
            {},
        )
        assert "T80 -> T90" in text
        assert "science +9.1 (+0.91/t)" in text
        assert "wonders +1" in text

    def test_the_agents_own_words_are_quoted_back(self):
        past = row(80, reflections={"hypothesis": "city 5 lands ~T86", "planning": "mine (51,25)"})
        text = _ten_turn_review_text(90, past, row(90), {})
        assert "city 5 lands ~T86" in text
        assert "mine (51,25)" in text

    def test_idle_district_slots_are_named(self):
        text = _ten_turn_review_text(120, row(110), row(120, pop=31, districts=7), {})
        assert "floor(pop/3)=10" in text
        assert "3 slot(s) idle" in text

    def test_gold_below_the_carrying_capacity_rule_is_flagged(self):
        text = _ten_turn_review_text(120, row(110), row(120, gold_per_turn=-1.0), {})
        assert "BELOW the +10" in text

    def test_a_missing_war_train_is_reported_as_missing(self):
        text = _ten_turn_review_text(120, row(110), row(120), {1: unit(1, "UNIT_ARCHER")})
        assert "MISSING" in text
        assert "siege" in text

    def test_the_three_questions_are_required(self):
        text = _ten_turn_review_text(90, row(80), row(90), {})
        assert "REQUIRED IN THIS TURN'S DIARY" in text
        assert "was this window efficient" in text
        assert "which prerequisite for the next goal" in text
        assert "does the planned completion turn still hold" in text

    def test_no_earlier_row_means_no_review(self):
        assert _ten_turn_review_text(10, None, row(10), {}) is None


class TestWarEconomy:
    """战时战争城市在造平民 (human request 2026-09-26).

    The war city builds the war; the rest of the empire compounds. Both halves are in
    `tactics/08`, and neither is visible in a diary row - the row counts cities, it does not
    say what each one is building. So the line can only exist if the review is handed the
    post-turn city snapshot, and it is advisory: it asks for a sentence, it does not fail a
    rule. A Settler for task 009 in a non-war city is a legitimate answer to it.
    """

    WAR = {"RUSSIA": {"state": 6}}

    def test_it_names_every_city_building_a_civilian(self):
        cities = {
            1: city(1, "Astrakhan", "UNIT_BUILDER"),
            2: city(2, "Chengdu", "UNIT_SETTLER"),
            3: city(3, "Xian", "UNIT_CATAPULT"),
        }
        text = _ten_turn_review_text(
            120, row(110, diplo_states=self.WAR), row(120, diplo_states=self.WAR), {}, cities
        )
        assert "WAR ECONOMY: 2/3 cities building civilians while at war" in text
        assert "Astrakhan UNIT_BUILDER" in text
        assert "Chengdu UNIT_SETTLER" in text
        assert "tactics/08" in text

    def test_no_line_at_peace(self):
        # The same queues in peacetime are just development; nothing to answer for.
        cities = {1: city(1, "Xian", "UNIT_BUILDER")}
        text = _ten_turn_review_text(120, row(110), row(120), {}, cities)
        assert "WAR ECONOMY" not in text

    def test_no_line_when_every_queue_is_military(self):
        cities = {1: city(1, "Xian", "UNIT_CATAPULT"), 2: city(2, "Chengdu", "BUILDING_MONUMENT")}
        text = _ten_turn_review_text(
            120, row(110, diplo_states=self.WAR), row(120, diplo_states=self.WAR), {}, cities
        )
        assert "WAR ECONOMY" not in text

    def test_a_military_engineer_is_not_a_civilian(self):
        # It is a support unit and what it builds is war work: counting it would cry wolf.
        cities = {1: city(1, "Xian", "UNIT_MILITARY_ENGINEER")}
        text = _ten_turn_review_text(
            120, row(110, diplo_states=self.WAR), row(120, diplo_states=self.WAR), {}, cities
        )
        assert "WAR ECONOMY" not in text

    def test_no_city_snapshot_is_not_a_crash(self):
        # An older caller (or a call site with no snapshot) still gets the rest of the review.
        text = _ten_turn_review_text(
            120, row(110, diplo_states=self.WAR), row(120, diplo_states=self.WAR), {}
        )
        assert "WAR ECONOMY" not in text
        assert "REQUIRED IN THIS TURN'S DIARY" in text
        assert "assault prerequisites" in text
