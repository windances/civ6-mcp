"""`get_game_status` must not report `starting` on a game the caller is already reading.

Measured 2026-09-29, in the session that took over the new match: `get_game_status` answered
`starting`, and the handoff task tells a session to stop and report unless it answers `in_game` - while
`get_game_overview`, `get_pending_diplomacy`, `get_pending_trades` and `get_world_congress` all
answered normally at turn 1. The session spent a dozen calls working out that the status was wrong.

The cause is structural, not a glitch. FireTuner serves one connection and stops accepting new ones
once one is established, so `_is_tuner_port_open()` is False for the session that holds it; and the OCR
fallback reads a stale frame when the game window is occluded (that session's foreground window was
another application). So the two probes both fail in exactly the case that matters, and the caller's own
live connection is the evidence to trust.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import game_launcher as gl  # noqa: E402


def _stub_probes(monkeypatch, *, pids: list[int]) -> None:
    """A game process and a window, no tuner response, and a screen OCR cannot classify."""
    monkeypatch.setattr(gl, "_running_game_pids", lambda: pids)
    monkeypatch.setattr(gl, "_find_game_window", lambda: None)
    monkeypatch.setattr(gl, "_is_tuner_port_open", lambda: False)
    monkeypatch.setattr(gl, "_tuner_port_state", lambda: {"listening": False, "clients": []})
    monkeypatch.setattr(gl, "_foreign_tuner_clients", lambda clients, pids: [])


def test_a_live_own_connection_is_reported_as_in_game(monkeypatch):
    _stub_probes(monkeypatch, pids=[556])
    text = gl.game_status(own_connection=True)
    assert "in_game" in text.lower(), text
    assert "own FireTuner connection is live" in text, (
        "the status has to explain why the port probe disagrees, or the next reader re-derives it"
    )


def test_without_that_connection_the_same_probes_still_say_starting(monkeypatch):
    """The flag is the fix, so its absence must keep the old - and for a fresh launcher, correct -
    answer: a process with no tuner and no readable screen is a game that has not finished starting."""
    _stub_probes(monkeypatch, pids=[556])
    text = gl.game_status(own_connection=False)
    assert "starting" in text.lower(), text
    assert "own FireTuner connection is live" not in text


def test_no_process_is_still_not_running(monkeypatch):
    """A live connection cannot conjure a game that is not running."""
    _stub_probes(monkeypatch, pids=[])
    text = gl.game_status(own_connection=True)
    assert "not_running" in text.lower(), text
