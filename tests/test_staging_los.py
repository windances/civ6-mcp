"""Line of sight: the manual's rule on the map's numbers, and what the plan does with it.

`prompts/tactics/04` step 6.2 and `tactics/07` Gate 2 both ask "can this gun actually shoot from
where it is going", and the plan used to answer with the tile's distance - `FIRE from here` for any
distance-2 tile. Distance is not line of sight: at 阿斯特拉罕 only one distance-2 tile had a line,
and 圣彼得堡 opened with one Trebuchet firing while two guns stood at distance 4 and 6. These tests
pin the rule (map data), the engine's override (`CANFIRE`), and the plan's use of both.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import los  # noqa: E402
from civ_mcp import staging as st  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def flat():
    """A distance-2 tile with nothing between it and the target: level 0."""
    return m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 0)])


def woods():
    return m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 1)])


def hills():
    return m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 1)])


def hills_and_woods():
    """Hills with woods on them: the manual's exception - level 2, and a hill cannot see over it."""
    return m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 2)])


def mountain():
    return m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, -1)])


def two_lines(clear_level, blocked_level):
    """A d2 tile with both candidate lines between it and the target on the hex grid."""
    return m.StagingRingTile(
        x=55, y=41, distance=2, between=[(56, 41, clear_level), (56, 42, blocked_level)]
    )


class TestTheRule:
    """The manual's rule (`manual:999`) on the game's own `SightThroughModifier` numbers."""

    def test_flat_ground_between_is_a_clear_shot(self):
        verdict = los.line_of_sight(flat())
        assert verdict.state == los.FIRE and verdict.can_fire

    def test_a_wood_between_blocks_a_unit_on_flat_ground(self):
        verdict = los.line_of_sight(woods())
        assert verdict.state == los.NO
        assert "hills or woods at (56,41)" in verdict.blockers

    def test_a_hill_between_blocks_a_unit_on_flat_ground(self):
        assert los.line_of_sight(hills()).state == los.NO

    def test_a_unit_on_a_hill_sees_over_plain_woods_and_over_a_plain_hill(self):
        for middle in (woods(), hills()):
            middle.hills = True
            assert los.line_of_sight(middle).state == los.FIRE

    def test_woods_on_a_hill_block_even_a_unit_standing_on_a_hill(self):
        """The manual's exception: "unless the blocking terrain contains both Hills and Woods"."""
        tile = hills_and_woods()
        tile.hills = True
        verdict = los.line_of_sight(tile)
        assert verdict.state == los.NO
        assert "hills with woods at (56,41)" in verdict.blockers

    def test_impassable_terrain_blocks_whatever_the_numbers_say(self):
        verdict = los.line_of_sight(mountain())
        assert verdict.state == los.NO
        assert "impassable terrain at (56,41)" in verdict.blockers

    def test_a_unit_on_a_hill_does_not_see_over_a_mountain(self):
        tile = mountain()
        tile.hills = True
        assert los.line_of_sight(tile).state == los.NO

    def test_an_adjacent_tile_needs_no_line_at_all(self):
        """`A unit can always see into a tile` - and d1 has nothing between it and the target."""
        tile = m.StagingRingTile(x=56, y=42, distance=1, hills=True, sight=2)
        verdict = los.line_of_sight(tile)
        assert verdict.state == los.FIRE and verdict.source == "range"

    def test_two_candidate_lines_with_one_clear_is_a_maybe(self):
        verdict = los.line_of_sight(two_lines(0, 2))
        assert verdict.state == los.MAYBE
        assert verdict.blockers and not verdict.ruled_out

    def test_two_blocked_lines_are_a_no(self):
        assert los.line_of_sight(two_lines(2, 2)).state == los.NO

    def test_a_server_that_sends_no_sight_data_is_unread_not_clear(self):
        """An old server's ring row has no `between`, and "not reported" is not "no blocker"."""
        verdict = los.line_of_sight(m.StagingRingTile(x=55, y=41, distance=2))
        assert verdict.state == los.UNKNOWN
        assert verdict.source == "none" and not verdict.can_fire

    def test_no_tile_at_all_is_unread(self):
        assert los.line_of_sight(None).state == los.UNKNOWN


class TestTheEnginesAnswer:
    """`CANFIRE` is a reading, not a prediction, and it overrides the map."""

    def test_the_engine_is_preferred_over_a_clear_map_line(self):
        verdict = los.line_of_sight(flat(), engine=True)
        assert verdict.state == los.FIRE and verdict.source == "engine"

    def test_the_engine_refusing_the_shot_is_no_even_where_the_map_looks_clear(self):
        verdict = los.line_of_sight(flat(), engine=False)
        assert verdict.state == los.NO and verdict.source == "engine"
        assert verdict.ruled_out

    def test_the_engine_overrides_a_map_blocker_it_can_shoot_past(self):
        assert los.line_of_sight(hills_and_woods(), engine=True).state == los.FIRE


