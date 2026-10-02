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
        text = CHECKS.read_text(encoding="utf-8-sig")
        checks = turn_checks.parse_checks(text)
        assert len(checks) >= 5
        assert len({c.check_id for c in checks}) == len(checks), "duplicate ids"

    def test_every_retirement_trace_still_resolves_to_its_archived_block(self):
        # A `once: true` goal leaves the file as `<!-- achieved T<turn>: <id> (game: <key>)
        # (original in archive/<file>) -->`. That trace is the *only* way back, so an orphaned one
        # is a rule that can never return - and silence is exactly how it would fail.
        text = CHECKS.read_text(encoding="utf-8-sig")
        traces = [ln.strip() for ln in text.splitlines() if turn_checks._ACHIEVED_TRACE.match(ln.strip())]
        assert traces, "no retirement traces: this test would then prove nothing"
        for trace in traces:
            match = turn_checks._ACHIEVED_TRACE.match(trace)
            archive = pathlib.Path("prompts/checks/archive") / pathlib.Path(match.group("archive")).name
            assert archive.exists(), f"{trace} names a missing archive copy"
            assert turn_checks.archived_goal_block(archive, match.group("id")) is not None, trace

    def test_the_china_wonder_obligation_is_live_or_recoverable(self):
        # Measured 2026-09-30: this goal had retired as `achieved T99` for a *different* match key
        # (`china_-1894041591`) while the A3-A7 experiment replayed a T1 branch of the same save
        # (`china_911679432`); a retirement trace carried no match key, so the rule was absent from
        # the live loop for the experiment's whole ~340 turns and all eight sessions built zero
        # wonders. Dynastic Cycle's wonder clause is half of the civilisation ability the directive
        # opens with, so the goal must be either live in the shipped file or recoverable - never
        # silently gone. Since 2026-10-02 the trace names the match that achieved it and
        # `restore_foreign_games` puts another match's goal back, so "recoverable" is now automatic
        # rather than a property of the file happening to still hold the block.
        text = CHECKS.read_text(encoding="utf-8-sig")
        live = {c.check_id for c in turn_checks.parse_checks(text)}
        trace = next(
            (
                ln.strip()
                for ln in text.splitlines()
                if turn_checks._ACHIEVED_TRACE.match(ln.strip())
                and turn_checks._ACHIEVED_TRACE.match(ln.strip()).group("id") == "dynasty-cycle-wonder"
            ),
            None,
        )
        assert "dynasty-cycle-wonder" in live or trace, (
            "dynasty-cycle-wonder is neither live nor recoverable from an achieved trace"
        )
        if "dynasty-cycle-wonder" in live:
            rule = next(c for c in turn_checks.parse_checks(text) if c.check_id == "dynasty-cycle-wonder")
            # The gate has to leave turns in which a wonder can actually be produced.
            assert rule.when and ">= 25" in rule.when, rule.when
            assert "50%" in rule.message, "the boost figure must be the Gathering Storm one"

    def test_the_ram_tower_deadline_fires_on_the_live_position(self):
        # T121 of the live game: no ram or tower, civil engineering not yet adopted.
        # The baseline, not the live file: the goal leaves the shipped file once it is met.
        text = turn_checks.restore_achieved(CHECKS.read_text(encoding="utf-8-sig"))
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
        text = turn_checks.restore_achieved(CHECKS.read_text(encoding="utf-8-sig"))
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


