"""An achieved goal is taken out of the live check file, with a timestamped copy first.

Retirement (see test_turn_check_retirement) makes a done goal stop nagging, but it stays in
the file, so the file the agent reads at the start of every turn keeps listing work that is
finished - and the whole point of the file is that everything in it still needs doing. At the
end of a turn the achieved goals are removed from it; the file as it was is kept under
`archive/` with a timestamp so the history of the directive stays readable and comparable.

The removal is a pure text edit plus a file write: the backup is written before the live file
is touched, and a second sweep finds nothing to do.
"""

from __future__ import annotations

import pathlib
import sys
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


@pytest.fixture()
def scratch(monkeypatch):
    """A workspace scratch dir for the check file and the retirement state file.

    mkdtemp/tmp_path are not writable in this sandbox, and the retirement state is written
    into CIV_MCP_DATA_DIR, so both are redirected here.
    """
    root = pathlib.Path(".tools") / f"_check_prune_{uuid.uuid4().hex}"
    checks_dir = root / "checks"
    checks_dir.mkdir(parents=True)
    data_dir = root / "data"
    data_dir.mkdir()
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data_dir))
    yield checks_dir
    import shutil

    shutil.rmtree(root, ignore_errors=True)


GOAL_FILE = """# Turn checks

Prose that explains the rules. It is hand-written and must survive the sweep.

<!-- check
id: build-a-ram
once: true
require: units(BATTERING_RAM) >= 1
message: Build a Battering Ram before CIVIC_CIVIL_ENGINEERING obsoletes it.
-->

<!-- check
id: keep-slots-filled
require: metric(districts) >= metric(pop) // 3
message: Fill the district slots.
-->

Closing prose.
"""


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


def context(**metrics) -> turn_checks.CheckContext:
    base = {"wonders": 0, "districts": 0, "pop": 3, "improvements": 9, "cities": 3}
    base.update(metrics)
    return turn_checks.CheckContext(turn=60, units={}, metrics=base, researched=frozenset())


class TestRemoveAchieved:
    def test_the_block_goes_and_a_trace_stays(self):
        out, removed = turn_checks.remove_achieved(
            GOAL_FILE, {"build-a-ram": 61}, "20260921-101500", "archive/turn-checks-x.md"
        )
        assert removed == ["build-a-ram"]
        assert "units(BATTERING_RAM)" not in out, "the rule is gone, not just ignored"
        assert "achieved T61: build-a-ram" in out
        assert "archive/turn-checks-x.md" in out, "the trace says where the original is"

    def test_the_prose_is_not_this_functions_to_delete(self):
        out, _ = turn_checks.remove_achieved(GOAL_FILE, {"build-a-ram": 61}, "s", "n")
        assert "Prose that explains the rules" in out
        assert "Closing prose." in out
        assert out.startswith("# Turn checks")

    def test_standing_rules_are_left_alone(self):
        out, removed = turn_checks.remove_achieved(GOAL_FILE, {"build-a-ram": 61}, "s", "n")
        assert "keep-slots-filled" in out
        assert "build-a-ram" not in {c.check_id for c in turn_checks.parse_checks(out)}

    def test_the_trace_is_not_parsed_as_a_rule(self):
        # A leftover comment that looked like a check block would be reported as malformed.
        out, _ = turn_checks.remove_achieved(GOAL_FILE, {"build-a-ram": 61}, "s", "n")
        assert turn_checks.parse_checks(out)[0].check_id == "keep-slots-filled"

    def test_nothing_achieved_changes_nothing(self):
        out, removed = turn_checks.remove_achieved(GOAL_FILE, {}, "s", "n")
        assert removed == []
        assert out == GOAL_FILE

    def test_an_unknown_id_changes_nothing(self):
        out, removed = turn_checks.remove_achieved(GOAL_FILE, {"never-existed": 61}, "s", "n")
        assert removed == []
        assert out == GOAL_FILE

    def test_the_blank_line_left_behind_is_collapsed(self):
        out, _ = turn_checks.remove_achieved(GOAL_FILE, {"build-a-ram": 61}, "s", "n")
        assert "\n\n\n" not in out

    @pytest.mark.parametrize("archive_note", ["", "archive/turn-checks-20260921.md"])
    def test_the_trace_reads_well_with_and_without_an_archive(self, archive_note):
        out, _ = turn_checks.remove_achieved(GOAL_FILE, {"build-a-ram": 61}, "s", archive_note)
        trace = next(line for line in out.splitlines() if "achieved T61" in line)
        assert trace.startswith("<!--") and trace.endswith("-->")
        assert ("original in" in trace) is bool(archive_note)

    def test_a_done_goal_is_no_longer_evaluated(self):
        # The point of removing it: a rule that cannot be satisfied again cannot fire again.
        out, _ = turn_checks.remove_achieved(GOAL_FILE, {"build-a-ram": 61}, "s", "n")
        run = turn_checks.run_checks(out, context(districts=9, pop=3))
        assert run.passed == {"keep-slots-filled"}
        assert run.failing_ids == set()


