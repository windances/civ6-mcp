"""Rolling the temporary-task state back with the game: the rules and the file moves.

The gap these tests pin, measured 2026-09-28: `scripts/rollback-to-turn.py` restored the archived
saves, split the diary and un-retired `once: true` goals - and did nothing about the task files, so a
rollback from T301 to T218 left `024-take-brussels` in `done/` while 布鲁塞尔 was an independent
city-state again and the human's instruction was carried by nobody. A task retired *after* the boundary
recorded a `done when:` the rollback has just un-done; a task *added* after it came from the human and
is kept, with the turn its deadline was counted from reported so the deadline is re-counted rather than
trusted.

The fixture is built under the checkout's `.tmp/` rather than pytest's `tmp_path`, for the reason
`test_temp_tasks.py` records: this sandbox refuses to create or remove `.pytest-tmp`. Nothing here
touches the live task files.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import task_rollback as tr  # noqa: E402

SCRATCH = ROOT / ".tmp" / "task-rollback-fixture"

AGENTS_STUB = """# Reference

**IN FORCE NOW:** `023-dutch-siege-corps.md` (take every Dutch city).

More prose.
"""

REGISTER_STUB = """# The live register

| task file | added | expires | why it exists, in one line | done when (first line) |
|---|---|---|---|---|

Task 009 was retired as `done/009-old-done-T100.md`.
"""

TASK_023 = """# TEMP TASK 023 - the Dutch campaign

added:     2026-09-28 (human instruction: 消灭荷兰)
expires:   turn 280 - fifty-four turns from T226, where this branch stands (read from the heartbeat)
done when: **the Netherlands holds no city.** Read `get_diplomacy` for 荷兰.
overrides: nothing
scope:     every Dutch city
"""

TASK_020 = """# TEMP TASK 020 - take Brussels

added:     2026-09-27 (human instruction: 占领布鲁塞尔)
expires:   turn 245 - from T228, the turn the match stands on
done when: **Brussels is ours** - the tile reads [CITY_CENTER] owned by 中国.
overrides: the city-state rule
scope:     布鲁塞尔
"""

TASK_009 = """# TEMP TASK 009 - an earlier objective

