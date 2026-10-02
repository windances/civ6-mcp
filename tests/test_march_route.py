"""The march: per-tile movement cost, and the turn a zone of control costs.

Two facts the tile-count arithmetic could not see, and the war paid for both after the event:
a tile costs what the map says (Hills 2, Woods 2, Forest-on-Hills 3, a river crossing the rest of
the turn), and entering a tile in an enemy zone of control spends the rest of that turn's movement
(manual:875), light and heavy cavalry excepted (manual:735-737). Before this, `arrive T+n` and
`ASSAULT OPENS on T+n` were computed as `ceil((#path - reach) / reach)`, and 232 `STOPPED_MID_PATH`
results over T228-T299 were reported after the fact rather than predicted.

The Lua half cannot run without a game, so it is covered two ways: the emitted chunks are
syntax-checked with a real Lua parser (skipped when `luaparser` is not installed), and the
predicates they must use are asserted as text - the ZOC flag the game actually has, the cavalry
exemption matched by class equality rather than substring, and the fallback that reports "not
known" instead of inventing a number.
"""

from __future__ import annotations

import pytest

from civ_mcp import lua as lq
from civ_mcp import narrate as nr
from civ_mcp.lua import units as lqu
from civ_mcp import staging as st
from civ_mcp.lua import models as m


def _code_only(lua: str) -> str:
    """A Lua chunk without its `--` comments.

    The comments *name* the wrong predicate on purpose (to explain why it must not be used), so a
    text assertion about what the code does has to read the code. The same trap caught the religion
    predicate: a comment mentioning a class name is not a use of it.
    """
    return "\n".join(line.split("--")[0] for line in lua.splitlines())


# --------------------------------------------------------------- what the game's data says


class TestTheZocFlagIsTheGamesOwn:
    """`GameInfo.Units[type].ZoneOfControl` is the projection flag, and it is not "is combat".

    Measured in the install's own data (`Base/Assets/Gameplay/Data/Units.xml`): all 71 units with
    Combat / RangedCombat / Bombard carry the flag, 47 are `true` (the melee, cavalry and
    anti-cavalry line, plus the Scout) and 24 are `false` - **every** ranged and siege unit,
    Catapult and Bombard included. So a plan may walk past an enemy gun without a stop and must not
    walk past an enemy Spearman, and the query has to read the flag rather than guess from strength.
    """

    def test_the_query_reads_the_flag(self):
        helper = lqu._MARCH_HELPER
        assert "_marchProjectsZoc" in helper
        assert "info.ZoneOfControl" in helper
        assert "GameInfo.Units[eu:GetType()]" in helper
        # A boolean column reaches Lua as `false` or as `0` - both have to read as "projects none",
        # and `true`/`1` as "projects one". Anything else falls back to the promotion class.
        assert "if v == false or v == 0 then return false end" in helper
        assert "if v == true or v == 1 then return true end" in helper
        assert 'pc == "PROMOTION_CLASS_SIEGE"' in helper

    def test_a_ranged_unit_is_not_assumed_to_project_one(self):
        # The predicate must not be "has combat strength": that files an Archer (which the data
        # marks `ZoneOfControl="false"`) as a ZOC projector, and the plan would route around
        # nothing. The flag is read first; the promotion class is only the fallback for a row that
        # does not carry the column at all, and even there it is the "no" side of the answer.
        helper = lqu._MARCH_HELPER
        assert helper.index("info.ZoneOfControl") < helper.index('pc == "PROMOTION_CLASS_RANGED"')
        assert 'if pc == "PROMOTION_CLASS_RANGED" or pc == "PROMOTION_CLASS_SIEGE" then return false end' in helper

    def test_the_scan_only_sees_visible_enemies(self):
        assert "vis:IsVisible(ex, ey)" in lqu._MARCH_HELPER
        # and only enemies: our own units never project a stop onto our own route
        assert "pid ~= me" in lqu._MARCH_HELPER
        assert "dip:IsAtWarWith(pid)" in lqu._MARCH_HELPER


