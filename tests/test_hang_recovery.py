"""Tests for HANG recovery and post-load civ verification.

Tests the autosave cleanup logic and GameState hang guard field.

The cleanup tests build their own directory under the workspace instead of asking pytest for
``tmp_path``: on this machine ``mkdtemp`` hands back a directory the sandbox will not let the
test process write into, so all three errored with PermissionError instead of running. A
plain directory under the workspace is writable, which is all these tests need.
"""

import os
import pathlib
import shutil
import uuid

import pytest

from civ_mcp.game_lifecycle import cleanup_old_autosaves


@pytest.fixture()
def save_dir():
    path = pathlib.Path(".tools") / f"_test_saves_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    yield path
    shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# cleanup_old_autosaves
# ---------------------------------------------------------------------------


class TestCleanupAutosaves:
    def test_keeps_n_most_recent(self, save_dir, monkeypatch):
        """With 12 saves and keep=8, the 4 oldest are deleted."""
        tmp_path = save_dir
        monkeypatch.setattr("civ_mcp.game_launcher.SINGLE_SAVE_DIR", str(tmp_path))
        # Create 12 fake saves with staggered mtimes
        for i in range(12):
            p = tmp_path / f"0_MCP_{i:04d}.Civ6Save"
            p.write_text("x")
            os.utime(p, (1000 + i, 1000 + i))

        cleanup_old_autosaves(keep=8)

        remaining = sorted(p.name for p in tmp_path.glob("0_MCP_*.Civ6Save"))
        assert len(remaining) == 8
        # The 8 newest (highest mtime) should survive
        expected = sorted(f"0_MCP_{i:04d}.Civ6Save" for i in range(4, 12))
        assert remaining == expected

    def test_no_delete_when_under_limit(self, save_dir, monkeypatch):
        tmp_path = save_dir
        monkeypatch.setattr("civ_mcp.game_launcher.SINGLE_SAVE_DIR", str(tmp_path))
        for i in range(5):
            (tmp_path / f"0_MCP_{i:04d}.Civ6Save").write_text("x")

        cleanup_old_autosaves(keep=8)
        assert len(list(tmp_path.glob("0_MCP_*.Civ6Save"))) == 5

    def test_exactly_at_limit(self, save_dir, monkeypatch):
        tmp_path = save_dir
        monkeypatch.setattr("civ_mcp.game_launcher.SINGLE_SAVE_DIR", str(tmp_path))
        for i in range(8):
            (tmp_path / f"0_MCP_{i:04d}.Civ6Save").write_text("x")

        cleanup_old_autosaves(keep=8)
        assert len(list(tmp_path.glob("0_MCP_*.Civ6Save"))) == 8


# ---------------------------------------------------------------------------
# GameState._hang_retry_active guard
# ---------------------------------------------------------------------------


class TestHangRetryGuard:
    def test_initial_state(self):
        """GameState starts with _hang_retry_active = False."""
        from unittest.mock import MagicMock

        from civ_mcp.game_state import GameState

        conn = MagicMock()
        gs = GameState(conn)
        assert gs._hang_retry_active is False