added:     2026-09-20 (human instruction: 旧的指令)
expires:   turn 120 - from T90, the turn the match stands on
done when: **the camp is cleared** - the tile reads no camp.
overrides: nothing
scope:     the camp
"""


@pytest.fixture()
def scratch() -> pathlib.Path:
    """A checkout with two retired tasks (one before the boundary, one after) and one in force."""
    shutil.rmtree(SCRATCH, ignore_errors=True)
    tmp = SCRATCH / "prompts" / "tasks" / "tmp"
    done = tmp / "done"
    done.mkdir(parents=True)
    (SCRATCH / ".civ6-mcp-data").mkdir(parents=True)
    (SCRATCH / "AGENTS.md").write_bytes(AGENTS_STUB.encode("utf-8"))
    (tmp / "README.md").write_text("# not a task\n", encoding="utf-8")
    (tmp / "current_tasks.md").write_bytes(REGISTER_STUB.encode("utf-8"))
    (tmp / "023-dutch-siege-corps.md").write_bytes(TASK_023.encode("utf-8"))
    (done / "020-take-brussels-done-T237.md").write_bytes(TASK_020.encode("utf-8"))
    (done / "009-an-earlier-objective-done-T100.md").write_bytes(TASK_009.encode("utf-8"))
    return SCRATCH


def in_force(root: pathlib.Path) -> set[str]:
    tmp = tr.tt.root_paths(root)[0]
    return {path.name for path in tr.tt.task_files(tmp)}


def listed(root: pathlib.Path) -> set[str]:
    agents = tr.tt.root_paths(root)[3]
    return tr.tt.in_force_names(tr.tt.read_text(agents))


class TestWhatTheBoundaryImplies:
    def test_a_task_retired_after_the_boundary_is_restored(self, scratch):
        plan = tr.build_plan(scratch, 218)
        assert [task.name for task in plan.restores] == ["020-take-brussels.md"]
        assert plan.restores[0].retired_at == 237
        assert plan.restores[0].anchor == 228

    def test_a_task_retired_before_the_boundary_is_left_alone(self, scratch):
        plan = tr.build_plan(scratch, 218)
        assert "009-an-earlier-objective.md" not in [task.name for task in plan.restores]
        assert "009-an-earlier-objective.md" in [task.name for task in plan.unchanged]

    def test_a_task_added_after_the_boundary_is_kept_and_reported(self, scratch):
        plan = tr.build_plan(scratch, 218)
        assert [task.name for task in plan.added_after] == ["023-dutch-siege-corps.md"]
        assert plan.added_after[0].anchor == 226

    def test_a_task_with_no_anchor_is_reported_rather_than_assumed(self, scratch):
        (scratch / "prompts" / "tasks" / "tmp" / "024-no-anchor.md").write_text(
            "# TEMP TASK 024\n\nadded: 2026-09-28\nexpires: soon\ndone when: it is done\nowner: me\n",
            encoding="utf-8",
        )
        plan = tr.build_plan(scratch, 218)
        assert [task.name for task in plan.unknown_anchor] == ["024-no-anchor.md"]

    def test_two_restores_sharing_a_done_when_are_reported_as_an_overlap(self, scratch):
        done = tr.tt.root_paths(scratch)[1]
        (done / "024-take-brussels-done-T224.md").write_bytes(TASK_020.replace("020", "024").encode())
        plan = tr.build_plan(scratch, 218)
        assert plan.overlaps() == [("020-take-brussels.md", "024-take-brussels.md")]


class TestTheApply:
    def test_the_file_moves_back_and_both_lists_follow(self, scratch):
        report = tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        assert [name for name, _, _ in report.restored] == ["020-take-brussels.md"]
        assert in_force(scratch) == {"020-take-brussels.md", "023-dutch-siege-corps.md"}
        assert listed(scratch) == in_force(scratch)
        rows = tr.tt.register_rows(tr.tt.read_text(tr.tt.root_paths(scratch)[2]))
        row = next(row for row in rows if row["file"] == "020-take-brussels.md")
        # The stop is T245; T228 is only the turn the deadline was counted from.
        assert row["expires"] == "turn 245"
        assert row["added"] == "2026-09-27"
        assert row["why"].isascii() and not tr.tt.stray_coordinates(row["why"])
        assert any("verified" in note for note in report.notes)

    def test_the_register_records_the_rollback(self, scratch):
        tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        register = tr.tt.read_text(tr.tt.root_paths(scratch)[2])
        assert "Task 020 was restored by the rollback to T218" in register
        assert "it was retired at T237" in register

    def test_the_backup_holds_every_file_it_touched(self, scratch):
        report = tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        assert report.backup is not None
        names = {path.name for path in report.backup.iterdir()}
        assert {"current_tasks.md", "AGENTS.md", "020-take-brussels-done-T237.md"} <= names

    def test_a_kept_task_stays_in_force(self, scratch):
        tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        assert "023-dutch-siege-corps.md" in in_force(scratch)
        assert "023-dutch-siege-corps.md" in listed(scratch)

    def test_strict_drops_a_task_added_after_the_boundary(self, scratch):
        report = tr.apply_plan(scratch, tr.build_plan(scratch, 218), strict=True)
        assert report.dropped == ["023-dutch-siege-corps.md"]
        assert in_force(scratch) == {"020-take-brussels.md"}
        assert listed(scratch) == in_force(scratch)

    def test_skip_leaves_one_of_two_sharing_an_objective_retired(self, scratch):
        done = tr.tt.root_paths(scratch)[1]
        (done / "024-take-brussels-done-T224.md").write_bytes(TASK_020.replace("020", "024").encode())
        report = tr.apply_plan(scratch, tr.build_plan(scratch, 218), skip={"020"})
        assert [name for name, _, _ in report.restored] == ["024-take-brussels.md"]
        assert report.skipped == ["020-take-brussels.md"]

    def test_nothing_to_change_writes_nothing(self, scratch):
        agents = tr.tt.root_paths(scratch)[3]
        before = agents.read_bytes()
        # A boundary at or after every retirement turn: the state at that turn is the state on disk.
        report = tr.apply_plan(scratch, tr.build_plan(scratch, 300))
        assert report.restored == [] and report.backup is None
        assert agents.read_bytes() == before
        assert "nothing to change" in report.notes[0]

    def test_applying_twice_changes_nothing_the_second_time(self, scratch):
        tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        agents = tr.tt.root_paths(scratch)[3].read_bytes()
        register = tr.tt.root_paths(scratch)[2].read_bytes()
        second = tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        assert second.restored == [] and second.backup is None
        assert tr.tt.root_paths(scratch)[3].read_bytes() == agents
        assert tr.tt.root_paths(scratch)[2].read_bytes() == register


class TestTheWhyForARestoredTask:
    def test_a_utf8_git_child_is_decoded_as_utf8(self, tmp_path):
        """`text=True` alone decodes with the locale code page, and git does not write that.

        The first real use of this module died here: `git log -p` output holding a Chinese commit
        subject raised UnicodeDecodeError in the reader thread, `stdout` came back None, and the
        recovery of a restored task's blurb crashed instead of falling back.

        The commit is **made here** rather than looked for in this checkout's history: the earlier
        version needed a non-ASCII subject among the last fifty commits, which a run of English commit
        messages quietly removed - the test then failed on its own premise (2026-09-29) instead of on the
        decoding it exists to pin.
        """
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True, capture_output=True)
        (repo / "f.txt").write_text("x", encoding="utf-8")
        subject = "任务 031：军事生产实验的第二次尝试"
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", subject], cwd=repo, check=True, capture_output=True)

        subjects = tr._git(repo, ["log", "-1", "--format=%s"])
        assert subjects is not None, "git should answer in a repository with one commit"
        assert subject in subjects, "the Chinese subject came back mangled - the child is not decoding UTF-8"

    def test_the_real_history_row_is_what_the_fallback_exists_for(self):
        """The row 024 was actually added with names its target's tile, so it cannot travel.

        Recovering it verbatim would write "(69,29)" back into `AGENTS.md` - the exact coordinate that
        took `tests/test_agents_is_game_agnostic.py` red and was repaired out of the reference and the
        register the same day. So this asserts the trap is real, not that the history is clean.
        """
        why = tr.why_from_git(ROOT, "024-take-brussels.md")
        assert why, "the register's history should hold the row 024 was added with"
        assert not tr.why_is_usable(why)
        assert tr.tt.stray_coordinates(why)

    def test_a_recovered_blurb_that_cannot_travel_falls_back(self, scratch, monkeypatch):
        monkeypatch.setattr(tr, "why_from_git", lambda root, name: "take the city-state at (69,29)")
        report = tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        assert [name for name, _, _ in report.restored] == ["020-take-brussels.md"]
        row = next(
            row for row in tr.tt.register_rows(tr.tt.read_text(tr.tt.root_paths(scratch)[2]))
            if row["file"] == "020-take-brussels.md"
        )
        assert tr.why_is_usable(row["why"]), row["why"]

    def test_a_recovered_blurb_with_a_turn_reference_falls_back(self, scratch, monkeypatch):
        """A blurb that reads `(T220: 32% of the map explored)` must not reach `AGENTS.md`.

        Measured 2026-09-28: restoring task 019 from the register's history put a bare `T220` into the
        `IN FORCE NOW` line, and `tests/test_agents_is_game_agnostic.py` counts those in prose against a
        budget of four - the restore turned the suite red one turn after the rollback that did it.
        """
        monkeypatch.setattr(
            tr, "why_from_git", lambda root, name: "scouts to sea (T220: a third of the map explored)"
        )
        report = tr.apply_plan(scratch, tr.build_plan(scratch, 218))
        assert [name for name, _, _ in report.restored] == ["020-take-brussels.md"]
        row = next(
            row for row in tr.tt.register_rows(tr.tt.read_text(tr.tt.root_paths(scratch)[2]))
            if row["file"] == "020-take-brussels.md"
        )
        assert "T220" not in row["why"]
        assert not tr._TURN_REF.search(row["why"])

    def test_an_override_that_cannot_travel_is_refused_before_any_move(self, scratch):
        agents = tr.tt.root_paths(scratch)[3].read_bytes()
        report = tr.apply_plan(
            scratch, tr.build_plan(scratch, 218), overrides={"020": "take the city at (69,29)"}
        )
        assert report.restored == [] and report.backup is None
        assert any("refused" in note for note in report.notes)
        assert in_force(scratch) == {"023-dutch-siege-corps.md"}
        assert tr.tt.root_paths(scratch)[3].read_bytes() == agents

    def test_history_supplies_the_last_known_blurb(self):
        diff = (
            "diff --git a/x b/x\n"
            "+| `020-take-brussels.md` | 2026-09-27 | turn 245 | take the city-state | **ours** |\n"
            "some other line\n"
            "+| `020-take-brussels.md` | 2026-09-27 | turn 246 | take the city-state, re-counted | **ours** |\n"
        )
        assert tr.why_from_history(diff, "020-take-brussels.md") == "take the city-state, re-counted"
        assert tr.why_from_history(diff, "021-nothing.md") is None

    def test_an_override_wins(self, scratch):
        task = tr.build_plan(scratch, 218).restores[0]
        why, source = tr.resolve_why(scratch, task, 218, {"020": "take Brussels, on the instruction"})
        assert (why, source) == ("take Brussels, on the instruction", "override")

    def test_the_blurb_is_english_and_carries_no_coordinate(self, scratch):
        task = tr.build_plan(scratch, 218).restores[0]
        why, source = tr.resolve_why(scratch, task, 218, {"020": "take Brussels, on the instruction"})
        assert source == "override"
        assert why.isascii() and tr.tt.stray_coordinates(why) == []
        assert tr.derived_why(task, 218).isascii()
        assert tr.tt.stray_coordinates(tr.derived_why(task, 218)) == []
        # A slug is the only English in a file name, so a proper noun has to be capitalised.
        assert tr.derived_why(task, 218).startswith("take Brussels")


class TestTheCommandLine:
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / ".tools" / "rollback-tasks.py"), *args],
            cwd=str(ROOT), capture_output=True, text=True, timeout=180,
        )

    def test_plan_only_writes_nothing(self, scratch):
        done = self._run("218", "--root", str(scratch))
        assert done.returncode == 0, done.stdout + done.stderr
        assert "to restore          1" in done.stdout
        assert "plan only" in done.stdout
        assert in_force(scratch) == {"023-dutch-siege-corps.md"}

    def test_apply_restores_and_reports_the_backup(self, scratch):
        done = self._run("218", "--root", str(scratch), "--apply")
        assert done.returncode == 0, done.stdout + done.stderr
        assert "restored      020-take-brussels.md" in done.stdout
        assert "backup        .civ6-mcp-data" in done.stdout
        assert in_force(scratch) == {"020-take-brussels.md", "023-dutch-siege-corps.md"}