class TestAGoalAnotherMatchAchievedComesBack:
    """The check file is shared by every match played from this checkout (fixed 2026-10-02).

    A `once: true` goal is pruned from the file the turn it is achieved, and the file is one file -
    so a goal match A achieved was gone for match B. Measured: the A3-A7 military-production
    experiment ran its whole ~340 turns with `dynasty-cycle-wonder` absent from the loop and all
    eight sessions ordered zero wonders. The trace now names the match that wrote it, and a trace
    naming a *different* match is restored on load.
    """

    GOAL = """<!-- check
id: a-goal
when: turn() >= 25
once: true
require: metric(wonders) >= 1
message: A wonder is wanted.
-->
"""

    def board(self, tmp_path: pathlib.Path, game: str, trace_game: str | None) -> pathlib.Path:
        """A check file whose only goal has retired, plus the archive the trace points at."""
        archive = tmp_path / "archive"
        archive.mkdir(parents=True, exist_ok=True)
        (archive / "turn-checks-20260101-000000.md").write_text(
            self.GOAL, encoding="utf-8"
        )
        key = f" (game: {trace_game})" if trace_game else ""
        trace = (
            f"<!-- achieved T99: a-goal{key}"
            " (original in archive/turn-checks-20260101-000000.md) -->\n"
        )
        path = tmp_path / "turn-checks.md"
        path.write_text("# Checks\n\n" + trace, encoding="utf-8")
        return path

    def test_a_goal_another_match_achieved_is_restored(self, tmp_path):
        path = self.board(tmp_path, "china_B", "china_A")
        text = path.read_text(encoding="utf-8")
        restored_text, restored = turn_checks.restore_foreign_games(
            text, "china_B", tmp_path
        )
        assert restored == ["a-goal"]
        assert "id: a-goal" in restored_text, "the block must come back, not just the id"
        assert "achieved T99" not in restored_text, "the trace is replaced by the block"
        # and the rule is live again for the check run
        assert {c.check_id for c in turn_checks.parse_checks(restored_text)} == {"a-goal"}
        # idempotent: a second call has nothing left to restore
        assert turn_checks.restore_foreign_games(restored_text, "china_B", tmp_path)[1] == []

    def test_this_matches_own_achievement_stays_retired(self, tmp_path):
        path = self.board(tmp_path, "china_A", "china_A")
        text = path.read_text(encoding="utf-8")
        restored_text, restored = turn_checks.restore_foreign_games(text, "china_A", tmp_path)
        assert restored == []
        assert restored_text == text, "this match already did it; re-arming it would nag for ever"

    def test_an_old_trace_without_a_key_is_left_alone(self, tmp_path):
        # The ambiguity is real (was it this match?) and guessing could re-arm a goal already done,
        # so an unattributable trace stays where it is.
        path = self.board(tmp_path, "china_B", None)
        text = path.read_text(encoding="utf-8")
        restored_text, restored = turn_checks.restore_foreign_games(text, "china_B", tmp_path)
        assert restored == [] and restored_text == text

    def test_without_a_game_key_nothing_is_touched(self, tmp_path):
        path = self.board(tmp_path, "china_B", "china_A")
        text = path.read_text(encoding="utf-8")
        assert turn_checks.restore_foreign_games(text, "", tmp_path) == (text, [])

    def test_the_sweep_writes_the_key_into_the_trace(self, tmp_path):
        # The round trip: a sweep for game A leaves a trace A can be identified by, so game B's
        # load restores the goal.
        archive = tmp_path / "archive"
        archive.mkdir(parents=True, exist_ok=True)
        (archive / "turn-checks-20260101-000000.md").write_text(self.GOAL, encoding="utf-8")
        path = tmp_path / "turn-checks.md"
        path.write_text("# Checks\n\n" + self.GOAL, encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        pruned, removed = turn_checks.remove_achieved(
            text,
            {"a-goal": 99},
            "20260101-000000",
            "archive/turn-checks-20260101-000000.md",
            "china_A",
        )
        assert removed == ["a-goal"]
        assert "(game: china_A)" in pruned
        # ... and the trace the sweep wrote is one the parser reads back and restores.
        assert turn_checks._ACHIEVED_TRACE.match(pruned.splitlines()[-1].strip())
        back, restored = turn_checks.restore_foreign_games(pruned, "china_B", tmp_path)
        assert restored == ["a-goal"] and "id: a-goal" in back


class TestTheRuleFileIsWrittenWithoutABom:
    """The English-only bar is also a no-BOM rule, and the prune used to break it.

    Measured on the live branch at T116: the first turn a ``once: true`` goal was achieved, the
    sweep rewrote ``prompts/checks/turn-checks.md`` through ``utf-8-sig``, which writes a BOM every
    time. The file is in ``text_encoding.ASCII_ONLY_DELIVERED`` - it is pure ASCII and its
    ``message:`` lines are printed into a model's context - so a BOM on it is a stray one, and both
    the pre-commit gate and ``tests/test_text_encoding.py`` went red on a file the agent had done
    nothing to.
    """

    GOAL = (
        "<!-- check\n"
        "id: a-goal\n"
        "when: turn() >= 1\n"
        "require: metric(wonders) >= 1\n"
        "once: true\n"
        "message: x\n"
        "-->\n"
    )

    def test_write_checks_leaves_no_bom(self, tmp_path):
        path = tmp_path / "turn-checks.md"
        assert turn_checks.write_checks(path, "# Checks\n")
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")

    def test_write_checks_does_not_translate_line_endings(self, tmp_path):
        """`Path.write_text` defaults to text mode, which turns every ``\\n`` into ``os.linesep``.

        Measured on the live branch: one prune rewrote all 397 lines of the rule file as CRLF on
        Windows, so the commit's diff was the whole document and `git blame` on the file the rules
        live in was destroyed in a single write. The repository stores this file as LF.
        """
        path = tmp_path / "turn-checks.md"
        assert turn_checks.write_checks(path, "# Checks\n\nline\n")
        assert b"\r" not in path.read_bytes()

    def test_the_backup_copy_does_not_translate_line_endings_either(self, tmp_path):
        (tmp_path / "archive").mkdir(parents=True, exist_ok=True)
        path = tmp_path / "turn-checks.md"
        path.write_bytes(b"# Checks\n\n" + self.GOAL.encode("utf-8"))
        removed, backup = turn_checks.sweep_achieved(
            path, {"a-goal": 116}, "20260101-000000", "china_A"
        )
        assert removed == ["a-goal"] and backup is not None
        assert b"\r" not in backup.read_bytes()

    def test_a_bom_that_is_already_there_is_not_carried_forward(self, tmp_path):
        path = tmp_path / "turn-checks.md"
        path.write_bytes(b"\xef\xbb\xbf# Checks\n")
        text, _ = turn_checks.load_checks(path)
        assert text == "# Checks\n", "the read tolerates a BOM either way"
        turn_checks.write_checks(path, text)
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")

    def test_the_sweep_that_retires_a_goal_leaves_no_bom(self, tmp_path):
        (tmp_path / "archive").mkdir(parents=True, exist_ok=True)
        path = tmp_path / "turn-checks.md"
        path.write_bytes(b"\xef\xbb\xbf# Checks\n\n" + self.GOAL.encode("utf-8"))
        removed, _ = turn_checks.sweep_achieved(
            path, {"a-goal": 116}, "20260101-000000", "china_A"
        )
        assert removed == ["a-goal"]
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf"), (
            "the live rule file must stay pure ASCII"
        )