class TestCavalryIgnoresZoc:
    """manual:735-737 - light and heavy cavalry are the exception to the ZOC rule.

    The test is class equality, never a substring: an anti-cavalry unit's PromotionClass contains
    "CAVALRY" too, and `string.find(pc, "CAVALRY")` would hand a Spearman the exemption.
    """

    def test_the_two_cavalry_classes_are_named_exactly(self):
        helper = lqu._MARCH_HELPER
        assert 'pc == "PROMOTION_CLASS_LIGHT_CAVALRY"' in helper
        assert 'pc == "PROMOTION_CLASS_HEAVY_CAVALRY"' in helper

    def test_no_substring_match_anywhere_in_the_helper(self):
        assert "string.find" not in _code_only(lqu._MARCH_HELPER)


# --------------------------------------------------------------------- the walk itself


class TestTheWalkUsesTheEnginesApis:
    def test_it_pays_the_maps_own_tile_cost(self):
        assert "plot:GetMovementCost()" in lqu._MARCH_HELPER

    def test_it_uses_the_units_own_per_turn_budget(self):
        assert "unit:GetMaxMoves()" in lqu._MARCH_HELPER

    def test_turn_zero_is_the_engines_answer_not_a_simulation(self):
        # `GetReachableMovement` already accounts for terrain, rivers and ZOC, so the first turn
        # follows it and only later turns are simulated.
        assert "while idx <= #path and reachSet[path[idx]] do" in lqu._MARCH_HELPER
        assert "local turn, budget = 1, perTurn" in lqu._MARCH_HELPER

    def test_the_enemy_scan_is_done_once_per_query(self):
        assert lqu._MARCH_HELPER.count("local function _marchZoc(me)") == 1
        assert "_MARCH_ZOC_READY" in lqu._MARCH_HELPER


class TestTheQueriesCarryTheWalk:
    def test_the_pathing_query_embeds_the_helper(self):
        query = lq.build_pathing_estimate_query(3211270, 56, 43)
        assert "GetMovementCost" in query and "GetMaxMoves" in query
        assert "_marchWalk(me, unit, path, reachSet)" in query
        assert "__MARCH__" not in query

    def test_the_pathing_query_reports_cost_and_zoc(self):
        query = lq.build_pathing_estimate_query(3211270, 56, 43)
        assert 'print("PATH|" .. turnsNeeded .. "|" .. totalTiles .. "|" .. reachCount' in query
        assert '.. "|" .. walkCost .. "|" .. walkZoc)' in query
        assert 'print("ZOCSTOP|"' in query

    def test_the_pathing_query_keeps_the_old_arithmetic_as_the_fallback(self):
        query = lq.build_pathing_estimate_query(3211270, 56, 43)
        assert "math.ceil((totalTiles - reachCount) / math.max(reachCount, 1))" in query
        assert "walkCost, walkZoc = -1, -1" in query

    def test_the_staging_query_embeds_the_helper(self):
        query = lq.build_staging_plan_query(56, 43)
        assert "GetMovementCost" in query and "GetMaxMoves" in query
        assert "__MARCH__" not in query
        assert query.count("_marchWalk(me, u, path") == 4  # ring, rally, next, kill

    def test_the_staging_query_keeps_the_old_arithmetic_as_the_fallback(self):
        query = lq.build_staging_plan_query(56, 43)
        assert "cost2, zoc2 = -1, -1" in query
        assert "cost3, zoc3 = -1, -1" in query


class TestTheEmittedLuaIsValid:
    """The half no test can exercise without a game: a syntax error would only show mid-war."""

    @pytest.mark.parametrize(
        "query",
        [
            lq.build_pathing_estimate_query(3211270, 56, 43),
            lq.build_staging_plan_query(56, 43),
            lq.build_staging_plan_query(56, 43, next_x=60, next_y=30),
            lq.build_staging_plan_query(56, 43, kill_x=59, kill_y=32),
        ],
    )
    def test_it_parses_as_lua(self, query):
        ast = pytest.importorskip("luaparser.ast", reason="luaparser is the dev-group Lua parser")
        ast.parse(query)  # raises on a syntax error


# -------------------------------------------------------------------------- the parsers


