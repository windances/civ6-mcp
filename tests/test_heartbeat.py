"""The heartbeat is a hint another process reads, so what it writes has to be readable.

``server.py`` passed the log line's ``"?"`` placeholder to ``heartbeat.write`` once - the dispatch
wrapper kept the numeric turn and the display label in one variable - so the file held
``"turn": "?"``. ``handoff.verdict`` reads that file with ``int(...)``, which raised ValueError, and
``scripts/resume-game.ps1`` therefore died before it printed a single line (measured 2026-09-28).
The turn in the file is an int whatever a caller passes, and a reader tolerates an old file that
was written before this.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import handoff, heartbeat  # noqa: E402

FIXTURE = ROOT / ".tmp" / "heartbeat-test.json"


@pytest.fixture()
def written(monkeypatch):
    """Write one heartbeat and return the JSON that landed on disk."""

    def write(turn) -> dict:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(heartbeat, "HEARTBEAT_PATH", FIXTURE)
        heartbeat.write("playing", turn=turn)
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    return write


class TestTheTurnIsAnIntegerInTheFile:
    def test_a_real_turn_survives(self, written):
        assert written(142)["turn"] == 142

    def test_the_log_placeholder_becomes_zero(self, written):
        # The measured defect: `logger._turn or "?"` reached this call.
        data = written("?")
        assert data["turn"] == 0
        assert isinstance(data["turn"], int), data

    def test_other_unreadable_values_become_zero(self, written):
        for value in (None, "", "T142", 14.7):
            assert written(value)["turn"] in (0, 14), value
            assert isinstance(written(value)["turn"], int), value

    def test_the_rest_of_the_heartbeat_is_untouched(self, written):
        data = written(142)
        assert data["phase"] == "playing"
        assert data["pid"] > 0 and data["ts"] > 0


class TestAReaderToleratesAnOldFile:
    def test_a_heartbeat_turn_that_is_not_a_number_is_unknown(self):
        assert handoff._heartbeat_turn("?") is None
        assert handoff._heartbeat_turn(None) is None
        assert handoff._heartbeat_turn(142) == 142
        assert handoff._heartbeat_turn("142") == 142
