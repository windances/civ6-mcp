"""Forgetting this match's past, without forgetting anybody else's.

`fresh-start.py` is the deliberate opposite of `rollback-to-turn.py`: a rollback restores the past
so a replayed branch makes sense, and this forgets the past so the loaded position is played on with
no memory of how it got there. Two things are easy to get wrong and expensive when wrong:

  1. **The check file is shared by every match played from this checkout.** Cutting every
     `achieved T...` trace would withdraw rules another match has already met - so only this match's
     traces go, and an un-keyed trace counts as this match's, exactly as
     `turn_checks.restore_foreign_games` reads it.
  2. **A session that is still playing rewrites everything.** The wipe has to refuse while one is
     live, or the diary comes back within one turn and the operator believes it worked.

Everything forgotten is copied first, so the operation is reversible.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "src"))

KEY = "china_-1894041591"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "fresh_start", ROOT / "scripts" / "fresh-start.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["fresh_start"] = module
    spec.loader.exec_module(module)
    return module


fs = load_module()


# --- the achieved notes, which is the part that can silently damage another match -----------------

CHECKS = f"""# Turn checks

<!-- achieved T99: ram-tower-before-civil-engineering (original in archive/turn-checks-20260926-012524.md) -->
<!-- achieved T99: dynasty-cycle-wonder (game: {KEY}) (original in archive/turn-checks-20261003-182343.md) -->
<!-- achieved T120: another-matches-goal (game: rome_12345) (original in archive/turn-checks-20260930-000000.md) -->

### `goal-kept` - a rule body that stays

