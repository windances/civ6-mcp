"""`get_target_report`: one target, read the way the pre-war analysis asks about it.

`tactics/07` is a procedure in seven steps, and its first three are questions about the *target*: is
it visible, how much wall and city pool is there, what is garrisoning it, and what can shoot at it.
Three of those (walls, the city centre pool, the garrison unit) are invisible to every metric the
turn loop has, so they were being read by hand or not at all. This tool is one call for them, and it
has to work **before a declaration** and **in fog** - the point of a pre-war analysis is that the
target is somewhere else on the map.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import narrate as nr  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402

TILE = "TTILE|58,42|visible|TERRAIN_GRASS_HILLS|FEATURE_FOREST|1|0|IMPROVEMENT_FARM|0|DISTRICT_CITY_CENTER|1|Russia"
CITY = (
    "TCITY|Moscow|1|Russia|pop:3|walls:80/100|cityhp:150/200|def:39"
    "|garrison:UNIT_MAN_AT_ARMS|garrisonhp:70/100|garrisoncs:45|capital:1|atwar:0|ours:0"
)
ENEMY = (
    "TENEMY|1|Russia|UNIT_ARCHER|56,41|80/100|CS:15|RS:25"
    "|pc:PROMOTION_CLASS_RANGED|d:2|atwar:0|fort:2"
)


class TestTheParser:
    def test_the_tile_the_city_and_the_units_all_read(self):
        tile, city, enemies = lq.parse_target_probe_response([TILE, CITY, ENEMY])
        assert (tile.x, tile.y) == (58, 42)
        assert tile.visibility == "visible" and tile.hills and tile.feature == "FEATURE_FOREST"
        assert tile.district == "DISTRICT_CITY_CENTER" and tile.owner_name == "Russia"
        assert city.name == "Moscow" and city.pop == 3
        assert (city.wall_hp, city.wall_max) == (80, 100)
        assert (city.hp, city.hp_max) == (150, 200)
        assert city.garrisoned and city.garrison == "UNIT_MAN_AT_ARMS" and city.garrison_cs == 45
        assert city.capital and not city.at_war and not city.ours
        assert enemies[0].unit_type == "UNIT_ARCHER" and enemies[0].distance == 2
        assert enemies[0].class_name == "RANGED" and enemies[0].fortified_turns == 2

    def test_a_tile_in_fog_parses_as_fog_not_as_empty(self):
        tile, city, enemies = lq.parse_target_probe_response(
            ["TTILE|58,42|revealed|TERRAIN_GRASS|none|0|0|none|0|none|-1|none"]
        )
        assert tile.visibility == "revealed" and not tile.seen
        assert city is None and enemies == []

    def test_a_camp_is_the_tile_improvement(self):
        tile, _, _ = lq.parse_target_probe_response(
            ["TTILE|60,29|visible|TERRAIN_GRASS|none|0|0|IMPROVEMENT_BARBARIAN_CAMP|0|none|-1|none", "TCAMP|1"]
        )
        assert tile.camp

    def test_a_city_with_no_garrison_says_so(self):
        _, city, _ = lq.parse_target_probe_response(
            ["TCITY|Moscow|1|Russia|pop:1|walls:0/0|cityhp:200/200|def:20|garrison:none"
             "|garrisonhp:0/0|garrisoncs:0|capital:0|atwar:1|ours:0"]
        )
        assert city is not None and not city.garrisoned and not city.walled and city.at_war

    def test_an_unanswered_probe_returns_no_tile_rather_than_raising(self):
        tile, city, enemies = lq.parse_target_probe_response(["ERR:INVALID_TARGET|58,42"])
        assert tile is None and city is None and enemies == []

    def test_an_empty_response_is_not_a_crash(self):
        assert lq.parse_target_probe_response([]) == (None, None, [])


class TestTheQuery:
    def test_it_asks_the_target_anchored_questions(self):
        q = lq.build_target_probe_query(58, 42)
        for token in ('print("TTILE|"', 'print("TCITY|"', 'print("TENEMY|"', 'print("TCAMP|1")'):
            assert token in q, token
        assert "Cities.GetCityInPlot" in q
        assert "DefenseTypes.DISTRICT_OUTER" in q and "DefenseTypes.DISTRICT_GARRISON" in q
        assert "u:GetFortifyTurns()" in q
        assert "IMPROVEMENT_BARBARIAN_CAMP" in q

    def test_it_is_read_only(self):
        q = lq.build_target_probe_query(58, 42)
        for write in ("RequestOperation", "RequestCommand", "SetProduction", "end_turn"):
            assert write not in q, write

    def test_it_reports_visibility_instead_of_assuming_it(self):
        q = lq.build_target_probe_query(58, 42)
        assert "pVis:IsVisible(idx)" in q and "pVis:IsRevealed(idx)" in q
        assert 'visTag = "fog"' in q and 'visTag = "revealed"' in q

    def test_enemy_units_are_distance_bounded_and_visibility_filtered(self):
        q = lq.build_target_probe_query(58, 42, radius=3)
        assert "Map.GetPlotDistance(tx, ty, ux, uy)" in q
        assert "if d <= r then" in q
        assert "pVis:IsVisible(ux, uy)" in q
        assert "local tx, ty, r = 58, 42, 3" in q


def tile(**kw):
    base = dict(
        x=58,
        y=42,
        visibility="visible",
        terrain="TERRAIN_GRASS_HILLS",
        hills=True,
        district="DISTRICT_CITY_CENTER",
        owner=1,
        owner_name="Russia",
    )
    base.update(kw)
    return lq.TargetTile(**base)


def city(**kw):
    base = dict(
        name="Moscow",
        owner=1,
        owner_name="Russia",
        pop=3,
        wall_hp=100,
        wall_max=100,
        hp=200,
        hp_max=200,
        defense=39,
        garrison="UNIT_MAN_AT_ARMS",
        garrison_hp=100,
        garrison_max=100,
        garrison_cs=45,
    )
    base.update(kw)
    return lq.TargetCity(**base)


def plan(units, options, ring):
    return m.StagingPlan(target="58,42", ring=ring, units=units, options=options)


def unit(uid, kind, role, x=55, y=41, moves=2):
    return m.StagingUnit(unit_type=kind, unit_id=uid, x=x, y=y, moves=moves, role=role)


class TestTheReport:
    def test_a_walled_garrisoned_city_is_read_in_full(self):
        report = lq.TargetReport(tile=tile(), city=city())
        text = nr.narrate_target_report(report)
        assert "Moscow" in text and "Russia" in text and "at peace" in text
        assert "pop 3" in text
        assert "walls 100/100" in text and "city HP 200/200" in text and "defence 39" in text
        assert "garrison UNIT_MAN_AT_ARMS (100/100 hp, CS 45)" in text
        assert "original capital" not in text

    def test_a_city_with_no_garrison_is_called_out_as_the_cheaper_siege(self):
        report = lq.TargetReport(tile=tile(), city=city(garrison="none"))
        text = nr.narrate_target_report(report)
        assert "no garrison unit" in text
        assert "three times" in text

    def test_fog_is_reported_as_fog_and_points_at_gate_0(self):
        report = lq.TargetReport(tile=tile(visibility="revealed"))
        text = nr.narrate_target_report(report)
        assert "not visible now" in text and "Gate 0" in text

    def test_a_camp_is_a_target_too(self):
        report = lq.TargetReport(tile=tile(camp=True, district="none", improvement="IMPROVEMENT_BARBARIAN_CAMP"))
        text = nr.narrate_target_report(report)
        assert "barbarian camp at (58,42)" in text
        assert "no city and no camp" not in text

    def test_the_enemies_near_the_target_are_listed_with_their_class(self):
        enemy = lq.TargetEnemy(
            player_id=1,
            owner_name="Russia",
            unit_type="UNIT_ARCHER",
            x=56,
            y=41,
            hp=80,
            max_hp=100,
            combat_strength=15,
            ranged_strength=25,
            promotion_class="PROMOTION_CLASS_RANGED",
            distance=2,
        )
        text = nr.narrate_target_report(lq.TargetReport(tile=tile(), city=city(), enemies=[enemy]))
        assert "Russia ARCHER CS 15/RS 25 HP 80/100 at (56,41) d2 [ranged]" in text
        assert "(NOT at war)" in text

    def test_no_visible_enemy_is_not_none_exists(self):
        text = nr.narrate_target_report(lq.TargetReport(tile=tile(), city=city()))
        assert "none visible" in text and "not 'none exist'" in text

    def test_the_arithmetic_comes_from_the_guns_that_can_fire(self):
        units = [unit(12, "UNIT_TREBUCHET", "siege"), unit(13, "UNIT_TREBUCHET", "siege")]
        ring = [m.StagingRingTile(x=56, y=43, distance=2, between=[(57, 43, 0)])]
        options = [
            m.StagingOption(unit_id=12, x=56, y=43, turns=0, this_turn=True),
        ]
        report = lq.TargetReport(tile=tile(), city=city(wall_hp=90, wall_max=100), plan=plan(units, options, ring))
        text = nr.narrate_target_report(report)
        # One Trebuchet reaches the ring (45 a turn), so 90 wall HP is two turns, not one.
        assert "90 wall HP at 45 = **~2 turn(s)**" in text
        assert "upper bound" in text

    def test_no_gun_in_position_says_the_wall_pool_is_not_the_plan(self):
        units = [unit(12, "UNIT_TREBUCHET", "siege")]
        ring = [m.StagingRingTile(x=56, y=43, distance=2, between=[(57, 43, 2)], hills=True)]
        options = [m.StagingOption(unit_id=12, x=56, y=43, turns=0, this_turn=True)]
        report = lq.TargetReport(tile=tile(), city=city(), plan=plan(units, options, ring))
        text = nr.narrate_target_report(report)
        assert "no siege unit can fire at this target" in text

    def test_the_staging_plan_comes_with_it(self):
        units = [unit(12, "UNIT_CATAPULT", "siege")]
        ring = [m.StagingRingTile(x=56, y=43, distance=2, between=[(57, 43, 0)])]
        options = [m.StagingOption(unit_id=12, x=56, y=43, turns=0, this_turn=True)]
        text = nr.narrate_target_report(
            lq.TargetReport(tile=tile(), city=city(), plan=plan(units, options, ring))
        )
        assert "STAGING PLAN for 58,42" in text
        assert "FIRE from here" in text

    def test_it_says_what_it_does_not_answer(self):
        text = nr.narrate_target_report(lq.TargetReport(tile=tile(), city=city()))
        assert "not answered here" in text
        assert "gates 4, 5 and 7" in text


class TestTheComposition:
    def test_the_report_is_a_probe_and_a_staging_plan(self):
        """Two queries, one answer: the probe is target-anchored, the plan is the assault's own."""
        from civ_mcp.game_state import GameState

        queries: list[str] = []

        class FakeConn:
            async def execute_write(self, lua, timeout=5.0):
                queries.append(lua)
                if "TTILE|" in lua:
                    return [TILE, CITY, ENEMY]
                return [
                    "STAGEPLAN|58,42|ring:1|camp:0",
                    "RING|56,43|2|ok|land|hill:0|sight:0|via:57,43,0",
                    "UNIT|UNIT_CATAPULT|12|55,41|2|siege|d4|cs25|hp100/100",
                    "OPTION|12|56,43|0|1|4",
                ]

        gs = GameState.__new__(GameState)
        gs.conn = FakeConn()
        report = asyncio.run(gs.target_report(58, 42))
        assert len(queries) == 2
        assert report.city is not None and report.city.name == "Moscow"
        assert report.tile.owner_name == "Russia"
        assert report.enemies and report.enemies[0].unit_type == "UNIT_ARCHER"
        assert report.plan is not None and report.plan.ring
        text = nr.narrate_target_report(report)
        assert "TARGET REPORT for Moscow" in text and "STAGING PLAN" in text

    def test_an_invalid_target_still_reports_the_fog_it_is(self):
        from civ_mcp.game_state import GameState

        class FakeConn:
            async def execute_write(self, lua, timeout=5.0):
                if "TTILE|" in lua:
                    return ["ERR:INVALID_TARGET|58,42"]
                return ["STAGEPLAN|58,42|ring:0|camp:0"]

        gs = GameState.__new__(GameState)
        gs.conn = FakeConn()
        report = asyncio.run(gs.target_report(58, 42))
        assert report.tile.visibility == "fog"
        assert "not visible now" in nr.narrate_target_report(report)
