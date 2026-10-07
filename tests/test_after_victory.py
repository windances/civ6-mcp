"""The human's `-AfterVictory` option: a won match stays playable, and is refused without it.

Measured 2026-10-08: at T385 the match reported `GAME OVER - VICTORY (Culture)`, and the tooling
read the turn off the save without ever reading that line - `resume-game.ps1` handed a session a
"play up to 100 turns" task in a finished match, and the conquest task published afterwards was
retired as unexecutable. `task_text` now branches on the victory, and `--after-victory` is the
human's way to say "keep playing anyway".
"""

from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import handoff as h  # noqa: E402

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
