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
    def test_counts_each_role_and_names_the_gap(self):
        units = {
            1: unit(1, "UNIT_ARCHER"),
            2: unit(2, "UNIT_WARRIOR"),
            3: unit(3, "UNIT_CATAPULT"),
        }
        train, missing = _war_train_status(units)
        assert "siege 1/2" in train
        assert "ranged 1/4" in train
        assert "1 siege" in missing and "1 ram/tower" in missing

    def test_a_complete_train_reports_none_missing(self):
        units = {
            1: unit(1, "UNIT_CATAPULT"),
            2: unit(2, "UNIT_TREBUCHET"),
            3: unit(3, "UNIT_WARRIOR"),
            4: unit(4, "UNIT_MAN_AT_ARMS"),
            5: unit(5, "UNIT_BATTERING_RAM"),
            6: unit(6, "UNIT_ARCHER"),
            7: unit(7, "UNIT_ARCHER"),
            8: unit(8, "UNIT_CROUCHING_TIGER"),
            9: unit(9, "UNIT_CROUCHING_TIGER"),
            10: unit(10, "UNIT_HORSEMAN"),
        }
        _, missing = _war_train_status(units)
        assert missing == []

    def test_no_units_is_not_a_crash(self):
        train, missing = _war_train_status({})
        assert "siege 0/2" in train and len(missing) == 5


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