class TestSweep:
    def test_the_backup_holds_the_file_as_it_was(self, scratch):
        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")

        removed, backup = turn_checks.sweep_achieved(path, {"build-a-ram": 61}, "20260921-101500")

        assert removed == ["build-a-ram"]
        assert backup == scratch / "archive" / "turn-checks-20260921-101500.md"
        assert backup.read_text(encoding="utf-8") == GOAL_FILE, "the copy is pre-edit"
        assert "units(BATTERING_RAM)" not in path.read_text(encoding="utf-8")

    def test_the_edit_is_atomic_and_leaves_no_temp_file(self, scratch):
        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        turn_checks.sweep_achieved(path, {"build-a-ram": 61}, "stamp")
        assert not list(scratch.glob("*.tmp"))

    def test_a_second_sweep_does_nothing(self, scratch):
        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        turn_checks.sweep_achieved(path, {"build-a-ram": 61}, "stamp")
        after_first = path.read_text(encoding="utf-8")

        removed, backup = turn_checks.sweep_achieved(path, {"build-a-ram": 61}, "later-stamp")

        assert removed == []
        assert backup is None, "no second backup for a file that changed nothing"
        assert path.read_text(encoding="utf-8") == after_first

    def test_only_the_first_sweep_writes_a_backup(self, scratch):
        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        turn_checks.sweep_achieved(path, {"build-a-ram": 61}, "stamp")
        turn_checks.sweep_achieved(path, {"build-a-ram": 61}, "later-stamp")
        assert [p.name for p in (scratch / "archive").iterdir()] == [
            "turn-checks-stamp.md"
        ]

    def test_nothing_achieved_writes_nothing(self, scratch):
        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        removed, backup = turn_checks.sweep_achieved(path, {}, "stamp")
        assert (removed, backup) == ([], None)
        assert path.read_text(encoding="utf-8") == GOAL_FILE
        assert not (scratch / "archive").exists()

    def test_a_missing_file_is_not_an_error(self, scratch):
        removed, backup = turn_checks.sweep_achieved(scratch / "absent.md", {"x": 1}, "stamp")
        assert (removed, backup) == ([], None)

    def test_two_goals_in_one_sweep(self, scratch):
        path = scratch / "turn-checks.md"
        text = GOAL_FILE.replace("id: keep-slots-filled", "id: fill-slots\nonce: true")
        path.write_text(text, encoding="utf-8")

        removed, backup = turn_checks.sweep_achieved(
            path, {"build-a-ram": 61, "fill-slots": 61}, "stamp"
        )

        assert sorted(removed) == ["build-a-ram", "fill-slots"]
        left = path.read_text(encoding="utf-8")
        assert turn_checks.parse_checks(left) == []
        assert "Prose that explains the rules" in left

    def test_the_archive_sits_beside_the_checks_not_in_the_data_dir(self, scratch):
        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        _, backup = turn_checks.sweep_achieved(path, {"build-a-ram": 61}, "stamp")
        assert backup.parent.parent == scratch