The body of a rule that has not been achieved, and must survive.
"""

ARCHIVED = {
    "turn-checks-20260926-012524.md": (
        "<!-- check\nid: ram-tower-before-civil-engineering\nwhen: not has_civic('CIVIC_CIVIL_ENGINEERING')\n"
        "-->\nNo ram, use the Catapult: the ram and the tower are out for this match.\n"
    ),
    "turn-checks-20261003-182343.md": (
        "<!-- check\nid: dynasty-cycle-wonder\nwhen: turn() >= 25\n-->\n"
        "Dynastic Cycle wants a wonder; the boost figure is 50%.\n"
    ),
}


def checks_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """The check file plus the archive its traces point at."""
    directory = tmp_path / "prompts" / "checks"
    (directory / "archive").mkdir(parents=True, exist_ok=True)
    for name, text in ARCHIVED.items():
        (directory / "archive" / name).write_text(text, encoding="utf-8")
    return directory


def test_only_this_matches_notes_are_taken_out(tmp_path):
    directory = checks_dir(tmp_path)
    text, turns, ids, foreign = fs.rearm_traces(CHECKS, KEY, directory)
    assert turns == [99, 99], "the un-keyed trace is this match's, and the keyed one is too"
    assert ids == ["ram-tower-before-civil-engineering", "dynasty-cycle-wonder"]
    assert foreign == [120], "another match's trace is left alone"
    assert "another-matches-goal" in text
    assert "<!-- achieved T99" not in text


def test_the_rule_body_comes_back_rather_than_vanishing(tmp_path):
    """A rule cannot be live and absent at once: the check file's own suite asserts it.

    `test_every_retirement_trace_still_resolves_to_its_archived_block` requires traces to be
    non-empty, and `..._wonder_obligation_is_live_or_recoverable` requires the goal to be live or
    traceable - so "forget the achievement" has to mean "the rule is live again".
    """
    directory = checks_dir(tmp_path)
    text, _, _, _ = fs.rearm_traces(CHECKS, KEY, directory)
    assert "id: ram-tower-before-civil-engineering" in text
    assert "id: dynasty-cycle-wonder" in text
    # The block is what `archived_goal_block` returns - the same text `restore_achieved` puts back,
    # so this is the blessed inverse operation and not a second implementation of it.
    assert "when: not has_civic('CIVIC_CIVIL_ENGINEERING')" in text
    assert "### `goal-kept` - a rule body that stays" in text
    assert "The body of a rule that has not been achieved, and must survive." in text
    assert text.count("<!-- achieved T") == 1, "only another match's note is left"


def test_a_note_whose_archive_is_missing_is_left_in_place(tmp_path, capsys):
    """Never silently drop a rule: an unresolvable trace stays, and says so."""
    directory = checks_dir(tmp_path)
    text, turns, ids, _ = fs.rearm_traces(
        f"<!-- achieved T99: gone-goal (game: {KEY}) (original in archive/missing.md) -->\n",
        KEY,
        directory,
    )
    assert (turns, ids) == ([], [])
    assert "gone-goal" in text, "the trace is the only way back, so it stays"
    assert "no block in" in capsys.readouterr().out


def test_prose_that_merely_names_a_trace_is_not_touched(tmp_path):
    """The documentation around `remove_achieved` mentions traces; a mention is not a trace."""
    directory = checks_dir(tmp_path)
    prose = (
        "A retirement trace carries no match key: `achieved T99` for the match key "
        f"`{KEY}`. It is prose, and it stays.\n"
    )
    text, turns, _, _ = fs.rearm_traces(prose, KEY, directory)
    assert turns == []
    assert "It is prose, and it stays." in text


def test_a_file_with_no_trace_is_left_exactly_as_it_was(tmp_path):
    directory = checks_dir(tmp_path)
    text, turns, ids, foreign = fs.rearm_traces("# checks\n\nno traces here\n", KEY, directory)
    assert (text, turns, ids, foreign) == ("# checks\n\nno traces here\n", [], [], [])


# --- a whole fake checkout -----------------------------------------------------------------------

MANIFEST = {
    "run_id": "fake-run-01",
    "label": "",
    "civ": "china",
    "seed": -1894041591,
    "created": "2026-10-01T00:00:00",
    "last_turn": 354,
    "notes": "",
}


def fake_checkout(tmp_path: pathlib.Path, *, live: bool = False) -> pathlib.Path:
    """A miniature of the real tree: the run, the legacy root copies, the checks and the tasks."""
    data = tmp_path / ".civ6-mcp-data"
    run = data / "runs" / "china--1894041591"
    run.mkdir(parents=True)
    (data / "runs" / "current").parent.mkdir(parents=True, exist_ok=True)
    # The pointer lives at the **root**, not under runs/ (`run_manifest.CURRENT_NAME`).
    (data / "current").write_text("china--1894041591", encoding="utf-8")
    (run / "run.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
    for name in (
        f"diary_{KEY}.jsonl",
        f"diary_{KEY}_cities.jsonl",
    ):
        (run / name).write_text(
            '{"turn": 350, "civ": "china"}\n{"turn": 351, "civ": "china"}\n', encoding="utf-8"
        )
        (data / name).write_text('{"turn": 352, "civ": "china"}\n', encoding="utf-8")
    (run / "turn-checks-state.json").write_text(
        json.dumps({KEY: {"dynasty-cycle-wonder": 99}}), encoding="utf-8"
    )
    (data / "turn-checks-state.pre-runs.json").write_text(
        json.dumps({KEY: {"ram-tower-before-civil-engineering": 99}}), encoding="utf-8"
    )
    for name in fs.SCRATCH:
        (run / name).write_text("{}", encoding="utf-8")
    directory = checks_dir(tmp_path)
    (directory / "turn-checks.md").write_text(CHECKS, encoding="utf-8")
    tmp = tmp_path / fs.TASKS_REL
    tmp.mkdir(parents=True)
    (tmp / "044-a-task.md").write_text("added: 2026-10-04\n", encoding="utf-8")
    (tmp / "current_tasks.md").write_text("| task |\n", encoding="utf-8")
    (tmp / "README.md").write_text("read me\n", encoding="utf-8")
    (data / "branches" / "rollback-to-T352-from-T353-T354-x").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def checkout(tmp_path):
    return fake_checkout(tmp_path)


def run_apply(root: pathlib.Path, turn: int = 352, stamp: str = "20261005-000000") -> dict:
    plan = fs.build_plan(root, turn)
    return fs.apply_plan(root, plan, stamp)


class TestThePlan:
    def test_it_lists_the_run_and_the_legacy_diary(self, checkout):
        plan = fs.build_plan(checkout, 352)
        paths = [item["path"] for item in plan["forgets"]]
        assert any("runs\\china--1894041591\\diary_" in p for p in paths), paths
        assert any(p == f".civ6-mcp-data\\diary_{KEY}.jsonl" for p in paths), (
            "the legacy root diary is the same match's memory and is read if the run pointer is lost"
        )
        assert plan["game_key"] == KEY
        assert plan["playing_to"] == 354

    def test_the_register_and_the_readme_are_not_tasks(self, checkout):
        plan = fs.build_plan(checkout, 352)
        assert plan["tasks_in_force"] == ["044-a-task.md"], plan["tasks_in_force"]

    def test_the_achieved_notes_are_reported_as_re_armed(self, checkout):
        plan = fs.build_plan(checkout, 352)
        assert plan["checks_changed"] is True
        assert plan["traces_rearmed"] == [99, 99]
        assert plan["goals_rearmed"] == [
            "ram-tower-before-civil-engineering",
            "dynasty-cycle-wonder",
        ]


class TestTheApply:
    def test_the_diary_and_the_state_are_gone(self, checkout):
        run_apply(checkout)
        data = checkout / ".civ6-mcp-data"
        run = data / "runs" / "china--1894041591"
        assert not (run / f"diary_{KEY}.jsonl").exists()
        assert not (data / f"diary_{KEY}.jsonl").exists(), "the legacy copy goes too"
        assert not (run / "turn-checks-state.json").exists()
        assert not (data / "turn-checks-state.pre-runs.json").exists()
        for name in fs.SCRATCH:
            assert not (run / name).exists(), name

    def test_the_manifest_is_reset_to_the_resumed_turn(self, checkout):
        run_apply(checkout, turn=352)
        run = checkout / ".civ6-mcp-data" / "runs" / "china--1894041591"
        assert json.loads((run / "run.json").read_text(encoding="utf-8"))["last_turn"] == 352

    def test_the_rule_bodies_come_back_and_only_this_matches_notes_go(self, checkout):
        run_apply(checkout)
        text = (checkout / fs.CHECKS_REL).read_text(encoding="utf-8")
        assert "### `goal-kept` - a rule body that stays" in text
        assert "id: ram-tower-before-civil-engineering" in text, (
            "the rule is live again: a goal can be neither live nor absent without breaking the "
            "check file's own contract"
        )
        assert "id: dynasty-cycle-wonder" in text
        assert "<!-- achieved T99" not in text, "this match's achieved notes are gone"
        assert "another-matches-goal" in text, "another match's trace is not ours to touch"

    def test_everything_forgotten_is_in_the_backup_first(self, checkout):
        result = run_apply(checkout)
        backup = result["backup"]
        assert backup.exists() and (backup / "manifest.json").exists()
        data = backup / "files" / ".civ6-mcp-data"
        run_diary = data / "runs" / "china--1894041591" / f"diary_{KEY}.jsonl"
        legacy_diary = data / f"diary_{KEY}.jsonl"
        assert run_diary.exists() and legacy_diary.exists(), (
            "the run-dir copy and the legacy root copy share a file name: the backup has to mirror "
            "the tree, or one silently overwrites the other (measured 2026-10-05 on the real match)"
        )
        assert run_diary.read_text(encoding="utf-8") != legacy_diary.read_text(encoding="utf-8")
        assert (data / "turn-checks-state.pre-runs.json").exists()
        assert (
            backup / "files" / "prompts" / "checks" / "turn-checks-before-20261005-000000.md"
        ).exists()
        written = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        assert written["resume_at"] == 352 and written["played_to_before"] == 354
        assert written["traces_rearmed"] == [99, 99]
        assert written["goals_rearmed"] == [
            "ram-tower-before-civil-engineering",
            "dynasty-cycle-wonder",
        ]
        assert written["tasks_kept"] == ["044-a-task.md"]

    def test_the_archives_are_not_touched(self, checkout):
        run_apply(checkout)
        assert (
            checkout / ".civ6-mcp-data" / "branches" / "rollback-to-T352-from-T353-T354-x"
        ).is_dir(), "the branch archives are the record; a fresh start does not delete them"

    def test_the_tasks_in_force_are_kept_and_only_reported(self, checkout):
        run_apply(checkout)
        tmp = checkout / fs.TASKS_REL
        assert (tmp / "044-a-task.md").exists(), (
            "withdrawing an instruction silently is the failure this repository keeps re-learning: "
            "the task stays, and the plan prints the retire command"
        )
        plan = fs.build_plan(checkout, 352)
        assert plan["tasks_in_force"] == ["044-a-task.md"]


class TestTheRefusal:
    def test_it_refuses_while_a_session_is_live(self, checkout, monkeypatch, capsys):
        monkeypatch.setattr(fs, "session_live", lambda run: (True, "heartbeat: pid 1 alive"))
        monkeypatch.setattr(sys, "argv", ["fresh-start.py", "352", "--apply"])
        assert fs.main(checkout) == 2
        out = capsys.readouterr().out
        assert "refusing" in out and "stop-agent.py" in out
        run = checkout / ".civ6-mcp-data" / "runs" / "china--1894041591"
        assert (run / f"diary_{KEY}.jsonl").exists(), "a refused run must not have forgotten anything"

    def test_force_forgets_anyway(self, checkout, monkeypatch, capsys):
        monkeypatch.setattr(fs, "session_live", lambda run: (True, "heartbeat: pid 1 alive"))
        monkeypatch.setattr(sys, "argv", ["fresh-start.py", "352", "--apply", "--force"])
        assert fs.main(checkout) == 0
        run = checkout / ".civ6-mcp-data" / "runs" / "china--1894041591"
        assert not (run / f"diary_{KEY}.jsonl").exists()

    def test_a_plan_run_changes_nothing(self, checkout, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["fresh-start.py", "352"])
        assert fs.main(checkout) == 0
        run = checkout / ".civ6-mcp-data" / "runs" / "china--1894041591"
        assert (run / f"diary_{KEY}.jsonl").exists()
        assert "plan only" in capsys.readouterr().out

    def test_main_defaults_to_the_checkout_root_and_is_never_given_it_by_accident(
        self, checkout, monkeypatch, capsys
    ):
        """The tests must not be able to wipe the real tree: `main` takes its root as an argument.

        Measured while writing this file: the first version of these tests called `fs.main()` with
        no argument, and the `--force` case forgot the *real* match's diary while pretending to test
        a temporary one. The default is still the checkout (the CLI needs it), so the guard is here:
        a test that wants a tree it owns has to say so.
        """
        assert fs.main.__defaults__ == (None,)
        monkeypatch.setattr(sys, "argv", ["fresh-start.py", "352"])
        assert fs.main(checkout) == 0
        assert "plan only" in capsys.readouterr().out
        assert fs.ROOT != checkout