def plan(units, options, ring, engine_fire=None):
    return m.StagingPlan(
        target="Moscow", ring=ring, units=units, options=options, engine_fire=engine_fire or {}
    )


def siege(uid=1, x=50, y=50, moves=2):
    return m.StagingUnit(unit_type="UNIT_CATAPULT", unit_id=uid, x=x, y=y, moves=moves, role="siege")


class TestThePlan:
    """What the plan does with a verdict: rank, report, and count only what can fire."""

    def test_a_blocked_tile_ranks_behind_a_clear_one_at_the_same_distance(self):
        units = [siege()]
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 2)], hills=True),
            m.StagingRingTile(x=56, y=41, distance=2, between=[(56, 42, 0)]),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=1, x=56, y=41, turns=0, this_turn=True),
        ]
        result = st.assign(plan(units, options, ring))
        placed = result.placed[0]
        assert (placed.tile.x, placed.tile.y) == (56, 41)
        assert placed.los.state == los.FIRE

    def test_a_clear_adjacent_tile_beats_a_blocked_distance_two_tile(self):
        """Distance is the doctrine; being able to shoot is the point of the doctrine."""
        units = [siege()]
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 2)], hills=True),
            m.StagingRingTile(x=56, y=42, distance=1),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=1, x=56, y=42, turns=0, this_turn=True),
        ]
        result = st.assign(plan(units, options, ring))
        assert result.placed[0].tile.distance == 1

    def test_the_row_says_fire_for_a_clear_tile_and_no_los_for_a_blocked_one(self):
        units = [siege(1), siege(2, x=51, y=51)]
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 0)]),
            m.StagingRingTile(x=56, y=41, distance=2, between=[(56, 42, 2)]),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=2, x=56, y=41, turns=0, this_turn=True),
        ]
        text = st.render(st.assign(plan(units, options, ring)), plan(units, options, ring))
        assert "FIRE from here" in text
        assert "NO LINE OF SIGHT" in text
        assert "hills with woods at (56,42)" in text

    def test_a_gun_that_cannot_fire_does_not_count_as_in_position(self):
        units = [siege()]
        ring = [m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 2)])]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True)]
        result = st.assign(plan(units, options, ring))
        assert result.shooters_in_place == 0

    def test_a_stuck_gun_is_pointed_at_a_tile_the_map_says_it_can_fire_from(self):
        units = [siege()]
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 2)]),
            m.StagingRingTile(x=54, y=41, distance=2, between=[(55, 42, 0)]),
            m.StagingRingTile(x=56, y=42, distance=1),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=1, x=54, y=41, turns=1, path_len=4),
        ]
        built = plan(units, options, ring)
        text = st.render(st.assign(built), built)
        assert "NO LINE OF SIGHT" in text
        assert "(54,41)" in text, "the alternative tile is named"

    def test_the_header_counts_the_tiles_that_actually_have_a_shot(self):
        units = [siege()]
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 0)]),
            m.StagingRingTile(x=56, y=41, distance=2, between=[(56, 42, 2)]),
            m.StagingRingTile(x=56, y=42, distance=1),
        ]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True)]
        built = plan(units, options, ring)
        text = st.render(st.assign(built), built)
        assert "3 firing tile(s), 2 with line of sight" in text

    def test_the_engines_reading_is_used_for_a_gun_already_standing_there(self):
        units = [siege()]
        ring = [m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 0)])]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True)]
        built = plan(units, options, ring, engine_fire={1: False})
        result = st.assign(built)
        assert result.placed[0].los.source == "engine"
        assert result.shooters_in_place == 0
        assert "NO LINE OF SIGHT" in st.render(result, built)

    def test_a_server_without_sight_data_still_plans_and_says_it_cannot_read(self):
        """The old shape must not crash, and must not be read as a clear line either."""
        units = [siege()]
        ring = [m.StagingRingTile(x=55, y=41, distance=2)]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True)]
        result = st.assign(plan(units, options, ring))
        assert result.placed[0].los.state == los.UNKNOWN
        assert result.opens_on == 0, "the old behaviour is kept: it is not ruled out"
        assert "LOS unread" in st.render(result, plan(units, options, ring))


