"""Save names: `0_MCP_NNNN` is an invariant, and the file is what settles it.

Measured 2026-09-27 (109 saves on this machine): the game's own `AutoSave_NNNN` is consistent -
its name runs exactly one turn ahead of the turn it holds, 100 of 100 - while `0_MCP_NNNN` was
named one turn low in 4 of the last 9, because `end_turn` built the name from the same
post-advance read that sometimes prints `Turn 203 -> 203`:

    0_MCP_0206 -> T207   0_MCP_0209 -> T210   0_MCP_0212 -> T213   0_MCP_0215 -> T216

That matters because the name is load-bearing in two places: the agent's expiry clock
(`tests/test_temp_tasks.game_turn`) and the human's load verification (`resume-game.ps1` through
`game_launcher._save_turn`). Both now ask the file first; these tests pin the decision.
"""

from __future__ import annotations

import pathlib
import shutil
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import game_launcher as gl  # noqa: E402
from civ_mcp import handoff  # noqa: E402
from civ_mcp.autosave import verified_save_name  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestTheCorrectedName:
    def test_a_name_that_lags_the_file_is_corrected(self):
        # The field case: the file holds T216 while the name claims 215.
        assert verified_save_name("0_MCP_0215", 216) == "0_MCP_0216"
        assert verified_save_name("0_MCP_0206", 207) == "0_MCP_0207"

    def test_a_name_that_matches_is_left_alone(self):
        assert verified_save_name("0_MCP_0218", 218) is None

    def test_the_games_own_autosave_is_never_renamed(self):
        # `AutoSave_NNNN` deliberately runs one ahead of the turn it holds; renaming it would
        # destroy that offset rather than a bug.
        assert verified_save_name("AutoSave_0217", 216) is None
        assert verified_save_name("AutoSave_0218", 218) is None

    def test_a_manual_save_is_never_renamed(self):
        assert verified_save_name("秦始皇（大一统） 218 公元1535年", 218) is None

    def test_an_unreadable_file_leaves_the_name_alone(self):
        assert verified_save_name("0_MCP_0215", None) is None

    def test_the_corrected_name_is_still_a_name_the_clock_can_read(self):
        # The rename must land on a name the fallback rule maps back to the same turn.
        corrected = verified_save_name("0_MCP_0215", 216)
        assert gl._save_turn(corrected) == 216


class TestReadingTheRealTurn:
    def saves(self) -> list[pathlib.Path]:
        found = []
        for directory in (gl.SAVE_DIR, gl.SINGLE_SAVE_DIR):
            found += [p for p in pathlib.Path(directory).glob("*.Civ6Save")]
        return found

    def test_the_file_is_asked_rather_than_the_name(self):
        saves = self.saves()
        if not saves:
            pytest.skip("no game install on this machine")
        newest = max(saves, key=lambda p: p.stat().st_mtime)
        turn = handoff.save_turn(newest)
        assert turn is None or (isinstance(turn, int) and turn > 0), (
            f"{newest.name} answered {turn!r}; the clock's fallback is the name, so a None is"
            " allowed but a nonsense value is not"
        )

    def test_a_named_low_mcp_save_reports_the_higher_turn(self):
        """The regression itself, on the real files, when they are still there.

        0_MCP_0215 was written while the game stood on T216. If that save has since been cleaned
        up by `cleanup_old_autosaves(keep=8)` the check is skipped rather than weakened.
        """
        path = pathlib.Path(gl.SINGLE_SAVE_DIR) / "0_MCP_0215.Civ6Save"
        if not path.exists():
            pytest.skip("0_MCP_0215 has been cleaned up since the measurement")
        assert handoff.save_turn(path) == 216
        assert verified_save_name("0_MCP_0215", 216) == "0_MCP_0216"


class TestTheServerRenamesItsOwnSave:
    """The wiring, on a real save file - the pure decision above proves nothing on its own.

    A copy of a known mis-named save is placed in a scratch directory, `SINGLE_SAVE_DIR` is
    pointed at it, and `end_turn`'s post-save check is called exactly as it is after a save.
    """

    SCRATCH = ROOT / ".tmp" / "naming-fixture"

    def _copy_of(self, name: str, monkeypatch) -> pathlib.Path:
        source = pathlib.Path(gl.SINGLE_SAVE_DIR) / name
        if not source.exists():
            pytest.skip(f"{name} has been cleaned up since the measurement")
        shutil.rmtree(self.SCRATCH, ignore_errors=True)
        self.SCRATCH.mkdir(parents=True)
        shutil.copy2(source, self.SCRATCH / name)
        monkeypatch.setattr(gl, "SINGLE_SAVE_DIR", str(self.SCRATCH))
        return self.SCRATCH / name

    def test_a_stale_mcp_save_is_renamed_to_the_turn_it_holds(self, monkeypatch):
        self._copy_of("0_MCP_0215.Civ6Save", monkeypatch)
        et._verify_mcp_save_name("0_MCP_0215")
        assert (self.SCRATCH / "0_MCP_0216.Civ6Save").exists(), (
            "the save holds T216, so its name must say 0216 afterwards"
        )
        assert not (self.SCRATCH / "0_MCP_0215.Civ6Save").exists()

    def test_a_correct_name_is_left_alone(self, monkeypatch):
        self._copy_of("0_MCP_0218.Civ6Save", monkeypatch)
        et._verify_mcp_save_name("0_MCP_0218")
        assert (self.SCRATCH / "0_MCP_0218.Civ6Save").exists()
        assert not (self.SCRATCH / "0_MCP_0219.Civ6Save").exists()

    def test_a_missing_file_is_not_a_crash(self, monkeypatch):
        shutil.rmtree(self.SCRATCH, ignore_errors=True)
        self.SCRATCH.mkdir(parents=True)
        monkeypatch.setattr(gl, "SINGLE_SAVE_DIR", str(self.SCRATCH))
        et._verify_mcp_save_name("0_MCP_9999")  # nothing to do, nothing to raise
