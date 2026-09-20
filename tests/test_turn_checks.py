"""Turn checks: rules in a markdown file, evaluated by end_turn every turn.

The point of the file is that a rule with a deadline stops depending on the agent
remembering it. The motivating case is real: Battering Ram and Siege Tower go obsolete at
CIVIC_CIVIL_ENGINEERING, and the live game reached T121 with neither built and the civic not
yet adopted - a window that was still open and would have closed silently.
"""

from __future__ import annotations

import pathlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402

CHECKS = pathlib.Path("prompts/checks/turn-checks.md")


def unit(uid: int, unit_type: str) -> m.UnitInfo:
    return m.UnitInfo(
        unit_id=uid,
        unit_index=uid,
        name=unit_type,
        unit_type=unit_type,
        x=0,
        y=0,
        moves_remaining=2,
        max_moves=2,
        health=100,
        max_health=100,
    )


def context(turn=121, units=None, **metrics) -> turn_checks.CheckContext:
    base = {
        "science": 44.7,
        "culture": 33.6,
        "gold_per_turn": 11.4,
        "military": 111,
        "pop": 31,
        "cities": 5,
        "districts": 7,
        "improvements": 24,
        "wonders": 1,
        "territory": 64,
        "techs_completed": 20,
        "civics_completed": 13,
        "trade_routes": {"capacity": 1, "active": 1},
    }
    base.update(metrics)
    return turn_checks.CheckContext(
        turn=turn,
        units=units or {},
        metrics=base,
        researched=frozenset({"TECH_ENGINEERING", "TECH_MILITARY_ENGINEERING"}),
    )


class TestParsing:
    def test_reads_a_block_with_all_its_fields(self):
        checks = turn_checks.parse_checks(
            """
            <!-- check
            id: ram
            when: not researched(CIVIC_CIVIL_ENGINEERING)
            require: units(BATTERING_RAM) >= 1
            message: build one
            level: error
            -->
            """
        )
        assert len(checks) == 1
        assert checks[0].check_id == "ram"
        assert checks[0].level == "error"
        assert checks[0].when == "not researched(CIVIC_CIVIL_ENGINEERING)"

    def test_multiline_messages_are_kept_together(self):
        checks = turn_checks.parse_checks(
            "<!-- check\nid: x\nrequire: 1 == 1\nmessage: first line\n  second line\n-->"
        )
        assert "second line" in checks[0].message

    def test_a_block_without_a_requirement_is_prose_not_a_rule(self):
        # The file documents its own format, so an example in the text has the same shape
        # as a rule. Only a complete block is a rule.
        assert turn_checks.parse_checks("<!-- check\nid: x\nmessage: no requirement\n-->") == []

    def test_prose_outside_blocks_is_ignored(self):
        assert turn_checks.parse_checks("# Title\n\njust prose, no rules\n") == []


class TestEvaluator:
    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("units(ARCHER) == 1", True),
            ("units(ARCHER, WARRIOR) == 2", True),
            ("researched(TECH_ENGINEERING)", True),
            ("not researched(CIVIC_CIVIL_ENGINEERING)", True),
            ("metric(districts) >= metric(pop) // 3", False),
            ("metric(gold_per_turn) >= 10", True),
            ("metric(trade_routes.active) >= metric(trade_routes.capacity)", True),
            ("turn() >= 90 and metric(wonders) >= 1", True),
            ("turn() < 90 or metric(wonders) == 0", False),
        ],
    )
    def test_expressions(self, expression, expected):
        ctx = context(units={1: unit(1, "UNIT_ARCHER"), 2: unit(2, "UNIT_WARRIOR")})
        assert bool(turn_checks.evaluate(expression, ctx)) is expected

    def test_code_is_not_an_expression(self):
        # A check file is data. Nothing in it may reach Python.
        for hostile in (
            "__import__('os').system('echo hi')",
            "open('/etc/passwd').read()",
            "metric.__class__",
            "(lambda: 1)()",
        ):
            with pytest.raises(turn_checks.CheckError):
                turn_checks.evaluate(hostile, context())

    def test_an_unknown_metric_is_reported_not_guessed(self):
        with pytest.raises(turn_checks.CheckError):
            turn_checks.evaluate("metric(unicorns) > 0", context())


