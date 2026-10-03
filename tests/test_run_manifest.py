"""The run manifest: naming a playthrough, and catching the game being swapped underneath one.

The failure this exists for is measured, not hypothetical. On 2026-10-03 a session played turn after
turn against a data directory belonging to `china_911679432` while the loaded game had become
`china_-1894041591`. Every read succeeded; every line looked normal. Nothing in the tooling compared
the game to an expectation, because no expectation existed - `{civ}_{seed}` was derived from the game
rather than asserted against it.

So the tests here are mostly about *disagreement*: the point is not to describe a run, it is to say
loudly when the game is not the run.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import run_manifest as rm  # noqa: E402
from civ_mcp import session_info  # noqa: E402


@pytest.fixture
def data(tmp_path):
    return tmp_path


class TestTheManifest:
    def test_an_unnamed_directory_has_none(self, data):
        assert rm.load(data) is None

    def test_init_writes_what_the_run_expects(self, data):
        manifest, message = rm.init("china-a", "A line", "china", 911679432, data_dir=data)
        assert message == "written"
        assert manifest["run_id"] == "china-a"
        assert rm.load(data)["seed"] == 911679432

    def test_a_label_defaults_to_the_id(self, data):
        manifest, _ = rm.init("china-a", data_dir=data)
        assert manifest["label"] == "china-a"

    def test_init_refuses_to_rename_an_existing_run(self, data):
        rm.init("china-a", data_dir=data)
        manifest, message = rm.init("china-b", data_dir=data)
        assert manifest["run_id"] == "china-a" and "refused" in message

    def test_replace_renames_it_and_keeps_the_progress(self, data):
        rm.init("china-a", data_dir=data)
        rm.touch(116, data_dir=data)
        manifest, message = rm.init("china-b", data_dir=data, replace=True)
        assert message == "written"
        assert manifest["run_id"] == "china-b" and manifest["last_turn"] == 116, (
            "renaming a run must not lose how far it has been played"
        )

    def test_a_corrupt_manifest_reads_as_unnamed(self, data):
        (pathlib.Path(data) / rm.MANIFEST_NAME).write_text("{not json", encoding="utf-8")
        assert rm.load(data) is None

    def test_touch_only_moves_forward(self, data):
        rm.init("china-a", data_dir=data)
        rm.touch(120, data_dir=data)
        rm.touch(90, data_dir=data)
        assert rm.load(data)["last_turn"] == 120

    def test_touch_without_a_manifest_is_a_no_op(self, data):
        assert rm.touch(120, data_dir=data) is None

    def test_reset_turn_moves_the_manifest_backwards(self, data):
        """A rollback is the one thing that genuinely goes back, so `touch` cannot express it."""
        rm.init("china-a", data_dir=data)
        rm.touch(116, data_dir=data)
        rm.reset_turn(59, data_dir=data)
        assert rm.load(data)["last_turn"] == 59

    def test_reset_turn_is_not_limited_to_going_back(self, data):
        """It sets the value; the forward-only rule belongs to `touch`, not to this."""
        rm.init("china-a", data_dir=data)
        rm.reset_turn(59, data_dir=data)
        rm.reset_turn(60, data_dir=data)
        assert rm.load(data)["last_turn"] == 60

    def test_reset_turn_without_a_manifest_is_a_no_op(self, data):
        assert rm.reset_turn(59, data_dir=data) is None


class TestVerification:
    def test_no_manifest_is_not_a_mismatch(self):
        """An unnamed directory must keep working: this is opt-in, like the localization table."""
        state, _ = rm.verify(None, "china", 911679432)
        assert state == "unset"

    def test_matching_identity_is_ok(self):
        state, _ = rm.verify(rm.make("china-a", civ="china", seed=911679432), "china", 911679432)
        assert state == "ok"

    def test_a_different_seed_is_a_mismatch(self):
        state, detail = rm.verify(
            rm.make("china-a", civ="china", seed=911679432), "china", -1894041591
        )
        assert state == "mismatch" and "911679432" in detail and "-1894041591" in detail

    def test_a_different_civ_is_a_mismatch(self):
        state, _ = rm.verify(rm.make("china-a", civ="china", seed=1), "rome", 1)
        assert state == "mismatch"

    def test_a_manifest_with_no_identity_says_so_rather_than_passing(self):
        state, detail = rm.verify(rm.make("china-a"), "china", 911679432)
        assert state == "unnamed" and "no civ/seed" in detail


class TestResolvingTheRunDirectory:
    """`CIV_MCP_DATA_DIR` points at the root; the modules must be pointed at the run inside it.

    The resolution has to happen *before* the modules import, because `diary.DIARY_DIR`,
    `heartbeat.HEARTBEAT_PATH` and `turn_checks.state_path` read the variable at import time. That
    is why it lives in the drivers' bootstrap and not inside those modules.
    """

    def test_a_flat_directory_is_returned_unchanged(self, tmp_path):
        """A checkout that has not been migrated must behave exactly as before."""
        (tmp_path / "diary_china_1.jsonl").write_text("{}\n", encoding="utf-8")
        assert rm.resolve_data_dir(tmp_path) == tmp_path

    def test_the_pointer_selects_the_run(self, tmp_path):
        (tmp_path / "runs" / "run-a").mkdir(parents=True)
        (tmp_path / "runs" / "run-b").mkdir(parents=True)
        (tmp_path / "current").write_text("run-b\n", encoding="utf-8")
        assert rm.resolve_data_dir(tmp_path) == tmp_path / "runs" / "run-b"

    def test_no_pointer_falls_back_to_the_root(self, tmp_path):
        (tmp_path / "runs" / "run-a").mkdir(parents=True)
        assert rm.resolve_data_dir(tmp_path) == tmp_path

    def test_a_pointer_to_a_missing_run_falls_back(self, tmp_path):
        (tmp_path / "runs").mkdir()
        (tmp_path / "current").write_text("gone\n", encoding="utf-8")
        assert rm.resolve_data_dir(tmp_path) == tmp_path

    def test_it_lists_the_runs_and_reports_the_current_one(self, tmp_path):
        (tmp_path / "runs" / "run-a").mkdir(parents=True)
        (tmp_path / "runs" / "run-b").mkdir(parents=True)
        (tmp_path / "current").write_text("run-a\n", encoding="utf-8")
        assert rm.run_ids(tmp_path) == ["run-a", "run-b"]
        assert rm.current(tmp_path) == "run-a"

    def test_each_run_resolves_to_a_different_directory(self, tmp_path):
        """The isolation claim, at the level the modules see it."""
        for name in ("run-a", "run-b", "run-c"):
            (tmp_path / "runs" / name).mkdir(parents=True)
        seen = set()
        for name in rm.run_ids(tmp_path):
            (tmp_path / "current").write_text(name + "\n", encoding="utf-8")
            seen.add(rm.resolve_data_dir(tmp_path))
        assert len(seen) == 3


class TestTheBannerLines:
    def test_unnamed_directory_says_how_to_name_it(self, data, monkeypatch):
        monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data))
        lines = rm.lines("china", 911679432)
        assert len(lines) == 1 and "no run manifest" in lines[0] and "scripts/run.py" in lines[0]

    def test_a_match_names_the_run(self, data, monkeypatch):
        monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data))
        rm.init("china-a", "A line", "china", 911679432, data_dir=data)
        rm.touch(116, data_dir=data)
        line = rm.lines("china", 911679432)[0]
        assert "china-a" in line and "A line" in line and "T116" in line

    def test_a_mismatch_is_loud_and_says_what_is_at_stake(self, data, monkeypatch):
        monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data))
        rm.init("china-a", "A line", "china", 911679432, data_dir=data)
        lines = rm.lines("china", -1894041591)
        assert lines[0].startswith("RUN MISMATCH")
        assert any("diary" in ln for ln in lines), "it must say what playing on would corrupt"

    def test_the_session_banner_carries_the_run_line(self, data, monkeypatch):
        """Both entry points print the session banner, so the assertion reaches both."""
        monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data))
        monkeypatch.setattr(session_info, "_home", lambda: data / "home")
        rm.init("china-a", "A line", "china", 911679432, data_dir=data)
        assert any(ln.startswith("RUN") for ln in session_info.banner("china", 911679432))