class TestAGunThatHasAlreadyFired:
    """`CANFIRE ... spent`: in the ring with no movement left - the fact the map cannot show.

    `tactics/04`: a unit that spends its move arriving fires next turn. Before this, the plan read a
    spent gun's tile out of the map and called it `FIRE from here`, which is true of the *line* and
    false of the *turn* - so `n shooter(s) in position` over-counted by one every time a gun had
    already moved.
    """

    def _plan(self, **kw):
        units = [siege()]
        ring = [m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 0)])]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True)]
        built = plan(units, options, ring)
        built.engine_spent = kw.get("spent", {1})
        return built

    def test_a_spent_gun_is_not_a_shooter_in_position(self):
        result = st.assign(self._plan())
        assert result.placed[0].spent
        assert result.shooters_in_place == 0
        assert result.opens_on == 1, "it fires next turn, so the assault opens a turn later"

    def test_the_row_says_no_shot_this_turn_rather_than_fire(self):
        built = self._plan()
        text = st.render(st.assign(built), built)
        assert "NO SHOT THIS TURN" in text and "no movement left" in text
        assert "FIRE from here" not in text
        assert "SPENT THIS TURN" in text

    def test_a_gun_with_movement_left_is_unaffected(self):
        built = self._plan(spent=set())
        result = st.assign(built)
        assert not result.placed[0].spent
        assert result.shooters_in_place == 1 and result.opens_on == 0
        assert "NO SHOT THIS TURN" not in st.render(result, built)

    def test_the_parser_records_spent_apart_from_the_line_of_sight_verdict(self):
        from civ_mcp import lua as lq

        parsed = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|58,42|ring:2|camp:0",
                "RING|55,41|2|ok|land|hill:0|sight:0|via:56,41,0",
                "CANFIRE|7|0|spent",
                "CANFIRE|9|1|ok",
            ]
        )
        assert parsed.engine_spent == {7}
        assert parsed.engine_fire == {7: False, 9: True}


class TestTheQuery:
    """The facts come from the game, and the engine's own answer is asked for where it exists."""

    def test_the_ring_row_carries_the_sight_facts(self):
        from civ_mcp import lua as lq

        q = lq.build_staging_plan_query(60, 29)
        assert '|hill:" .. t.hills .. "|sight:" .. t.sight' in q
        assert "tinfo.SightThroughModifier" in q and "finfo.SightThroughModifier" in q
        assert "tinfo.Hills" in q

    def test_the_tiles_between_a_distance_two_pair_come_from_the_games_own_distance(self):
        from civ_mcp import lua as lq

        q = lq.build_staging_plan_query(60, 29)
        assert 'via = "|via:"' in q
        assert "n.d == 1 and Map.GetPlotDistance(t.x, t.y, n.x, n.y) == 1" in q
        # An impassable tile between blocks everything: the manual calls those impenetrable.
        assert "(n.passable and n.sight or -1)" in q

    def test_the_engine_is_asked_for_every_gun_in_range_and_a_spent_one_says_so(self):
        from civ_mcp import lua as lq

        q = lq.build_staging_plan_query(60, 29)
        assert 'print("CANFIRE|"' in q
        assert "if (rs > 0 or bomb > 0) and Map.GetPlotDistance(ux, uy, tx, ty) <=" in q
        # A gun with no movement left is *reported*, not skipped: it is in the ring and cannot
        # shoot this turn, and that is a fact the map cannot show (`tactics/04`: arriving costs the
        # shot). The engine is asked only where the answer is a line-of-sight verdict.
        assert 'print("CANFIRE|" .. u:GetID() .. "|0|spent")' in q
        assert 'if moves <= 0 then' in q
        assert '.. (canF and 1 or 0) .. "|ok")' in q

    def test_the_parser_reads_the_sight_facts_and_the_engines_answer(self):
        from civ_mcp import lua as lq

        plan = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|58,42|ring:3|camp:0",
                "RING|55,41|2|ok|land|hill:0|sight:0|via:56,41,2;56,42,0",
                "RING|56,42|1|ok|land|hill:1|sight:1",
                "CANFIRE|7|1",
                "CANFIRE|9|0",
            ]
        )
        far = plan.ring[0]
        assert far.between == [(56, 41, 2), (56, 42, 0)]
        assert far.hills is False and far.sight == 0
        assert plan.ring[1].hills is True and plan.ring[1].sight == 1
        assert plan.ring[1].between == []
        assert plan.engine_fire == {7: True, 9: False}

    def test_an_old_server_parses_with_no_sight_facts(self):
        from civ_mcp import lua as lq

        plan = lq.parse_staging_plan_response(["RING|55,41|2|ok|land"])
        assert plan.ring[0].between == [] and plan.ring[0].hills is False
        assert plan.engine_fire == {}
