"""`get_reinforcements`: what is in the plan, and which turn what is building reaches the rally.

`tactics/07` step 3 asks "how long, and what will it cost", and the leg that decides a deadline was
split between two tools - a city's queue countdown in `get_cities` and a map distance in the
pathing tool - with nothing joining them. Measured shape of the miss: a second Catapult ordered for
a siege that had already opened, arriving after the walls were down.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import narrate as nr  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402

ROW = (
    "REINF|UNIT_CATAPULT|siege|moves:2|ready:3|dist:12|rally:55,45|rallydist:5"
    "|city:Xian|cityxy:52,44"
)


class TestTheParser:
    def test_a_queue_row_reads_in_full(self):
        rows = lq.parse_reinforcement_response([ROW])
        assert len(rows) == 1
        r = rows[0]
        assert r.unit_type == "UNIT_CATAPULT" and r.role == "siege"
        assert r.moves == 2 and r.ready_turns == 3 and r.distance == 12
        assert r.rally == (55, 45) and r.rally_distance == 5
        assert r.city == "Xian" and (r.city_x, r.city_y) == (52, 44)

    def test_junk_and_short_rows_are_ignored(self):
        assert lq.parse_reinforcement_response(["junk", "REINF|UNIT_X", ""]) == []

    def test_a_row_with_no_rally_tile_still_parses(self):
        rows = lq.parse_reinforcement_response(
            ["REINF|UNIT_ARCHER|ranged|moves:2|ready:1|dist:9|rally:-|rallydist:-1|city:Beijing|cityxy:50,40"]
        )
        assert rows[0].rally is None and rows[0].rally_distance == -1
        assert rows[0].march_turns == 0, "no rally tile means no march leg to estimate"


class TestTheArithmetic:
    def test_the_arrival_is_the_queue_plus_the_march(self):
        r = lq.Reinforcement(
            unit_type="UNIT_CATAPULT", role="siege", moves=2, ready_turns=3, rally_distance=5
        )
        assert r.march_turns == 3  # 5 tiles at 2 moves, rounded up
        assert r.arrives_in == 6

    def test_a_fast_unit_marches_faster(self):
        slow = lq.Reinforcement(unit_type="U", moves=2, ready_turns=0, rally_distance=9)
        fast = lq.Reinforcement(unit_type="U", moves=4, ready_turns=0, rally_distance=9)
        assert slow.march_turns == 5 and fast.march_turns == 3

    def test_a_ready_unit_that_is_already_there_arrives_now(self):
        r = lq.Reinforcement(unit_type="U", moves=2, ready_turns=0, rally_distance=0)
        assert r.march_turns == 0 and r.arrives_in == 0

    def test_the_queue_is_never_negative(self):
        r = lq.Reinforcement(unit_type="U", moves=2, ready_turns=-1, rally_distance=4)
        assert r.arrives_in == 2


def plan(units, options, ring=None):
    ring = ring or [
        m.StagingRingTile(x=56, y=43, distance=2, between=[(57, 43, 0)]),
        m.StagingRingTile(x=57, y=42, distance=1),
    ]
    return m.StagingPlan(target="58,42", ring=ring, units=units, options=options)


def unit(uid, kind, role, x=55, y=41):
    return m.StagingUnit(unit_type=kind, unit_id=uid, x=x, y=y, moves=2, role=role)


def siege_plan():
    return plan(
        [unit(12, "UNIT_TREBUCHET", "siege"), unit(18, "UNIT_MAN_AT_ARMS", "melee")],
        [
            m.StagingOption(unit_id=12, x=56, y=43, turns=0, this_turn=True),
            m.StagingOption(unit_id=18, x=57, y=42, turns=0, this_turn=True),
        ],
    )


class TestTheNarration:
    def test_it_names_the_plan_and_every_arrival(self):
        report = lq.ReinforcementReport(
            target="58,42",
            plan=siege_plan(),
            building=lq.parse_reinforcement_response([ROW]),
        )
        text = nr.narrate_reinforcements(report)
        assert "REINFORCEMENTS to 58,42" in text
        assert "in the plan now: melee 1, siege 1" in text
        assert "CATAPULT [siege, 2 moves] from Xian (52,44): ready T+3" in text
        assert "at the rally ~T+6" in text
        assert "estimate" in text and "does not exist yet" in text

    def test_an_empty_queue_says_nothing_is_coming(self):
        text = nr.narrate_reinforcements(
            lq.ReinforcementReport(target="58,42", plan=siege_plan(), building=[])
        )
        assert "no military unit is in any queue" in text
        assert "purchase" in text

    def test_a_role_nothing_covers_is_named(self):
        report = lq.ReinforcementReport(
            target="58,42",
            plan=siege_plan(),
            building=lq.parse_reinforcement_response([ROW]),
        )
        text = nr.narrate_reinforcements(report)
        assert "no ranged unit in place or building" in text
        assert "no siege unit in place or building" not in text  # one is in the plan

    def test_a_row_with_no_rally_tile_is_called_out(self):
        report = lq.ReinforcementReport(
            target="58,42",
            plan=None,
            building=lq.parse_reinforcement_response(
                ["REINF|UNIT_ARCHER|ranged|moves:2|ready:1|dist:9|rally:-|rallydist:-1|city:B|cityxy:50,40"]
            ),
        )
        text = nr.narrate_reinforcements(report)
        assert "no passable distance-3 tile" in text

    def test_the_arrival_is_compared_with_the_plan_s_opening_turn(self):
        building = lq.parse_reinforcement_response(
            ["REINF|UNIT_CATAPULT|siege|moves:2|ready:9|dist:6|rally:55,45|rallydist:4|city:X|cityxy:52,44"]
        )
        text = nr.narrate_reinforcements(
            lq.ReinforcementReport(target="58,42", plan=siege_plan(), building=building)
        )
        assert "after the assault's own opening turn" in text and "purchase_item" in text


class TestTheQuery:
    def test_it_reads_the_queue_and_the_map_in_one_pass(self):
        q = lq.build_reinforcement_query(58, 42)
        assert "bq:GetCurrentProductionTypeHash()" in q
        assert "bq:GetTurnsLeft()" in q
        assert "Map.GetPlotDistance(cx, cy, tx, ty)" in q
        assert "Map.GetPlotDistance(tx, ty, px, py) == 3" in q
        assert 'print("REINF|"' in q

    def test_it_reports_military_units_only(self):
        q = lq.build_reinforcement_query(58, 42)
        assert 'string.find(name, "^UNIT_")' in q
        assert "(cs + rs + bomb) > 0" in q

    def test_its_roles_are_the_staging_plans_roles(self):
        q = lq.build_reinforcement_query(58, 42)
        for role in ('role = "recon"', 'role = "siege"', 'role = "ranged"', 'role = "short-ranged"'):
            assert role in q, role

    def test_it_is_read_only(self):
        q = lq.build_reinforcement_query(58, 42)
        for write in ("RequestOperation", "RequestCommand", "SetProduction", "end_turn"):
            assert write not in q, write


class TestTheComposition:
    def test_the_report_is_a_plan_and_a_queue_read(self):
        from civ_mcp.game_state import GameState

        queries: list[str] = []

        class FakeConn:
            async def execute_write(self, lua, timeout=5.0):
                queries.append(lua)
                if "REINF|" in lua:
                    return [ROW]
                return [
                    "STAGEPLAN|58,42|ring:2|camp:0",
                    "RING|56,43|2|ok|land|hill:0|sight:0|via:57,43,0",
                    "RING|57,42|1|ok|land|hill:0|sight:0",
                    "UNIT|UNIT_TREBUCHET|12|55,41|2|siege|d4|cs35|hp100/100",
                    "UNIT|UNIT_MAN_AT_ARMS|18|55,40|2|melee|d4|cs45|hp100/100",
                    "OPTION|12|56,43|0|1|4",
                    "OPTION|18|57,42|0|1|3",
                ]

        gs = GameState.__new__(GameState)
        gs.conn = FakeConn()
        report = asyncio.run(gs.reinforcements(58, 42))
        assert len(queries) == 2
        assert report.plan is not None and report.plan.ring
        assert report.building and report.building[0].unit_type == "UNIT_CATAPULT"
        text = nr.narrate_reinforcements(report)
        assert "REINFORCEMENTS to 58,42" in text and "CATAPULT" in text