class TestPathingEstimateParsing:
    def test_the_new_fields_are_read(self):
        est = lq.parse_pathing_estimate(
            ["PATH|3|8|2|13|2", "ZOCSTOP|57,41|1", "WAYPOINTS|(55,40);(56,41);(57,41)"]
        )
        assert (est.turns, est.total_tiles, est.reachable_this_turn) == (3, 8, 2)
        assert est.total_cost == 13
        assert est.zoc_stops == 2
        assert est.zoc_at == (57, 41, 1)

    def test_a_clear_route_reads_as_zero_stops(self):
        est = lq.parse_pathing_estimate(["PATH|1|4|2|6|0"])
        assert est.total_cost == 6 and est.zoc_stops == 0
        assert est.zoc_at is None

    def test_an_old_server_reads_as_not_known_not_as_clear(self):
        est = lq.parse_pathing_estimate(["PATH|2|5|2"])
        assert est.turns == 2
        assert est.total_cost == -1
        assert est.zoc_stops == -1
        assert est.zoc_at is None


class TestStagingOptionParsing:
    def test_a_ring_option_carries_its_route(self):
        plan = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|56,43|ring:2",
                "RING|55,41|2|ok|land",
                "UNIT|UNIT_TREBUCHET|3211270|55,40|2|siege",
                "OPTION|3211270|55,41|1|0|6|zoc:1|cost:8|zocat:56,41,1",
            ]
        )
        option = plan.options[0]
        assert option.turns == 1 and option.path_len == 6
        assert option.cost == 8 and option.zoc == 1 and option.zoc_at == (56, 41, 1)

    def test_a_clear_route_carries_its_cost_and_a_zero(self):
        plan = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|56,43|ring:2",
                "RING|55,41|2|ok|land",
                "UNIT|UNIT_TREBUCHET|3211270|55,40|2|siege",
                "OPTION|3211270|55,41|0|1|3|zoc:0|cost:3",
            ]
        )
        assert plan.options[0].cost == 3 and plan.options[0].zoc == 0
        assert plan.options[0].zoc_at is None

    def test_an_old_server_reads_as_not_known(self):
        plan = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|56,43|ring:2",
                "RING|55,41|2|ok|land",
                "UNIT|UNIT_TREBUCHET|3211270|55,40|2|siege",
                "OPTION|3211270|55,41|1|0|6",
            ]
        )
        assert plan.options[0].cost == -1 and plan.options[0].zoc == -1

    def test_the_other_option_shapes_carry_their_route_too(self):
        plan = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|56,43|ring:2",
                "RALLYRING|58,43|3|ok|land",
                "KILLRING|59,32|1",
                "NEXTRING|60,30|2",
                "RALLYOPTION|7|58,43|1|0|5|zoc:1|cost:7|zocat:57,43,1",
                "KILLOPTION|7|59,32|0|1|zoc:0|cost:2",
                "NEXTOPTION|7|60,30|2|0|zoc:1|cost:9|zocat:59,31,2",
            ]
        )
        rally = plan.rally_options[0]
        assert (rally.cost, rally.zoc, rally.zoc_at) == (7, 1, (57, 43, 1))
        kill = plan.kill_options[0]
        assert (kill.cost, kill.zoc, kill.zoc_at) == (2, 0, None)
        nxt = plan.next_options[0]
        assert (nxt.cost, nxt.zoc, nxt.zoc_at) == (9, 1, (59, 31, 2))


# ---------------------------------------------------------------- the plan and its table


def _plan(with_zoc: int, cost: int = 8, zoc_at=(56, 41, 1)) -> m.StagingPlan:
    """One siege unit, two distance-2 ring tiles, one option each - so the tiebreak decides."""
    plan = m.StagingPlan(target="56,43")
    plan.ring = [
        m.StagingRingTile(x=55, y=41, distance=2),
        m.StagingRingTile(x=57, y=42, distance=2),
    ]
    plan.units = [
        m.StagingUnit(
            unit_type="UNIT_TREBUCHET",
            unit_id=3211270,
            x=55,
            y=40,
            moves=2,
            role="siege",
            distance=3,
            strength=35,
            hp=100,
            max_hp=100,
        )
    ]
    plan.options = [
        m.StagingOption(
            unit_id=3211270, x=57, y=42, turns=1, path_len=6, cost=cost + 2, zoc=with_zoc,
            zoc_at=zoc_at,
        ),
        m.StagingOption(unit_id=3211270, x=55, y=41, turns=1, path_len=5, cost=cost, zoc=0),
    ]
    return plan


