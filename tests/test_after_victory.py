"""The human's `-AfterVictory` option: a won match stays playable, and is refused without it.

Measured 2026-10-08: at T385 the match reported `GAME OVER - VICTORY (Culture)`, and the tooling
read the turn off the save without ever reading that line - `resume-game.ps1` handed a session a
"play up to 100 turns" task in a finished match, and the conquest task published afterwards was
retired as unexecutable. `task_text` now branches on the victory, and `--after-victory` is the
human's way to say "keep playing anyway".

The option has two halves, and the second is the one that pinned the match: the launcher says the
session is continuing, and `execute_end_turn` must be willing to send ACTION_ENDTURN. Measured
T387: `Game.GetWinningTeam()` stays set for the rest of a won match, so `check_game_over()` reports
a victory on every call forever and the engine gate returned `GAME OVER — VICTORY!` before it ever
reached a blocker. `CIV_MCP_AFTER_VICTORY` is that gate's switch.
"""

from __future__ import annotations

import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import handoff as h  # noqa: E402
from civ_mcp.end_turn import (  # noqa: E402
    _after_victory_allowed,
    _after_victory_marker,
    _terminal_game_over,
)

VICTORY = "GAME OVER - VICTORY (Culture) at T385"


def _facts(victory: str | None) -> dict:
    """A finished match: live-looking facts plus the GAME OVER line, and no probe turn."""
    facts, _ = h.check(probe=False)
    facts = dict(facts)
    facts["checked_at"] = "2026-10-08 00:37:00"
    facts["victory"] = victory
    return facts


def _result() -> dict:
    return {"turn": None, "ready": True, "blockers": [], "rollback": False}


class TestTheVictoryBranch:
    def test_without_the_flag_the_task_refuses_to_play(self):
        text = h.task_text(_facts(VICTORY), _result())
        assert VICTORY in text
        assert "There is nothing to play here" in text
        assert "-AfterVictory" in text, "the refusal has to name the way out"

    def test_with_the_flag_the_task_says_the_session_is_continuing(self):
        text = h.task_text(_facts(VICTORY), _result(), after_victory=True)
        assert "continuing it deliberately" in text
        assert "one more turn" in text, "the victory screen is the first obstacle in this state"
        assert "there is nothing to play here" not in text

    def test_the_flag_also_arrives_on_the_result_dict(self):
        """`main` sets it there, so `write_task` does not need a new parameter."""
        text = h.task_text(_facts(VICTORY), {**_result(), "after_victory": True})
        assert "continuing it deliberately" in text

    def test_a_live_match_is_untouched(self):
        text = h.task_text(_facts(None), {**_result(), "turn": 386})
        assert "GAME OVER" not in text
        assert "found turn 386" in text


class TestTheTurnNeverRendersAsNone:
    def test_it_falls_back_to_the_newest_save(self):
        """Measured 2026-10-08: a tuner-busy preflight wrote `found turn None` into the task."""
        facts = _facts(None)
        facts["saves"] = {"newest": {"name": "AutoSave_0387", "turn": 386}}
        text = h.task_text(facts, _result())
        assert "found turn 386" in text
        assert "found turn None" not in text

    def test_without_a_save_it_says_unknown_rather_than_none(self):
        facts = _facts(None)
        facts["saves"] = {"newest": {"name": "x", "turn": None}}
        text = h.task_text(facts, _result())
        assert "found turn unknown" in text
        assert "None" not in text


class _Over:
    """Only the fields `_terminal_game_over` reads - no live game needed."""

    def __init__(
        self,
        defeat: bool = False,
        victory_type: str = "VICTORY_CULTURE",
        winner_name: str = "China",
        winner_leader: str = "Qin (Unifier)",
    ) -> None:
        self.is_defeat = defeat
        self.victory_type = victory_type
        self.winner_name = winner_name
        self.winner_leader = winner_leader


class TestTheEngineGate:
    """The half that pinned T387: the gate must be willing to send ACTION_ENDTURN."""

    def test_without_the_variable_a_victory_is_terminal(self, monkeypatch):
        monkeypatch.delenv("CIV_MCP_AFTER_VICTORY", raising=False)
        line = _terminal_game_over(_Over())
        assert line is not None
        assert "GAME OVER — VICTORY" in line
        assert "Culture" in line

    def test_with_the_variable_the_turn_is_played_on(self, monkeypatch):
        monkeypatch.setenv("CIV_MCP_AFTER_VICTORY", "1")
        assert _terminal_game_over(_Over()) is None

    def test_a_defeat_is_terminal_even_with_the_variable(self, monkeypatch):
        """Nothing to play on for: a rival's win ends this match either way."""
        monkeypatch.setenv("CIV_MCP_AFTER_VICTORY", "1")
        line = _terminal_game_over(_Over(defeat=True, winner_name="Georgia", winner_leader="Tamar"))
        assert line is not None
        assert "GAME OVER — DEFEAT" in line

    def test_each_sites_own_prefix_survives(self, monkeypatch):
        """The post-advance site opens with `Turn 387 -> 388`, and it must keep doing so."""
        monkeypatch.delenv("CIV_MCP_AFTER_VICTORY", raising=False)
        line = _terminal_game_over(_Over(), prefix="Turn 387 -> 388\n")
        assert line is not None
        assert line.startswith("Turn 387 -> 388\n")


