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

    def test_the_neighbourhood_scan_has_both_coordinates(self):
        """`y` was never read, so the whole scan died on `y + dy` and reported nothing.

        Measured live 2026-09-25: the InGame Lua state answered
        `ERR:Runtime Error: ...:15: operator + is not supported for nil + number`, and because
        `GameState.unused_attacks` swallows the exception (by design - a failed scan is not a
        failed turn) the effect was silent: the driver's own `use-your-attacks` guard and the
        turn-check metric both read zero unused attacks on turns when units were standing next to
        enemies with a legal attack left. One missing `local y = unit:GetY()` disabled the check
        that exists to stop exactly that, so it gets its own test rather than riding on the
        structural one above.
        """
        query = lq.build_unused_attack_query()
        assert "local y = unit:GetY()" in query
        assert query.index("local y = unit:GetY()") < query.index("x + dx, y + dy")

    def test_a_siege_unit_is_scanned_at_its_bombard_range(self):
        """A Catapult is Combat 25 / RangedCombat 0 / Bombard 35 / Range 2.

        A range test that only reads `RangedCombat` gives it range 1 and reports no legal target
        two tiles away - measured live 2026-09-25, a Catapult at distance 2 from Moscow answered
        `REFUSING: no legal attack ... Legal targets from here: none` from the driver's guard.
        """
        query = lq.build_unused_attack_query()
        assert "entry.Bombard" in query
        assert "shoots" in query


class TestPhantomAttacksAreNotReported:
    """An entry that cannot be executed is not an unused attack.

    Measured T213-T215: `skip_remaining_units(force=True)` discarded three entries per turn -
    two Bombards (siege units cannot attack units at all, `ERR:SIEGE_CANNOT_ATTACK_UNITS`) and
    two melee units that had just entered a Zone of Control - and `use-your-attacks` failed on
    the same entries. A report that is wrong that often stops being read, so each cause is
    excluded in the query itself.
    """

    def test_a_siege_unit_is_not_scanned_against_unit_targets(self):
        query = lq.build_unused_attack_query()
        assert "can_hit_units" in query, "the unit-target scan must be gated on RangedCombat"
        assert "(rs > 0) or not shoots" in query

    def test_a_unit_with_no_attacks_left_is_skipped(self):
        # GetAttacksRemaining is the API SelectedUnit.lua uses to decide the same thing.
        query = lq.build_unused_attack_query()
        assert "GetAttacksRemaining" in query
        assert "attacks_left(unit) > 0" in query

    def test_a_missing_attack_count_api_keeps_the_unit(self):
        # Conservative default: a false alarm beats a lost attack.
        query = lq.build_unused_attack_query()
        assert "pcall(function() return u:GetAttacksRemaining() end)" in query
        assert "return 1" in query

    def test_a_unit_locked_by_a_zone_of_control_is_skipped(self):
        query = lq.build_unused_attack_query()
        assert "HasMovedIntoZOC()" in query

    def test_a_melee_land_unit_is_not_offered_a_target_at_sea(self):
        """manual:723 - the phantom this list was still handing the end-turn guard.

        Measured live T95-T97 on the running branch: a Barbarian Galley sat in our own harbour
        beside a Heavy Chariot and a Warrior, and the driver's guard refused to end the turn over
        `UNIT_HEAVY_CHARIOT@60,14 -> UNIT_GALLEY@59,13` on every one of those turns - while both
        orders came back `ERR:MELEE_CANNOT_ATTACK_AT_SEA`. The only way through was `--force`, and
        `--force` discards every pending attack, including the real ones (a Skirmisher's free shot
        at a Man-at-Arms went with it). A guard that cannot be satisfied teaches the session to
        ignore guards, which is worse than the entry it was reporting.
        """
        query = lq.build_unused_attack_query()
        # The same predicate the action path refuses on: the attacker is a land melee unit...
        assert "landMelee" in query
        assert 'entry.Domain == "DOMAIN_LAND"' in query
        # ...and the target is at sea.
        assert 'Domain == "DOMAIN_SEA"' in query
        # The exclusion has to sit exactly where the hit is recorded, not somewhere earlier: an
        # earlier `continue` would also drop a legal adjacency attack against a land unit.
        assert "if not (landMelee and atSea) then" in query
        assert query.index("if losOK then") < query.index("if not (landMelee and atSea) then")

    def test_the_engine_is_asked_at_every_shooting_distance(self):
        # The old gate was `if shoots and d > 1`, so a range-1 shooter was never checked.
        query = lq.build_unused_attack_query()
        assert "if shoots and d > 1 then" not in query
        assert "if shoots then" in query


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
            def __init__(self):
                self.writes = 0

            async def execute_write(self, _lua):
                self.writes += 1
                return ["OK:FORTIFIED|2 fortified"]

            async def execute_read(self, _lua):
                self.writes += 1
                return ["OK:SKIPPED|13 units"]

        gs.conn = Conn()
        return gs

    def test_the_sweep_refuses_while_an_attack_is_pending(self):
        """Naming the loss was not enough - four attacks died this way over one war.

        Measured T145-T152: a Crossbowman pair with a legal shot on the galley at (50,23), a
        Horseman standing adjacent to its target at (56,42), and a Man-at-Arms twice (the
        second one a real second attack, the one ELITE_GUARD grants). Refusing is what makes
        the loss impossible rather than reported after the fact.
        """
        gs = self._gs(["UNIT_HEAVY_CHARIOT@53,36 -> UNIT_SWORDSMAN@53,35(7hp)"])
        report = asyncio.run(gs.skip_remaining_units())
        assert report.startswith("REFUSED|UNUSED ATTACK (1 unit(s)")
        assert "UNIT_HEAVY_CHARIOT@53,36 -> UNIT_SWORDSMAN@53,35(7hp)" in report
        assert "force=True" in report
        assert gs.conn.writes == 0, "a refusal must not fortify or finish anything"

    def test_force_sweeps_and_names_what_it_discarded(self):
        gs = self._gs(["UNIT_HORSEMAN@56,42 -> UNIT_MAN_AT_ARMS@56,43(76hp)"])
        report = asyncio.run(gs.skip_remaining_units(force=True))
        assert "UNUSED ATTACK (1 unit(s) had a legal attack" in report
        assert "UNIT_HORSEMAN@56,42" in report
        assert "SKIPPED|13 units" in report, "the deliberate sweep still happens"

    def test_a_clean_turn_says_nothing_extra(self):
        gs = self._gs([])
        report = asyncio.run(gs.skip_remaining_units())
        assert "UNUSED ATTACK" not in report
        assert "SKIPPED|13 units" in report
        assert "FORTIFIED|2 fortified" in report


