"""The two telemetry gaps that made the T101-T116 siege unreadable, closed and pinned.

1. **City HP was dropped for an unwalled city.** The attack result built its city line behind
   `if w_max > 0`, so a city without walls reported no city number at all - and an unwalled city
   is exactly the case where the city HP pool is the only progress there is. Twelve turns of
   Catapult fire at Moscow produced no city number on either side of the table.
2. **Our own losses were not reported.** The damage report came from the snapshot diff, whose
   baseline is not always pre-AI on a blocker or mid-turn-diplomacy re-entry; the Heavy Chariot
   went 74 -> 55 HP with no event recorded, which is why `answer-the-attack` fired once in the
   whole war. The baseline is now recorded at the moment ACTION_ENDTURN is sent.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp.game_state import GameState, _extract_city_defense  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


class TestCityDefenseParsing:
    def test_an_unwalled_city_still_reports_its_hp(self):
        # CITY_DEF|wall:0/0|garrison:197/200 - the game prints this for a city without walls.
        parsed = _extract_city_defense(["CITY_DEF|wall:0/0|garrison:197/200"])
        assert parsed == (0, 0, 197, 200)

    def test_a_walled_city_reports_both(self):
        assert _extract_city_defense(["CITY_DEF|wall:74/100|garrison:150/200"]) == (74, 100, 150, 200)

    def test_no_line_is_none(self):
        assert _extract_city_defense(["UNIT|UNIT_WARRIOR|100/100|owner:1"]) is None


class TestCityHpHistory:
    def _gs(self) -> GameState:
        gs = GameState.__new__(GameState)
        gs._city_hp_history = {}
        gs._last_snapshot = type("Snap", (), {"turn": 110})()
        gs._high_water_turn = 110
        return gs

    def _estimate(self, city: str):
        return type("Est", (), {"target_city": city})()

    def test_an_attack_records_the_city_hp(self):
        gs = self._gs()
        gs._record_city_hp(self._estimate("Moscow"), 182, 200)
        assert gs.city_hp_history()["Moscow"] == [(110, 182, 200)]

    def test_the_same_reading_twice_in_a_turn_is_recorded_once(self):
        gs = self._gs()
        gs._record_city_hp(self._estimate("Moscow"), 182, 200)
        gs._record_city_hp(self._estimate("Moscow"), 182, 200)
        assert len(gs.city_hp_history()["Moscow"]) == 1

    def test_a_field_battle_records_nothing(self):
        gs = self._gs()
        gs._record_city_hp(self._estimate(""), 100, 100)
        assert gs.city_hp_history() == {}

    def test_the_history_is_bounded(self):
        gs = self._gs()
        for hp in range(60):
            gs._record_city_hp(self._estimate("Moscow"), 200 - hp, 200)
            gs._last_snapshot.turn += 1
        assert len(gs.city_hp_history()["Moscow"]) <= 30


class TestSiegeProgressEvent:
    def _gs(self, entries):
        gs = GameState.__new__(GameState)
        gs._city_hp_history = {"Moscow": entries}
        return gs

    def test_progress_is_reported_with_the_delta(self):
        gs = self._gs([(110, 200, 200), (111, 182, 200)])
        text = et._siege_progress_event(gs, 111)
        assert "Moscow: city hp 182/200" in text
        assert "-18 over 2 turn(s)" in text
        assert "hit this turn" in text
        assert "SIEGE STALLED" not in text

    def test_three_flat_turns_is_a_stall(self):
        gs = self._gs([(110, 200, 200), (111, 200, 200), (112, 200, 200)])
        text = et._siege_progress_event(gs, 112)
        assert "SIEGE STALLED" in text
        assert "not lost city HP in 3 recorded turns" in text

    def test_healing_back_is_a_stall_too(self):
        gs = self._gs([(110, 150, 200), (111, 170, 200), (112, 182, 200)])
        assert "SIEGE STALLED" in assert_text(et._siege_progress_event(gs, 112))

    def test_no_history_is_silent(self):
        assert et._siege_progress_event(self._gs([]), 112) is None

    def test_an_old_history_does_not_keep_reporting(self):
        gs = self._gs([(100, 200, 200), (101, 180, 200)])
        assert et._siege_progress_event(gs, 120) is None


def assert_text(text: str | None) -> str:
    assert text is not None
    return text


class TestDamageBaseline:
    def _unit(self, uid: int, health: int) -> m.UnitInfo:
        return m.UnitInfo(
            unit_id=uid, unit_index=uid, name=f"unit{uid}", unit_type="UNIT_WARRIOR",
            x=0, y=0, moves_remaining=2, max_moves=2, health=health, max_health=100,
        )

    def _gs(self, hp_map: dict[int, int], after: dict[int, m.UnitInfo]):
        gs = GameState.__new__(GameState)
        gs._hp_at_end_turn_request = dict(hp_map)
        gs._damaged_last_turn = []
        return gs, type("Snap", (), {"units": after, "cities": {}, "turn": 110})()

    def test_the_pre_request_baseline_is_what_counts(self):
        # The snapshot's baseline (74) is stale: the request-time map says 100, so the unit did
        # take damage while the AI moved and the event list must say so.
        gs, after_snap = self._gs({1: 100}, {1: self._unit(1, 55)})
        baseline = gs._hp_at_end_turn_request
        gs._damaged_last_turn = [
            uid
            for uid, health in baseline.items()
            if uid in after_snap.units and after_snap.units[uid].health < health
        ]
        assert gs._damaged_last_turn == [1]

    def test_an_undamaged_army_reports_nothing(self):
        gs, after_snap = self._gs({1: 100, 2: 80}, {1: self._unit(1, 100), 2: self._unit(2, 80)})
        baseline = gs._hp_at_end_turn_request
        gs._damaged_last_turn = [
            uid
            for uid, health in baseline.items()
            if uid in after_snap.units and after_snap.units[uid].health < health
        ]
        assert gs._damaged_last_turn == []

    def test_a_vanished_unit_is_missing_from_the_baseline_comparison(self):
        # A killed unit is not in `after`, so the HP comparison cannot see it; the end_turn code
        # reports those separately (the `missing` list), and this pins the detection.
        gs, after_snap = self._gs({1: 100, 2: 80}, {1: self._unit(1, 100)})
        missing = [uid for uid in gs._hp_at_end_turn_request if uid not in after_snap.units]
        assert missing == [2]
