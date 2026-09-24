"""Mechanics the game manual settles, and which the repo had guessed at.

Reading the 25th anniversary manual (`.tools/manuals/manual.clean.txt`, extracted with
`.tools/pdf-text.py`, and queryable mid-turn through `search_knowledge`) turned up three places
where our own numbers or doctrine disagreed with the game:

1. **River crossing is -5, not -2.** *RIVERS -> OFFENSIVE PENALTY*: "When attacking across a
   river, the attacking unit gets a -5 modifier to its combat strength." Our estimator said -2,
   so every across-the-river attack looked two points better than the game would resolve it.
2. **A garrison inside a city is not damageable.** *GARRISON UNITS IN CITIES*: a portion of the
   garrisoned unit's combat strength is added to the city's, "the garrisoned unit will take no
   damage when the city is attacked", and it is destroyed only if the city falls. So "ranged
   shoots the garrison" was the wrong order of work - ranged shoots the **city's HP**, and the
   garrison is a target only when it comes out.
3. **A city heals only while it has a supply line.** *HEALING DAMAGE TO CITIES*: "A city heals a
   small amount every turn, even during combat, as long as it has a supply line. A supply line is
   any hex adjacent to the city that is not within an enemy unit's Zone of Control." That makes
   cutting those hexes a real lever - and it is cheaper than out-damaging twenty points a turn.

The middle one is prose and is asserted in its own file; the two measurable ones are pinned here.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

CITY_LINE = (
    "CAPTURE_READY|Moscow|54,40|hp:40|max:200|walls:0/0|owner:1"
    "|melee_adjacent:1|melee_within_2:3|supply:4/6|UNIT_SPEARMAN"
)
OLD_CITY_LINE = (
    "CAPTURE_READY|Moscow|54,40|hp:0|max:200|walls:0/0|owner:1"
    "|melee_adjacent:1|melee_within_2:3|UNIT_SPEARMAN"
)


class TestTheRiverModifier:
    def test_the_estimate_uses_the_manuals_minus_five(self):
        lua = lq.build_combat_estimate_query(1, 54, 40)
        assert "river -5" in lua
        assert "attModTotal = attModTotal - 5" in lua
        assert "river -2" not in lua, "the manual says -5; -2 was a guess"

    def test_only_melee_attacks_are_penalised(self):
        lua = lq.build_combat_estimate_query(1, 54, 40)
        assert "if not isRanged and tgtPlot then" in lua


class TestTheSupplyLine:
    def test_the_scan_measures_it(self):
        lua = lq.build_capture_check_query()
        assert "supply:" in lua
        assert "local nx, ny = cx + sdx, cy + sdy" in lua, "it walks the city's adjacent hexes"
        assert "local cut = false" in lua
        # The rule the count implements is quoted in the Lua where the next reader will look.
        assert "HEALING DAMAGE" in lua
        assert "as long as it has a supply line" in lua

    def test_the_parser_reads_it(self):
        row = lq.parse_capture_readiness_response([CITY_LINE])[0]
        assert (row.supply_covered, row.supply_total) == (4, 6)
        assert row.supply_open == 2 and row.supplied

    def test_a_fully_cut_city_is_not_healing(self):
        cut = CITY_LINE.replace("supply:4/6", "supply:6/6")
        row = lq.parse_capture_readiness_response([cut])[0]
        assert row.supply_open == 0 and not row.supplied

    def test_a_line_without_the_field_still_parses(self):
        row = lq.parse_capture_readiness_response([OLD_CITY_LINE])[0]
        assert row.city_name == "Moscow" and row.melee_unit == "UNIT_SPEARMAN"
        assert row.supply_total == 0 and row.supply_open == 0
        assert not row.supplied, "no data must not read as 'supplied'"

    def test_the_metrics_carry_it(self):
        rows = lq.parse_capture_readiness_response([CITY_LINE, OLD_CITY_LINE])
        metrics = et._capture_metrics(rows)
        assert metrics["enemy_supply_open_min"] == 2
        assert metrics["enemy_cities_supplied"] == 1

    def test_no_city_in_sight_is_neutral(self):
        metrics = et._capture_metrics([])
        assert metrics["enemy_supply_open_min"] == 999
        assert metrics["enemy_cities_supplied"] == 0


class TestTheSiegeProgressShowsIt:
    def _gs(self, entries):
        gs = GameState.__new__(GameState)
        gs._city_hp_history = {"Moscow": entries}
        return gs

    def test_the_line_reports_how_much_of_the_supply_is_cut(self):
        gs = self._gs([(110, 200, 200), (111, 182, 200)])
        rows = lq.parse_capture_readiness_response([CITY_LINE])
        text = et._siege_progress_event(gs, 111, rows) or ""
        assert "supply line 4/6 cut" in text
        assert "still healing" in text

    def test_a_cut_supply_line_says_the_healing_has_stopped(self):
        cut = CITY_LINE.replace("supply:4/6", "supply:6/6")
        rows = lq.parse_capture_readiness_response([cut])
        text = et._siege_progress_event(self._gs([(111, 20, 200)]), 111, rows) or ""
        assert "6/6 cut" in text and "NOT healing" in text

    def test_the_stall_advice_names_the_supply_line_first(self):
        gs = self._gs([(110, 200, 200), (111, 200, 200), (112, 200, 200)])
        text = et._siege_progress_event(gs, 112, []) or ""
        assert "SIEGE STALLED" in text
        assert "cut the supply line" in text
        assert "stand on, or beside, every hex" in text

    def test_it_still_works_without_readiness_rows(self):
        gs = self._gs([(110, 200, 200), (111, 182, 200)])
        text = et._siege_progress_event(gs, 111) or ""
        assert "Moscow: city hp 182/200" in text
        assert "supply line" not in text
