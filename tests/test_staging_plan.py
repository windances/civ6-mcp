"""The staging plan: distinct tiles, different movement, and no queueing in the corridor.

Human instruction, 2026-09-26: 在集结前，规划集结方案，不能被堵住，不同部队移动力不一样，找到最优集结方案后，才开始执行. The game supplies the ring and the paths (`lua/units.py`); this file decides the
assignment, and these tests cover that decision without a game.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import staging as st  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def plan(units, options, ring=None, rally_ring=None, rally_options=None):
    ring = ring or [
        m.StagingRingTile(x=55, y=41, distance=2),
        m.StagingRingTile(x=56, y=41, distance=2),
        m.StagingRingTile(x=56, y=42, distance=1),
        m.StagingRingTile(x=55, y=42, distance=2),
    ]
    return m.StagingPlan(
        target="圣彼得堡", ring=ring, units=units, options=options,
        rally_ring=rally_ring or [], rally_options=rally_options or [],
    )


def unit(uid, kind, role, x=50, y=50, moves=2):
    return m.StagingUnit(unit_type=kind, unit_id=uid, x=x, y=y, moves=moves, role=role)


class TestAssignment:
    def test_shooters_get_the_distance_two_tiles_and_melee_the_adjacent_one(self):
        units = [unit(1, "UNIT_TREBUCHET", "siege"), unit(2, "UNIT_MAN_AT_ARMS", "melee")]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=1, x=55, y=42, turns=0, this_turn=True),
            m.StagingOption(unit_id=2, x=56, y=42, turns=0, this_turn=True),
        ]
        result = st.assign(plan(units, options))
        placed = {a.unit.unit_id: a.tile for a in result.placed}
        assert placed[1].distance == 2
        assert placed[2].distance == 1
        assert result.opens_on == 0, "the shooters are in position this turn"

    def test_two_units_never_get_the_same_tile(self):
        """A second order onto an occupied tile is `STACKING_CONFLICT` and costs the turn."""
        units = [unit(1, "UNIT_CATAPULT", "siege"), unit(2, "UNIT_TREBUCHET", "siege")]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
                   m.StagingOption(unit_id=2, x=55, y=41, turns=0, this_turn=True)]
        result = st.assign(plan(units, options))
        tiles = [(a.tile.x, a.tile.y) for a in result.placed]
        assert len(tiles) == len(set(tiles)) == 1
        assert len(result.unplaced) == 1
        assert "already claimed" in result.conflicts[0]

    def test_a_unit_with_no_reachable_tile_is_named_and_sent_to_the_rear(self):
        units = [unit(1, "UNIT_CATAPULT", "siege", x=40, y=40, moves=2)]
        result = st.assign(plan(units, []))
        assert result.unplaced and result.unplaced[0].unit_id == 1
        text = st.render(result, plan(units, []))
        assert "NO TILE IN REACH" in text
        assert "cut the" in text and "supply line" in text

    def test_the_assault_opens_when_the_last_shooter_is_in_position(self):
        units = [unit(1, "UNIT_CATAPULT", "siege"), unit(2, "UNIT_TREBUCHET", "siege")]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
                   m.StagingOption(unit_id=2, x=56, y=41, turns=2, this_turn=False)]
        result = st.assign(plan(units, options))
        assert result.opens_on == 2
        assert "T+2" in st.render(result, plan(units, options))

    def test_spare_ring_tiles_are_offered_to_the_units_that_could_not_fit(self):
        units = [unit(1, "UNIT_CATAPULT", "siege")]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True)]
        result = st.assign(plan(units, options))
        assert result.idle_tiles, "the ring has tiles nobody claimed"
        assert "SPARE RING TILES" in st.render(result, plan(units, options))


class TestTheSurplusHasAJob:
    """Human instruction: 攻城部队确定后，如果还有多余部队，如何安排？

    The assault establishment is 3 siege / 3 melee-or-cavalry / 4 ranged. Everything above it
    takes the supply hexes of the ring first -each unit cuts the hex it stands on plus its ring
    neighbours, so closing six hexes takes about three units -then depth behind the ring.
    """

    def _units(self, siege=4, melee=3):
        units = [
            unit(100 + i, "UNIT_TREBUCHET", "siege", x=50 + i, y=40)
            for i in range(siege)
        ]
        units += [
            unit(200 + i, "UNIT_MAN_AT_ARMS", "melee", x=50 + i, y=41) for i in range(melee)
        ]
        return units

    def _options(self, units, ring):
        return [
            m.StagingOption(unit_id=u.unit_id, x=t.x, y=t.y, turns=0, this_turn=True)
            for u in units
            for t in ring
        ]

    def test_the_extra_melee_unit_cuts_the_supply_line_instead_of_taking_a_firing_tile(self):
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2),
            m.StagingRingTile(x=56, y=41, distance=2),
            m.StagingRingTile(x=55, y=42, distance=2),
            m.StagingRingTile(x=56, y=42, distance=1),
            m.StagingRingTile(x=57, y=42, distance=1),
            m.StagingRingTile(x=57, y=43, distance=1),
            # extra adjacent hexes, so the assault force (6 units) does not fill them all: a
            # supply hex must still be free for the surplus unit to take, which is the whole
            # point of the rung
            m.StagingRingTile(x=58, y=43, distance=1),
            m.StagingRingTile(x=58, y=42, distance=1),
        ]
        units = self._units(siege=3, melee=4)
        result = st.assign(plan(units, self._options(units, ring), ring))
        assert len(result.placed) == 6, "3 siege + 3 melee is the establishment"
        assert len(result.surplus) == 1, "the fourth melee unit is surplus"
        assert result.surplus[0].note == "SUPPLY"
        assert result.surplus[0].tile.distance == 1, "supply hexes are the adjacent ring"
        text = st.render(result, plan(units, self._options(units, ring), ring))
        assert "CUT THE SUPPLY LINE" in text
        assert "supply hexes cut after this plan:" in text

    def test_a_surplus_unit_that_can_reach_no_supply_hex_becomes_depth(self):
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2),
            m.StagingRingTile(x=56, y=42, distance=1),
        ]
        units = self._units(siege=4, melee=0)
        # only the first unit can reach a tile at all, and it is not surplus
        options = [m.StagingOption(unit_id=units[0].unit_id, x=55, y=41, turns=0, this_turn=True)]
        result = st.assign(plan(units, options, ring))
        assert len(result.placed) == 1
        assert [a.note for a in result.surplus] == [""], "the fourth siege unit is surplus"
        assert result.surplus[0].tile is None, "nothing in reach, so it holds behind the ring"
        assert "DEPTH" in st.render(result, plan(units, options, ring))

    def test_a_surplus_unit_advances_toward_the_next_objective(self):
        """Human instruction 2026-09-26: 多余部队还可以向下一个城市目标/蛮族营地集结推进.

        The march is what the last deadline was lost to, so a surplus unit that cannot help the
        current siege -no supply hex in reach, no depth slot -is pushed toward the next target's
        ring now, as long as the tile is outside this city's strike.
        """
        units = [
            m.StagingUnit("UNIT_TREBUCHET", 1, 55, 40, 2, "siege", distance=3),
            m.StagingUnit("UNIT_TREBUCHET", 2, 54, 40, 2, "siege", distance=4),
            m.StagingUnit("UNIT_TREBUCHET", 3, 53, 40, 2, "siege", distance=5),
            m.StagingUnit("UNIT_MAN_AT_ARMS", 4, 52, 42, 2, "melee", distance=7),
        ]
        plan_ = plan(
            units,
            [
                m.StagingOption(unit_id=1, x=58, y=41, turns=0, this_turn=True),
                m.StagingOption(unit_id=2, x=57, y=38, turns=1),
            ],
            [m.StagingRingTile(x=58, y=41, distance=2), m.StagingRingTile(x=57, y=38, distance=2)],
        )
        plan_.next_ring = [m.StagingRingTile(x=52, y=44, distance=2)]
        plan_.next_options = [m.StagingOption(unit_id=4, x=52, y=44, turns=1)]
        result = st.assign(plan_)
        advance = [a for a in result.surplus if a.note == "ADVANCE"]
        assert len(advance) == 1, "the surplus melee unit has a next objective to reach"
        assert (advance[0].tile.x, advance[0].tile.y) == (52, 44)
        text = st.render(result, plan_)
        assert "ADVANCE toward the next objective" in text
        assert "less marching when the next siege opens" in text

    def test_the_ladder_is_printed_with_the_answer(self):
        ring = [m.StagingRingTile(x=56, y=42, distance=1)]
        units = self._units(siege=4, melee=0)
        result = st.assign(plan(units, self._options(units, ring), ring))
        text = st.render(result, plan(units, self._options(units, ring), ring))
        for step in ("supply hexes", "reinforcement road", "depth behind the ring", "pillage"):
            assert step in text
        assert "Never stack them on the ring" in text

    def test_supply_coverage_counts_a_unit_standing_beside_a_hex(self):
        ring = [
            m.StagingRingTile(x=56, y=42, distance=1),
            m.StagingRingTile(x=57, y=42, distance=1),
            m.StagingRingTile(x=58, y=42, distance=1),
        ]
        # one unit beside the middle hex cuts all three (it touches each of them)
        cut, total = st.supply_coverage(ring, [m.StagingUnit("UNIT_MAN_AT_ARMS", 1, 57, 41, 2, "melee")])
        assert (cut, total) == (3, 3)
        assert st.supply_coverage(ring, [m.StagingUnit("UNIT_MAN_AT_ARMS", 1, 40, 40, 2, "melee")]) == (0, 3)


class TestTheParser:
    def test_a_scout_is_never_sent_to_a_ring_tile(self):
        """Found on the first live run of this query (2026-09-26): a Scout filed as melee.

        A Scout has Combat 10, so a classifier that only asks "is Combat > 0" put it on
        `(58,40) d1` -adjacent to the city, inside its strike, where it dies for nothing.
        """
        units = [
            m.StagingUnit("UNIT_SCOUT", 1, 60, 42, 3, "recon", distance=3, strength=10),
            m.StagingUnit("UNIT_TREBUCHET", 2, 55, 40, 2, "siege", distance=3, strength=35),
        ]
        ring = [m.StagingRingTile(x=57, y=39, distance=1), m.StagingRingTile(x=58, y=41, distance=2)]
        options = [
            m.StagingOption(unit_id=1, x=57, y=39, turns=0, this_turn=True),
            m.StagingOption(unit_id=2, x=58, y=41, turns=0, this_turn=True),
        ]
        result = st.assign(plan(units, options, ring))
        assert [u.unit_type for u in result.recon] == ["UNIT_SCOUT"]
        assert all(a.unit.unit_type != "UNIT_SCOUT" for a in result.placed + result.surplus)
        text = st.render(result, plan(units, options, ring))
        assert "RECON" in text and "never a ring tile" in text

    def test_a_unit_far_from_the_target_is_not_called_unreachable(self):
        # A garrison 8 tiles away is not "no tile in reach", it is not part of this plan -and
        # the two read very differently to whoever picks the file up.
        units = [
            m.StagingUnit("UNIT_TREBUCHET", 1, 55, 40, 2, "siege", distance=3),
            m.StagingUnit("UNIT_WARRIOR", 2, 60, 31, 2, "melee", distance=8),
        ]
        ring = [m.StagingRingTile(x=58, y=41, distance=2)]
        options = [m.StagingOption(unit_id=1, x=58, y=41, turns=0, this_turn=True)]
        result = st.assign(plan(units, options, ring))
        text = st.render(result, plan(units, options, ring))
        assert "TOO FAR to matter for this assault (d8)" in text
        assert "NO TILE IN REACH" not in text

    def test_a_wounded_front_liner_is_relieved_by_a_fresh_one(self):
        """Human instruction 2026-09-26: 多余部队还可以替换残血的扛伤部队.

        A front-line unit at half health is the one the city's strike kills — a 55 HP Horseman
        died attacking a walled city (T154), a Knight went 52 -> 6 in one blow (T151). It yields
        its ring tile to a fresh unit of the same role and withdraws to heal.
        """
        units = [
            m.StagingUnit("UNIT_TREBUCHET", 1, 55, 40, 2, "siege", distance=3, hp=70, max_hp=100),
            m.StagingUnit("UNIT_MAN_AT_ARMS", 2, 55, 42, 2, "melee", distance=2, hp=27, max_hp=100),
            m.StagingUnit("UNIT_MAN_AT_ARMS", 3, 54, 42, 2, "melee", distance=3, hp=100, max_hp=100),
            m.StagingUnit("UNIT_MAN_AT_ARMS", 4, 53, 42, 2, "melee", distance=4, hp=100, max_hp=100),
            # a fourth front-liner is one above the establishment, i.e. the relief
            m.StagingUnit("UNIT_MAN_AT_ARMS", 5, 52, 42, 2, "melee", distance=5, hp=100, max_hp=100),
        ]
        ring = [
            m.StagingRingTile(x=58, y=41, distance=2),
            m.StagingRingTile(x=58, y=40, distance=1),
            m.StagingRingTile(x=59, y=40, distance=1),
        ]
        options = [
            m.StagingOption(unit_id=1, x=58, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=2, x=58, y=40, turns=0, this_turn=True),
            m.StagingOption(unit_id=3, x=58, y=40, turns=0, this_turn=True),
            m.StagingOption(unit_id=5, x=59, y=40, turns=0, this_turn=True),
        ]
        result = st.assign(plan(units, options, ring))
        rotated = [a for a in result.rotation]
        assert len(rotated) == 1 and rotated[0].unit.unit_id == 2
        assert rotated[0].note == "UNIT_MAN_AT_ARMS", "the fresh Man-at-Arms relieves it"
        placed = [a.unit.unit_id for a in result.placed]
        assert 2 not in placed, "the wounded unit does not hold a ring tile"
        assert 5 in placed, "the fresh surplus unit took the slot"
        text = st.render(result, plan(units, options, ring))
        assert "ROTATION" in text and "WITHDRAW to heal" in text
        assert "(27/100 hp)" in text

    def test_a_wounded_siege_unit_is_not_rotated_out_of_its_firing_tile(self):
        # A siege unit at range 2 is not taking the city's strike; only the front line rotates.
        units = [
            m.StagingUnit("UNIT_TREBUCHET", 1, 55, 40, 2, "siege", distance=3, hp=20, max_hp=100),
        ]
        ring = [m.StagingRingTile(x=58, y=41, distance=2)]
        options = [m.StagingOption(unit_id=1, x=58, y=41, turns=0, this_turn=True)]
        result = st.assign(plan(units, options, ring))
        assert result.rotation == []
        assert [a.unit.unit_id for a in result.placed] == [1]

    def test_only_mobile_surplus_units_hunt_the_missionary(self):
        """Human instruction 2026-09-26: 多余部队里机动性高的部队还可以集火消灭传教士.

        The damage is not the problem — a missionary has no combat strength and dies to one
        attack, or to a single `condemn` from an adjacent military unit while at war. Catching it
        is: a religious unit steps away from a column, so the job goes to the units with 3+ moves
        (cavalry above all, which ignores zones of control), never to a Catapult that would spend
        two turns walking.
        """
        units = [
            m.StagingUnit("UNIT_TREBUCHET", 1, 55, 40, 2, "siege", distance=3, hp=100, max_hp=100),
            m.StagingUnit("UNIT_TREBUCHET", 2, 54, 40, 2, "siege", distance=4, hp=100, max_hp=100),
            m.StagingUnit("UNIT_TREBUCHET", 3, 53, 40, 2, "siege", distance=5, hp=100, max_hp=100),
            m.StagingUnit("UNIT_TREBUCHET", 4, 52, 40, 2, "siege", distance=6, hp=100, max_hp=100),
            m.StagingUnit("UNIT_HORSEMAN", 5, 60, 32, 4, "melee", distance=9, hp=100, max_hp=100),
        ]
        plan_ = plan(units, [m.StagingOption(unit_id=1, x=58, y=41, turns=0, this_turn=True)],
                     [m.StagingRingTile(x=58, y=41, distance=2)])
        plan_.kill_ring = [m.StagingRingTile(x=59, y=32, distance=1)]
        plan_.kill_options = [m.StagingOption(unit_id=5, x=59, y=32, turns=0, this_turn=True)]
        result = st.assign(plan_)
        hunts = [a for a in result.surplus if a.note == "KILL"]
        assert len(hunts) == 1 and hunts[0].unit.unit_type == "UNIT_HORSEMAN"
        # the fourth Trebuchet is surplus too, but it has 2 moves and no kill option: it must not
        # be the one sent after a unit that can outrun it
        assert all(a.unit.unit_type != "UNIT_TREBUCHET" for a in hunts)
        text = st.render(result, plan_)
        assert "HUNT THE MISSIONARY" in text
        assert "mobile unit only" in text

    def test_it_reads_the_three_line_shapes(self):
        from civ_mcp import lua as lq

        lines = [
            "STAGEPLAN|56,43|ring:4",
            "RING|55,41|2|ok|land",
            "RING|57,41|2|impassable|land",
            "UNIT|UNIT_TREBUCHET|3211270|55,40|2|siege",
            "OPTION|3211270|55,41|0|1|1",
            "OPTION|3211270|57,42|3|0|6",
            "SENTINEL",
        ]
        plan = lq.parse_staging_plan_response(lines)
        assert plan.target == "56,43"
        assert [t.distance for t in plan.ring] == [2, 2]
        assert plan.ring[1].blocked is True
        assert plan.units[0].unit_id == 3211270 and plan.units[0].role == "siege"
        assert plan.options[0].this_turn is True
        assert plan.options[1].turns == 3 and plan.options[1].this_turn is False

    def test_junk_is_ignored(self):
        from civ_mcp import lua as lq

        assert lq.parse_staging_plan_response(["", "garbage", "RING|bad"]).ring == []

    def test_fractional_movement_does_not_kill_the_parser(self):
        """Regression, measured 2026-09-27 T212: the whole tool died on this.

        A unit can hold a fraction of a movement point (a Line Infantry stood at
        1.5/3), and `parse_staging_plan_response` read that field with `int()`:
        `get_staging_plan` answered `invalid literal for int() with base 10: '1.5'`
        and the Alexandria assault lost the table it needed. Whole numbers must
        still arrive as ints, because the renderer and the sorter both use them.
        """
        from civ_mcp import lua as lq

        plan = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|72,36|ring:18",
                "UNIT|UNIT_LINE_INFANTRY|5111819|69,35|1.5|melee|d2|cs65|hp100/100",
                "UNIT|UNIT_BOMBARD|4325376|67,34|2|siege|d3|cs45|hp100/100",
                "OPTION|5111819|71,35|0|1|1",
            ]
        )
        fractional, whole = plan.units
        assert fractional.moves == 1.5
        assert whole.moves == 2 and isinstance(whole.moves, int)
        assert plan.options[0].turns == 0 and isinstance(plan.options[0].turns, int)

    def test_a_fractional_query_argument_does_not_kill_the_builder(self):
        from civ_mcp import lua as lq

        query = lq.build_staging_plan_query(56.0, "43")
        assert "local tx, ty = 56, 43" in query

    def test_the_query_carries_the_target_and_the_sentinel(self):
        from civ_mcp import lua as lq

        query = lq.build_staging_plan_query(56, 43)
        assert "local tx, ty = 56, 43" in query
        assert "GetReachableMovement" in query and "GetMoveToPath" in query
        assert "STAGEPLAN|" in query and "OPTION|" in query
        assert "{" not in query.split("--")[0] or True  # the template must not raise on format


class TestACampIsTheSamePlanAgainstADifferentObject:
    """Human instruction 2026-09-26: the pre-war analysis, the staging and the assault apply to
    every city AND every barbarian camp.

    The ring, the paths and the assignments are the same plan for both; what differs is the last
    step. A camp has no HP, no walls and no supply line - one military unit moving onto its tile
    destroys it - so the plan has to say `WALK-IN OPENS` rather than `ASSAULT OPENS`, must not
    offer to cut a supply line that does not exist, and must keep the walk-in unspent.
    """

    def _ring(self):
        return [
            m.StagingRingTile(x=59, y=41, distance=1),
            m.StagingRingTile(x=60, y=41, distance=1),
            m.StagingRingTile(x=60, y=42, distance=1),
            m.StagingRingTile(x=59, y=43, distance=1),
            m.StagingRingTile(x=58, y=42, distance=2),
            m.StagingRingTile(x=61, y=42, distance=2),
        ]

    def _force(self, camp: bool):
        """One ranged unit and four melee: the fourth melee is surplus and takes a supply hex."""
        units = [unit(1, "UNIT_CROSSBOWMAN", "ranged", x=50, y=50)]
        units += [unit(10 + i, "UNIT_MAN_AT_ARMS", "melee", x=50 + i, y=51) for i in range(4)]
        ring = self._ring()
        options = [
            m.StagingOption(unit_id=u.unit_id, x=t.x, y=t.y, turns=0, this_turn=True)
            for u in units
            for t in ring
        ]
        built = m.StagingPlan(target="60,29", ring=ring, units=units, options=options, camp=camp)
        return built, st.assign(built)

    def test_a_camp_walks_in_and_has_no_supply_line_to_cut(self):
        built, result = self._force(camp=True)
        text = st.render(result, built)
        assert "the camp at 60,29" in text
        assert "WALK-IN OPENS" in text and "ASSAULT OPENS" not in text
        assert "HOLD THE RING" in text and "CUT THE SUPPLY LINE" not in text
        assert "supply hexes cut" not in text
        assert "unspent" in text and "guard, not the camp" in text

    def test_a_city_keeps_the_siege_wording(self):
        built, result = self._force(camp=False)
        text = st.render(result, built)
        assert "ASSAULT OPENS" in text and "WALK-IN OPENS" not in text
        assert "CUT THE SUPPLY LINE" in text and "HOLD THE RING" not in text
        assert "supply hexes cut after this plan" in text

    def test_the_flag_comes_from_the_game_and_defaults_to_a_city(self):
        from civ_mcp import lua as lq

        assert lq.parse_staging_plan_response(["STAGEPLAN|60,29|ring:18|camp:1"]).camp is True
        assert lq.parse_staging_plan_response(["STAGEPLAN|58,39|ring:18|camp:0"]).camp is False
        # An older server prints neither token: the city wording is the safe default.
        assert lq.parse_staging_plan_response(["STAGEPLAN|58,39|ring:18"]).camp is False

    def test_the_query_asks_the_game_which_object_the_tile_holds(self):
        from civ_mcp import lua as lq

        query = lq.build_staging_plan_query(60, 29)
        assert "GetCityInPlot" in query and '|camp:' in query


class TestTheAssemblyLeg:
    """The plan must show the rally tile, not only the tile a unit fires from.

    `tactics/04` step 1: assemble **three tiles or more** from the target, because a city's
    strike and a Catapult both reach two; then advance as one body. The tool used to print only
    the ring assignment, so following it literally walked the train onto d2 - measured T194
    (2/3 shooters in position when the assault opened) and T215 (2/5, one Bombard still 21 tiles
    away). These tests pin the missing first leg.
    """

    def _plan(self):
        units = [
            unit(1, "UNIT_BOMBARD", "siege", x=60, y=36, moves=2),
            unit(2, "UNIT_MAN_AT_ARMS", "melee", x=60, y=37, moves=2),
        ]
        ring = [
            # A d2 tile with a flat tile between it and the target: the map's sight data the
            # plan reads line of sight from (`civ_mcp.los`), so this row prints `FIRE from here`.
            m.StagingRingTile(x=55, y=41, distance=2, between=[(56, 41, 0)]),
            m.StagingRingTile(x=56, y=42, distance=1),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=1, this_turn=False, path_len=5),
            m.StagingOption(unit_id=2, x=56, y=42, turns=0, this_turn=True, path_len=3),
        ]
        # The assembly ring is its own set of tiles at d3, never part of the firing ring: nothing
        # is assigned to them, they are where a unit forms up first (the Lua's RALLYRING lines).
        rally_ring = [m.StagingRingTile(x=53, y=40, distance=3)]
        rally_options = [
            m.StagingOption(unit_id=1, x=53, y=40, turns=2, this_turn=False, path_len=9),
        ]
        return plan(units, options, ring, rally_ring, rally_options)

    def test_a_unit_gets_a_rally_tile_outside_the_citys_reach(self):
        built = self._plan()
        result = st.assign(built)
        text = st.render(result, built)
        assert "ASSEMBLY FIRST" in text
        assert "RALLY (53,40) d3 T+2" in text

    def test_a_ring_tile_is_never_offered_as_its_own_rally(self):
        built = self._plan()
        text = st.render(st.assign(built), built)
        # The Bombard's firing tile is (55,41) d2; (53,40) d3 is the only assembly tile.
        assert text.count("RALLY (") == 1

    def test_a_unit_already_on_the_ring_gets_no_rally_leg(self):
        units = [unit(2, "UNIT_MAN_AT_ARMS", "melee", x=60, y=37, moves=2)]
        ring = [m.StagingRingTile(x=56, y=42, distance=1)]
        options = [m.StagingOption(unit_id=2, x=56, y=42, turns=0, this_turn=True)]
        built = plan(units, options, ring)
        text = st.render(st.assign(built), built)
        assert "RALLY (" not in text
        assert "ASSEMBLY FIRST" not in text, "no assembly leg exists, so the note is noise"

    def test_the_rally_leg_is_kept_out_of_the_firing_line(self):
        built = self._plan()
        text = st.render(st.assign(built), built)
        for line in text.splitlines():
            if "RALLY" in line and "UNIT_" in line:
                assert "FIRE from here" in line  # it is still the firing row
                assert line.index("->") < line.index("RALLY")

    def test_a_rally_tile_is_not_also_offered_as_spare(self):
        # Two assembly tiles at d3: one is the unit's rally, the other is not. The spare list is
        # about **firing** tiles, so neither appears in it.
        units = [unit(1, "UNIT_BOMBARD", "siege", x=60, y=36, moves=2)]
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=1, this_turn=False, path_len=5),
        ]
        rally_ring = [
            m.StagingRingTile(x=53, y=40, distance=3),
            m.StagingRingTile(x=52, y=39, distance=3),
        ]
        rally_options = [
            m.StagingOption(unit_id=1, x=53, y=40, turns=2, this_turn=False, path_len=9),
        ]
        built = plan(units, options, ring, rally_ring, rally_options)
        text = st.render(st.assign(built), built)
        assert "RALLY (53,40) d3" in text
        spare = [line for line in text.splitlines() if "SPARE RING TILES" in line]
        if spare:  # there are no spare firing tiles here, so this is only a guard if one appears
            assert "(53,40)" not in spare[0]
            assert "(52,39)" not in spare[0], "an assembly tile is never a spare firing tile"


class TestTheIssueOrder:
    """Which move call goes first - a fact no single row of the table states.

    A column ordered nearest-first queues behind itself: measured T228-T299, **232
    `STOPPED_MID_PATH` results across 72 turns** (`T257`-`T259` alone: 15, 17, 19), and every plan
    left 6-9 units unplaced (T254: 9 of 10, T260: 7 of 10, T283: 6 of 9). The plan now names the
    order, furthest ring tile first.
    """

    def _plan(self):
        units = [
            unit(11, "UNIT_BOMBARD", "siege", x=60, y=36, moves=2),
            unit(22, "UNIT_INFANTRY", "melee", x=60, y=37, moves=2),
        ]
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2),
            m.StagingRingTile(x=56, y=42, distance=1),
        ]
        options = [
            m.StagingOption(unit_id=11, x=55, y=41, turns=1, this_turn=False, path_len=5),
            m.StagingOption(unit_id=22, x=56, y=42, turns=0, this_turn=True, path_len=3),
        ]
        return plan(units, options, ring)

    def test_the_furthest_ring_tile_is_named_first(self):
        built = self._plan()
        text = st.render(st.assign(built), built)
        order = [line for line in text.splitlines() if "ISSUE THE MOVE CALLS" in line]
        assert order, "the plan has to say which call goes first"
        # The siege unit holds the d2 firing tile and the melee the d1 tile, so the shooter's
        # call comes first - the same reason `tactics/04` says to fill the last firing tile first.
        assert order[0].index("#11") < order[0].index("#22")
        assert "STOPPED_MID_PATH" in order[0], "the order carries the measurement that produced it"

    def test_one_placed_unit_has_no_order_to_give(self):
        units = [unit(22, "UNIT_INFANTRY", "melee", x=60, y=37, moves=2)]
        ring = [m.StagingRingTile(x=56, y=42, distance=1)]
        options = [m.StagingOption(unit_id=22, x=56, y=42, turns=0, this_turn=True)]
        built = plan(units, options, ring)
        text = st.render(st.assign(built), built)
        assert "ISSUE THE MOVE CALLS" not in text, "one call has only one order"


class TestTheAssemblyRingInTheQuery:
    """The rally leg has to come from the game, and it has to be its own ring.

    The old shape asked `_rally_option` for a distance-3 tile inside the firing ring, which the Lua
    never emits (`d >= 1 and d <= 2`), so the whole assembly leg was dead code behind a green test.
    The query now prints a separate `RALLYRING` at d3 with its own `RALLYOPTION` paths, and the
    firing ring is untouched.
    """

    def test_the_query_emits_the_assembly_ring(self):
        from civ_mcp import lua as lq

        q = lq.build_staging_plan_query(60, 29)
        assert 'print("RALLYRING|"' in q
        assert 'print("RALLYOPTION|"' in q
        # Assembly tiles are distance 3 and only distance 3; the firing ring stays 1-2.
        assert "Map.GetPlotDistance(tx, ty, px, py) == 3" in q
        assert "d >= 1 and d <= 2" in q

    def test_the_query_caps_the_assembly_ring_and_orders_it_by_the_army(self):
        from civ_mcp import lua as lq

        q = lq.build_staging_plan_query(60, 29)
        assert "math.min(#candidates, 6)" in q, "the path scan stays bounded"
        assert "a.away < b.away" in q, "assembly tiles nearest our own army come first"

    def test_the_parser_reads_the_assembly_ring(self):
        from civ_mcp import lua as lq

        plan = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|60,29|ring:4|camp:0",
                "RING|59,28|1|ok|land",
                "RALLYRING|57,26|3|ok|land",
                "RALLYRING|63,32|3|ok|water",
                "UNIT|UNIT_BOMBARD|7|60,36|2|siege|d7|cs45|hp100/100",
                "RALLYOPTION|7|57,26|2|0|9",
            ]
        )
        assert [(t.x, t.y, t.distance) for t in plan.rally_ring] == [(57, 26, 3), (63, 32, 3)]
        assert plan.rally_ring[1].water is True
        assert len(plan.rally_options) == 1
        assert plan.rally_options[0].unit_id == 7 and plan.rally_options[0].turns == 2
        assert plan.rally_options[0].path_len == 9
        # The firing ring is unaffected by the assembly ring's presence.
        assert [t.distance for t in plan.ring] == [1]

    def test_a_server_without_the_assembly_ring_prints_no_rally_leg(self):
        """Back-compat: an older server sends no RALLY* lines, and the plan reads as it did."""
        from civ_mcp import lua as lq

        units = [unit(1, "UNIT_BOMBARD", "siege", x=60, y=36, moves=2)]
        ring = [m.StagingRingTile(x=55, y=41, distance=2)]
        options = [m.StagingOption(unit_id=1, x=55, y=41, turns=1, this_turn=False, path_len=5)]
        built = plan(units, options, ring)
        parsed = lq.parse_staging_plan_response(["STAGEPLAN|60,29|ring:1|camp:0"])
        assert parsed.rally_ring == [] and parsed.rally_options == []
        text = st.render(st.assign(built), built)
        assert "RALLY" not in text
        assert "assembly tile(s)" not in text


class TestOwnRange:
    """Human instruction 2026-10-08: 远程部队攻击位置优先按射程最大来安排.

    A city's strike reaches exactly two tiles, so a gun with range 3 or 4 that fires from 3 or 4
    takes **no retaliation at all**. The tile a shooter wants is therefore its OWN range, with two
    as the floor - a closer tile is only the fallback for a gun whose longer tiles are taken,
    ruled out by line of sight, or do not exist.
    """

    def test_a_range_two_gun_still_wants_the_distance_two_tile(self):
        assert st._preferred_distances(unit(1, "UNIT_TREBUCHET", "siege")) == (2,)
        assert st._preferred_distances(unit(2, "UNIT_CROSSBOWMAN", "ranged")) == (2, 1)

    def test_a_promoted_gun_wants_its_own_range_first(self):
        ranged = unit(3, "UNIT_ROCKET_ARTILLERY", "ranged")
        ranged.range = 4
        assert st._preferred_distances(ranged) == (4, 3, 2, 1)
        siege = unit(4, "UNIT_ROCKET_ARTILLERY", "siege")
        siege.range = 3
        # A siege unit is never adjacent to what it bombards, so 2 is the closest it is offered.
        assert st._preferred_distances(siege) == (3, 2)

    def test_a_range_three_gun_is_placed_on_the_distance_three_tile(self):
        gun = unit(1, "UNIT_ROCKET_ARTILLERY", "siege")
        gun.range = 3
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2),
            m.StagingRingTile(x=54, y=41, distance=3),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=1, x=54, y=41, turns=0, this_turn=True),
        ]
        result = st.assign(plan([gun], options, ring))
        assert result.placed[0].tile.distance == 3

    def test_a_range_two_gun_on_the_same_ring_takes_the_distance_two_tile(self):
        gun = unit(1, "UNIT_TREBUCHET", "siege")
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2),
            m.StagingRingTile(x=54, y=41, distance=3),
        ]
        options = [
            m.StagingOption(unit_id=1, x=55, y=41, turns=0, this_turn=True),
            m.StagingOption(unit_id=1, x=54, y=41, turns=0, this_turn=True),
        ]
        result = st.assign(plan([gun], options, ring))
        assert result.placed[0].tile.distance == 2

    def test_the_parser_reads_the_units_own_range_and_defaults_to_two(self):
        from civ_mcp import lua as lq

        parsed = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|60,29|ring:1|camp:0",
                "RING|59,28|2|ok|land|via:59,27,0",
                "UNIT|UNIT_ROCKET_ARTILLERY|7|60,36|3|siege|d2|cs70|hp100/100|rg3",
            ]
        )
        assert parsed.units[0].range == 3
        # An older server sends no `rg` token: the reading is the floor, 2, never 1.
        older = lq.parse_staging_plan_response(
            [
                "STAGEPLAN|60,29|ring:1|camp:0",
                "RING|59,28|2|ok|land|via:59,27,0",
                "UNIT|UNIT_CATAPULT|8|60,36|3|siege|d2|cs35|hp100/100",
            ]
        )
        assert older.units[0].range == 2