class TestRunChecks:
    def test_a_failing_rule_is_returned_with_its_reason(self):
        text = (
            "<!-- check\nid: siege\nrequire: units(CATAPULT, TREBUCHET) >= 2\n"
            "message: fewer than two siege units\n-->"
        )
        run = turn_checks.run_checks(text, context())
        checks, failures = run.checks, run.failures
        assert len(run.checks) == 1 and len(run.failures) == 1
        assert run.failures[0][0].check_id == "siege"
        assert run.failures[0][1] == "units(CATAPULT, TREBUCHET) >= 2"

    def test_a_passing_rule_is_silent(self):
        text = "<!-- check\nid: ok\nrequire: metric(wonders) >= 1\nmessage: x\n-->"
        run = turn_checks.run_checks(text, context())
        assert run.failures == []

    def test_the_when_gate_skips_rather_than_fails(self):
        text = (
            "<!-- check\nid: gated\nwhen: turn() < 90\nrequire: units(CATAPULT) >= 2\n"
            "message: x\n-->"
        )
        run = turn_checks.run_checks(text, context(turn=121))
        assert run.failures == []

    def test_a_broken_expression_is_reported_rather_than_dropped(self):
        text = "<!-- check\nid: bad\nrequire: metric(unicorns) > 0\nmessage: x\n-->"
        run = turn_checks.run_checks(text, context())
        assert len(run.failures) == 1
        assert "un-evaluable" in run.failures[0][1]


class TestTheRealFile:
    """The shipped check file has to parse and evaluate, not just exist."""

    def test_it_parses(self):
        text = CHECKS.read_text(encoding="utf-8")
        checks = turn_checks.parse_checks(text)
        assert len(checks) >= 5
        assert len({c.check_id for c in checks}) == len(checks), "duplicate ids"

    def test_the_ram_tower_deadline_fires_on_the_live_position(self):
        # T121 of the live game: no ram or tower, civil engineering not yet adopted.
        text = CHECKS.read_text(encoding="utf-8")
        units = {
            1: unit(1, "UNIT_ARCHER"),
            2: unit(2, "UNIT_MAN_AT_ARMS"),
            3: unit(3, "UNIT_SCOUT"),
            4: unit(4, "UNIT_TRADER"),
            5: unit(5, "UNIT_SETTLER"),
            6: unit(6, "UNIT_BUILDER"),
            7: unit(7, "UNIT_BUILDER"),
        }
        run = turn_checks.run_checks(text, context(units=units))
        ids = {check.check_id for check, _ in run.failures}
        assert "ram-tower-before-civil-engineering" in ids
        assert "siege-train" in ids
        assert "ranged-mass" in ids
        assert "melee-screen" in ids
        # and the rules that do hold stay quiet
        assert "dynasty-cycle-wonder" not in ids
        assert "carrying-capacity" not in ids
        # the idle trade route is the built-in empire warning's job, not a duplicate rule here
        assert "no-idle-trade-route" not in {c.check_id for c in turn_checks.parse_checks(text)}

    def test_the_ram_tower_check_goes_quiet_once_the_civic_lands(self):
        text = CHECKS.read_text(encoding="utf-8")
        ctx = turn_checks.CheckContext(
            turn=121,
            units={},
            metrics={"wonders": 1, "districts": 1, "pop": 3, "gold_per_turn": 20,
                     "trade_routes": {"capacity": 1, "active": 1}},
            researched=frozenset({"CIVIC_CIVIL_ENGINEERING"}),
        )
        run = turn_checks.run_checks(text, ctx)
        # The civic landed, so the `when` gate retires the rule: skipped, not failed.
        assert "ram-tower-before-civil-engineering" not in run.failing_ids
        assert "ram-tower-before-civil-engineering" in run.skipped