class TestThePlanPrefersTheRouteThatDoesNotStop:
    def test_a_route_through_a_zoc_loses_the_tie(self):
        # Both tiles arrive on T+1 and are equally good for a siege unit; only one of them spends
        # that turn inside an enemy zone of control.
        result = st.assign(_plan(with_zoc=2))
        assert [(a.tile.x, a.tile.y) for a in result.placed] == [(55, 41)]

    def test_the_route_it_took_is_on_the_row(self):
        result = st.assign(_plan(with_zoc=2))
        assert result.placed[0].zoc == 0
        assert result.placed[0].cost == 8

    def test_an_old_server_does_not_change_the_choice(self):
        # cost/zoc -1 on every option: the tiebreak is uniform and the old plan stands.
        plan = _plan(with_zoc=0)
        for option in plan.options:
            option.cost = -1
            option.zoc = -1
        result = st.assign(plan)
        assert len(result.placed) == 1
        assert result.placed[0].zoc == -1


class TestTheTableSaysWhereTheTurnIsSpent:
    def test_a_zoc_stop_is_named_with_its_tile_and_turn(self):
        plan = _plan(with_zoc=2)
        result = st.assign(plan)
        result.placed[0].zoc = 2
        result.placed[0].zoc_at = (56, 41, 1)
        text = st.render(result, plan)
        assert "ZOC STOP at (56,41) on turn +1" in text
        assert "manual:875" in text
        assert "already counted in the arrival turn above" in text

    def test_the_plan_level_line_counts_the_stopped_routes(self):
        plan = _plan(with_zoc=2)
        result = st.assign(plan)
        result.placed[0].zoc = 2
        result.placed[0].zoc_at = (56, 41, 1)
        text = st.render(result, plan)
        assert "ZONE OF CONTROL on the march: 1 of the routes above" in text
        assert "UNIT_TREBUCHET #3211270 stops at (56,41) on turn +1" in text

    def test_a_clear_route_reports_its_cost_without_noise(self):
        plan = _plan(with_zoc=0)
        result = st.assign(plan)
        chosen = result.placed[0]
        assert chosen.zoc == 0 and chosen.cost > 0
        text = st.render(result, plan)
        assert f"cost {chosen.cost} mp, no visible ZOC on the way" in text
        assert "ZOC STOP" not in text
        assert "ZONE OF CONTROL" not in text

    def test_an_old_server_renders_exactly_as_before(self):
        plan = _plan(with_zoc=0)
        for option in plan.options:
            option.cost = -1
            option.zoc = -1
        result = st.assign(plan)
        text = st.render(result, plan)
        assert "ZOC" not in text
        assert "no visible" not in text and "mp, " not in text


class TestTheNarrationOfAMarch:
    def test_a_zoc_stop_is_named(self):
        est = m.PathingEstimate(
            turns=3, total_tiles=8, reachable_this_turn=2, total_cost=13, zoc_stops=1,
            zoc_at=(57, 41, 1),
        )
        text = nr.narrate_pathing_estimate(est)
        assert "13 movement points of terrain" in text
        assert "ZOC STOP at (57,41) on turn +1" in text
        assert "~3 turns" in text

    def test_a_clear_route_says_so(self):
        est = m.PathingEstimate(
            turns=2, total_tiles=5, reachable_this_turn=2, total_cost=6, zoc_stops=0
        )
        text = nr.narrate_pathing_estimate(est)
        assert "6 movement points of terrain" in text
        assert "no visible enemy ZOC on the route" in text

    def test_an_old_server_narrates_as_before(self):
        est = m.PathingEstimate(turns=2, total_tiles=5, reachable_this_turn=2)
        text = nr.narrate_pathing_estimate(est)
        assert text == "~2 turns (5 tiles total, 2 reachable this turn)"

    def test_reachable_this_turn_still_reads_as_reachable(self):
        est = m.PathingEstimate(
            turns=0, total_tiles=3, reachable_this_turn=3, total_cost=3, zoc_stops=0
        )
        text = nr.narrate_pathing_estimate(est)
        assert text.startswith("Reachable this turn (3 tiles in path")
        assert "no visible enemy ZOC on the route" in text