async def _no_rows():
    return []


class TestTheHookSweeps:
    """`end_turn` is where the sweep belongs: the goal is achieved *by* the turn that just ran."""

    def _gs(self, units: dict, turn: int = 61):
        class Snap:
            def __init__(self):
                self.turn = turn
                self.units = units

        class GS:
            def __init__(self):
                self._last_snapshot = Snap()
                self._briefing_turn = None

            async def get_game_identity(self):
                return ("china", -1894041591)

            async def _take_snapshot(self):
                return self._last_snapshot

        return GS()

    def _wire(self, monkeypatch, path: pathlib.Path):
        from civ_mcp import end_turn as et

        monkeypatch.setattr(et, "_agent_diary_rows", lambda gs: _no_rows())
        # end_turn imports turn_checks inside the function, so patch the module itself.
        monkeypatch.setattr(turn_checks, "load_checks", lambda p=None: (path.read_text(encoding="utf-8"), path))
        return et

    def test_the_turn_that_achieves_a_goal_prunes_it_and_says_so(self, scratch, monkeypatch):
        import asyncio

        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        et = self._wire(monkeypatch, path)
        gs = self._gs({1: unit(1, "UNIT_BATTERING_RAM")})
        monkeypatch.setattr(
            et, "_latest_at_or_before", lambda rows, turn: {"pop": 3, "districts": 0}
        )

        events = asyncio.run(et._check_turn_checks(gs, 61, gs._last_snapshot.units, None))
        messages = [e.message for e in events]

        assert any("CHECK ACHIEVED [build-a-ram]" in msg for msg in messages)
        pruned = next(msg for msg in messages if "CHECK FILE PRUNED" in msg)
        assert "build-a-ram" in pruned and "archive" in pruned
        assert turn_checks.load_retired("china_-1894041591") == {"build-a-ram": 61}

        left = path.read_text(encoding="utf-8")
        assert "units(BATTERING_RAM)" not in left
        assert "keep-slots-filled" in left, "the rule that still fails is still in the file"
        assert list((scratch / "archive").glob("turn-checks-*.md"))

    def test_a_pruned_file_does_not_report_itself_broken(self, scratch, monkeypatch):
        import asyncio

        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        et = self._wire(monkeypatch, path)
        gs = self._gs({1: unit(1, "UNIT_BATTERING_RAM")})
        monkeypatch.setattr(
            et, "_latest_at_or_before", lambda rows, turn: {"pop": 3, "districts": 0}
        )

        asyncio.run(et._check_turn_checks(gs, 61, gs._last_snapshot.units, None))
        second = asyncio.run(et._check_turn_checks(gs, 62, gs._last_snapshot.units, None))
        messages = [e.message for e in second]

        assert not any("BROKEN" in msg for msg in messages), messages
        assert not any("PRUNED" in msg for msg in messages), "no second sweep to report"
        assert any("CHECK FAILED [keep-slots-filled]" in msg for msg in messages)

    def test_the_briefing_after_the_sweep_agrees_with_the_file(self, scratch, monkeypatch):
        import asyncio

        path = scratch / "turn-checks.md"
        path.write_text(GOAL_FILE, encoding="utf-8")
        et = self._wire(monkeypatch, path)
        gs = self._gs({1: unit(1, "UNIT_BATTERING_RAM")})
        monkeypatch.setattr(
            et, "_latest_at_or_before", lambda rows, turn: {"pop": 3, "districts": 0}
        )

        asyncio.run(et._check_turn_checks(gs, 61, gs._last_snapshot.units, None))
        gs._briefing_turn = None
        briefing = asyncio.run(et.turn_start_briefing(gs, 62))

        assert "build-a-ram" not in briefing, "it is out of the file, so out of the briefing"
        assert "[keep-slots-filled]" in briefing