class TestTheEndTurnSweep:
    """The path that actually ate them: end_turn resolves the "units with moves" blocker.

    It must keep resolving it - one forgotten unit used to freeze the turn for the whole poll
    budget - but never when the leftover move is an attack.
    """

    def _gs(self, entries):
        return TestTheSkipReport()._gs(entries)

    def test_a_pending_attack_bounces_the_turn_without_sweeping(self):
        gs = self._gs(["UNIT_MAN_AT_ARMS@56,42 -> UNIT_GREAT_WRITER@56,43(100hp)"])
        resolved, note = asyncio.run(et._sweep_unmoved_units(gs))
        assert resolved is False
        assert "UNUSED ATTACK at end_turn" in note
        assert "UNIT_MAN_AT_ARMS@56,42" in note
        assert "force=True" in note
        assert gs.conn.writes == 0

    def test_a_forgotten_unit_is_still_swept(self):
        gs = self._gs([])
        resolved, note = asyncio.run(et._sweep_unmoved_units(gs))
        assert resolved is True
        assert "SKIPPED|13 units" in note
        assert gs.conn.writes == 2, "fortify then skip, exactly as before"

    def test_a_refusal_from_the_sweep_itself_is_surfaced_not_looped(self):
        # The two scans can disagree (the first read can fail and return [] by design), so the
        # sweep's own refusal has to end the loop rather than send it round again.
        class Refusing:
            async def unused_attacks(self):
                return []

            async def skip_remaining_units(self, force=False):
                from civ_mcp.game_state import SKIP_REFUSED

                return f"{SKIP_REFUSED}UNUSED ATTACK (1 unit(s) ...)"

        resolved, note = asyncio.run(et._sweep_unmoved_units(Refusing()))
        assert resolved is False
        assert note.startswith("REFUSED|")


class TestTheRules:
    FILE = pathlib.Path("prompts/checks/turn-checks.md")

    def context(self, **metrics):
        base = {"wonders": 1, "districts": 30, "pop": 30, "improvements": 90, "cities": 5,
                "gold_per_turn": 30, "attacks_this_turn": 0, "unused_attacks": 0}
        base.update(metrics)
        return turn_checks.CheckContext(turn=115, units={}, metrics=base, researched=frozenset())

    def failing(self, **metrics) -> set[str]:
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8-sig"), self.context(**metrics))
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
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8-sig"), et._context_from_row(row))
        assert "use-your-attacks" not in run.failing_ids
        assert "finish-the-wounded" not in run.failing_ids
        assert not [c for c, reason in run.failures if "un-evaluable" in reason]
