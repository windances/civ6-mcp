"""Unused attacks are reported where they are thrown away, and checked where they are counted.

The failure this exists for (live T109-T116): a Heavy Chariot stood on (53,36) with two
movement points for seven turns, twice with a Russian Swordsman on the adjacent tile at 53 hp
and once at 7 hp, and never attacked. `get_units` even printed
`>> CAN ATTACK: UNIT_SWORDSMAN@53,35(7hp)` for it. Every turn closed with
`skip_remaining_units`, which fortified the chariot and said nothing about the attack it had
just discarded.

Two fixes: the skip call now lists the attacks it is about to destroy, and the check context
carries `unused_attacks` so a rule can fire on the fact rather than on "did you attack
anything at all" (two Catapults shooting a city satisfied the old rule while the enemy one
tile away was ignored).
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402

LINE = (
    "UNUSED_ATTACK|UNIT_HEAVY_CHARIOT|1310724|53,36|"
    "UNIT_SWORDSMAN@53,35(7hp);UNIT_ARCHER@51,36(100hp)"
)


class TestParsing:
    def test_one_entry_per_unit_with_its_targets(self):
        assert lq.parse_unused_attack_response([LINE]) == [
            "UNIT_HEAVY_CHARIOT@53,36 -> UNIT_SWORDSMAN@53,35(7hp);UNIT_ARCHER@51,36(100hp)"
        ]

    def test_nothing_to_report(self):
        assert lq.parse_unused_attack_response(["NO_UNUSED_ATTACKS"]) == []

    def test_a_malformed_line_is_skipped_not_crashed(self):
        assert lq.parse_unused_attack_response(["UNUSED_ATTACK|UNIT_X", "garbage"]) == []

    def test_the_query_asks_the_same_question_as_the_can_attack_hint(self):
        # Same legality test as build_units_query: adjacency, LOS via CanStartOperation for
        # ranged beyond one tile, barbarians always hostile, war required otherwise.
        query = lq.build_unused_attack_query()
        assert "GetMovesRemaining() > 0" in query
        assert "CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK" in query
        assert "IsAtWarWith(otherOwner)" in query
        assert "{SENTINEL}" not in query, "the marker must be substituted"


class FakeGS:
    """Only what the metric helper touches."""

    def __init__(self, entries):
        self.entries = entries
        self.calls = 0

    async def unused_attacks(self):
        self.calls += 1
        return list(self.entries)


class TestTheMetric:
    def test_it_counts_units_not_targets(self):
        gs = FakeGS(["A -> B", "C -> D"])
        metrics = asyncio.run(et._contact_metrics(gs, 115, {}))
        assert metrics["unused_attacks"] == 2

    def test_it_is_zero_when_nothing_is_left_unused(self):
        metrics = asyncio.run(et._contact_metrics(FakeGS([]), 115, {}))
        assert metrics["unused_attacks"] == 0

    def test_it_is_cached_for_the_turn(self):
        gs = FakeGS(["A -> B"])
        asyncio.run(et._contact_metrics(gs, 115, {}))
        asyncio.run(et._contact_metrics(gs, 115, {}))
        assert gs.calls == 1, "the check path can run several times a turn"

    def test_a_failed_scan_is_not_an_exception(self):
        class Broken(FakeGS):
            async def unused_attacks(self):
                raise RuntimeError("tuner busy")

        assert asyncio.run(et._contact_metrics(Broken([]), 115, {}))["unused_attacks"] == 0

    def test_a_historical_row_reads_as_zero(self):
        row = {"turn": 115, "is_agent": True, "unit_composition": {"WARRIOR": 1}}
        assert et._context_from_row(row).metrics["unused_attacks"] == 0


class TestTheSkipReport:
    def _gs(self, entries):
        from civ_mcp.game_state import GameState

        gs = GameState.__new__(GameState)

        async def unused():
            return list(entries)

        gs.unused_attacks = unused

        class Conn:
            async def execute_write(self, _lua):
                return ["OK:FORTIFIED|2 fortified"]

            async def execute_read(self, _lua):
                return ["OK:SKIPPED|13 units"]

        gs.conn = Conn()
        return gs

    def test_the_attack_about_to_be_lost_is_named(self):
        gs = self._gs(["UNIT_HEAVY_CHARIOT@53,36 -> UNIT_SWORDSMAN@53,35(7hp)"])
        report = asyncio.run(gs.skip_remaining_units())
        assert "UNUSED ATTACK (1 unit(s)" in report
        assert "UNIT_HEAVY_CHARIOT@53,36 -> UNIT_SWORDSMAN@53,35(7hp)" in report
        assert "finished for the turn" in report
        assert "SKIPPED|13 units" in report, "the skip still happens"

    def test_a_clean_turn_says_nothing_extra(self):
        gs = self._gs([])
        report = asyncio.run(gs.skip_remaining_units())
        assert "UNUSED ATTACK" not in report
        assert "SKIPPED|13 units" in report
        assert "FORTIFIED|2 fortified" in report


class TestTheRules:
    FILE = pathlib.Path("prompts/checks/turn-checks.md")

    def context(self, **metrics):
        base = {"wonders": 1, "districts": 30, "pop": 30, "improvements": 90, "cities": 5,
                "gold_per_turn": 30, "attacks_this_turn": 0, "unused_attacks": 0}
        base.update(metrics)
        return turn_checks.CheckContext(turn=115, units={}, metrics=base, researched=frozenset())

    def failing(self, **metrics) -> set[str]:
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), self.context(**metrics))
        return run.failing_ids

    def test_an_unused_attack_fails_even_though_other_units_attacked(self):
        # The live T111 shape: two Catapults fired at the city while an adjacent 53 hp
        # Swordsman was ignored. `attacks_this_turn >= 1` would have passed.
        ids = self.failing(attacks_this_turn=2, unused_attacks=2, enemies_within_2=1)
        assert "use-your-attacks" in ids
        assert "engage-the-screen" not in ids, "something did attack this turn"

    def test_every_attack_used_is_quiet(self):
        assert "use-your-attacks" not in self.failing(unused_attacks=0)

    def test_a_wounded_enemy_with_no_attack_fails(self):
        ids = self.failing(weakest_enemy_hp_within_2=7, enemies_within_2=1)
        assert "finish-the-wounded" in ids

    def test_a_wounded_enemy_and_one_attack_clears_it(self):
        ids = self.failing(weakest_enemy_hp_within_2=7, enemies_within_2=1, attacks_this_turn=1)
        assert "finish-the-wounded" not in ids

    def test_a_healthy_enemy_is_not_this_rules_business(self):
        assert "finish-the-wounded" not in self.failing(weakest_enemy_hp_within_2=80)

    def test_the_history_recomputes_without_the_new_metrics(self):
        # A stored row has neither metric; zeros must leave both rules quiet rather than
        # reporting them un-evaluable (which would show as a permanent streak).
        row = {
            "turn": 115, "is_agent": True, "unit_composition": {"WARRIOR": 2},
            "pop": 30, "districts": 30, "wonders": 1, "cities": 5, "improvements": 90,
            "gold_per_turn": 30,
        }
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), et._context_from_row(row))
        assert "use-your-attacks" not in run.failing_ids
        assert "finish-the-wounded" not in run.failing_ids
        assert not [c for c, reason in run.failures if "un-evaluable" in reason]
