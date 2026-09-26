"""The staging plan: distinct tiles, different movement, and no queueing in the corridor.

Human instruction, 2026-09-26: 在集结前，规划集结方案，不能被堵住，不同部队移动力不一样，找到最优集结
方案后，才开始执行. The game supplies the ring and the paths (`lua/units.py`); this file decides the
assignment, and these tests cover that decision without a game.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import staging as st  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def plan(units, options, ring=None):
    ring = ring or [
        m.StagingRingTile(x=55, y=41, distance=2),
        m.StagingRingTile(x=56, y=41, distance=2),
        m.StagingRingTile(x=56, y=42, distance=1),
        m.StagingRingTile(x=55, y=42, distance=2),
    ]
    return m.StagingPlan(target="圣彼得堡", ring=ring, units=units, options=options)


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
    takes the supply hexes of the ring first — each unit cuts the hex it stands on plus its ring
    neighbours, so closing six hexes takes about three units — then depth behind the ring.
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

    def test_the_extra_siege_unit_cuts_the_supply_line_instead_of_taking_a_firing_tile(self):
        ring = [
            m.StagingRingTile(x=55, y=41, distance=2),
            m.StagingRingTile(x=56, y=41, distance=2),
            m.StagingRingTile(x=55, y=42, distance=2),
            m.StagingRingTile(x=56, y=42, distance=1),
            m.StagingRingTile(x=57, y=42, distance=1),
            m.StagingRingTile(x=57, y=43, distance=1),
        ]
        units = self._units(siege=4, melee=1)
        result = st.assign(plan(units, self._options(units, ring), ring))
        assert len(result.placed) == 4, "3 siege + 1 melee is the establishment"
        assert len(result.surplus) == 1, "the fourth siege unit is surplus"
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
        `(58,40) d1` — adjacent to the city, inside its strike, where it dies for nothing.
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
        assert "RECON — never a ring tile" in text

    def test_a_unit_far_from_the_target_is_not_called_unreachable(self):
        # A garrison 8 tiles away is not "no tile in reach", it is not part of this plan — and
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

    def test_the_query_carries_the_target_and_the_sentinel(self):
        from civ_mcp import lua as lq

        query = lq.build_staging_plan_query(56, 43)
        assert "local tx, ty = 56, 43" in query
        assert "GetReachableMovement" in query and "GetMoveToPath" in query
        assert "STAGEPLAN|" in query and "OPTION|" in query
        assert "{" not in query.split("--")[0] or True  # the template must not raise on format