class TestTheAfterVictoryVariable:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " on "])
    def test_truthy_values_enable_it(self, monkeypatch, value):
        monkeypatch.setenv("CIV_MCP_AFTER_VICTORY", value)
        assert _after_victory_allowed() is True

    @pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "maybe"])
    def test_other_values_leave_the_gate_on(self, monkeypatch, value):
        monkeypatch.setenv("CIV_MCP_AFTER_VICTORY", value)
        assert _after_victory_allowed() is False

    def test_unset_means_off(self, monkeypatch):
        monkeypatch.delenv("CIV_MCP_AFTER_VICTORY", raising=False)
        assert _after_victory_allowed() is False


class TestTheMarkerFile:
    """The second way in, so a restart that keeps its environment still sees the decision."""

    def test_the_marker_lives_beside_the_run_data(self, monkeypatch):
        monkeypatch.setenv("CIV_MCP_DATA_DIR", str(ROOT / "elsewhere"))
        assert _after_victory_marker() == ROOT / "elsewhere" / "after-victory"

    def test_the_marker_opens_the_gate_without_the_variable(self, monkeypatch):
        marker = ROOT / "_after-victory-test.marker"
        monkeypatch.setattr("civ_mcp.end_turn._after_victory_marker", lambda: marker)
        monkeypatch.delenv("CIV_MCP_AFTER_VICTORY", raising=False)
        assert _after_victory_allowed() is False
        marker.write_text("CIV_MCP_AFTER_VICTORY\n", encoding="ascii")
        try:
            assert _after_victory_allowed() is True
            assert _terminal_game_over(_Over()) is None
        finally:
            marker.unlink()

    def test_a_marker_that_cannot_be_read_refuses_rather_than_raising(self, monkeypatch):
        monkeypatch.setattr(
            "civ_mcp.end_turn._after_victory_marker",
            lambda: ROOT / "no-such-directory" / "after-victory",
        )
        monkeypatch.delenv("CIV_MCP_AFTER_VICTORY", raising=False)
        assert _after_victory_allowed() is False


class TestNoSiteKeepsItsOwnCopyOfTheRefusal:
    """A second copy of the return is how this bug comes back.

    `execute_end_turn` checks the game-over state in five places - at entry, twice inside the
    polling loop, in the blocked path and after the advance - and each one used to build its own
    `GAME OVER` string. Restoring one of those by hand re-creates the T387 stall for that path
    only, which is exactly the kind of failure that reads as "the tool is sometimes stuck".
    """

    def test_every_check_goes_through_the_helper(self):
        source = (ROOT / "src" / "civ_mcp" / "end_turn.py").read_text(encoding="utf-8")
        checks = source.count("await gs.check_game_over()")
        helpers = source.count("_terminal_game_over(")
        assert checks == 5, f"{checks} game-over checks in end_turn.py, expected 5"
        # Four call sites plus one definition.
        assert helpers == checks + 1, (
            f"{checks} game-over checks but {helpers} references to _terminal_game_over - one of "
            "them builds its own GAME OVER line again"
        )

    def test_the_single_definition_is_where_the_victory_is_read(self):
        source = (ROOT / "src" / "civ_mcp" / "end_turn.py").read_text(encoding="utf-8")
        assert "GAME OVER — VICTORY!" in source
        assert source.count("GAME OVER — VICTORY!") == 1, (
            "the victory line belongs to _terminal_game_over alone"
        )


class TestTheProbeIsWhatFindsIt:
    """`_game_probe` asks the game whether the match is decided, so the option is never manual.

    The launcher's `-AfterVictory` only *says* the session is continuing; what makes a won match
    playable is the gate in `end_turn`. Both need the handoff to know the match is over, and the
    handoff used to read the turn off the save without ever asking - measured T385, where the
    generated task offered 100 turns of play in a finished match.
    """

    def test_the_probe_reads_the_winning_team(self):
        source = (ROOT / "src" / "civ_mcp" / "game_launcher.py").read_text(encoding="utf-8")
        assert "GAMEOVER|" in source, "the probe no longer asks whether the match is decided"
        assert "Game.GetWinningTeam()" in source
        assert '"game_over"' in source, "the answer is not carried out of the probe"

    def test_a_probe_victory_is_enough_without_the_explicit_string(self):
        facts = _facts(None)
        facts["probe"] = {"connected": True, "ingame": True, "turn": 387, "game_over": "VICTORY"}
        text = h.task_text(facts, _result())
        assert "This match is already won" in text
        assert "-AfterVictory" in text

    def test_a_defeat_is_not_offered_as_a_match_to_play_on(self):
        """The human's option is playing on after a *win*; a rival's win ends it for everyone."""
        facts = _facts(None)
        facts["probe"] = {"connected": True, "ingame": True, "turn": 387, "game_over": "DEFEAT"}
        text = h.task_text(facts, _result(), after_victory=True)
        assert "already won" not in text
        assert "continuing it deliberately" not in text

    def test_a_live_probe_carries_no_game_over(self):
        facts = _facts(None)
        facts["probe"] = {"connected": True, "ingame": True, "turn": 387, "game_over": None}
        text = h.task_text(facts, {"turn": 387, "ready": True, "blockers": []})
        assert "GAME OVER" not in text
        assert "found turn 387" in text
