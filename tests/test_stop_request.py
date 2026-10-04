"""The stop request: a file the human leaves, a line the session cannot miss, a recorded delivery.

There is no signal that can reach a running session (the harness CLI has no stop; the headless profile
answers one task and exits; on Windows process control cannot run a shutdown flow), so the request is a
file and the delivery is a line appended to every tool result the session reads. The part that makes it
trustworthy is the stamping: the MCP records when the line first went out, so "the session was told and
did not stop" is readable from outside - and the floor under it all is `scripts/civ6-clean.ps1`.

Advisory on purpose (human decision 2026-10-04): the MCP does not refuse the session's calls, because a
refusal can cut a move or a queue change in half and leave a worse position than finishing the turn.
"""

from __future__ import annotations

import json
import time

import pytest

from civ_mcp import stop_request as sr


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """A data root of its own, so a test can never touch the run being played."""
    monkeypatch.setenv("CIV_MCP_DATA_DIR", str(tmp_path))
    return tmp_path


def a_request(**over) -> dict:
    request = {
        "requested_at": time.time(),
        "requested_by": "scripts/stop-agent.py",
        "mode": "after-turn",
        "note": "",
        "delivered_at": None,
        "delivered_turn": None,
        "delivered_pid": None,
    }
    request.update(over)
    return request


def test_no_request_means_no_line(data_dir):
    assert sr.read(data_dir) is None
    assert sr.note(354, data_dir) == ""


def test_the_line_says_what_to_do_and_what_not_to(data_dir):
    sr.write(a_request(), data_dir)
    line = sr.note(354, data_dir)
    assert line.startswith("STOP REQUESTED|")
    assert "Finish your own half" in line
    assert "end_turn" in line and "stop" in line
    assert "do not end it, and do not order their units" in line, (
        "the human's half must be protected by the same request that stops the session"
    )
    assert "do not start another turn" in line


def test_the_note_the_human_left_is_read_back(data_dir):
    sr.write(a_request(note="stopping to reload a save"), data_dir)
    line = sr.note(354, data_dir)
    assert "stopping to reload a save" in line


def test_delivery_is_stamped_once_and_not_again(data_dir):
    """The stamp is the fact that separates "not told yet" from "told and did not stop"."""
    sr.write(a_request(), data_dir)
    sr.note(354, data_dir)
    first = sr.read(data_dir)
    assert first["delivered_turn"] == 354
    assert first["delivered_at"] is not None

    time.sleep(0.01)
    sr.note(355, data_dir)
    second = sr.read(data_dir)
    assert second["delivered_at"] == first["delivered_at"], "a second call must not re-stamp it"
    assert second["delivered_turn"] == 354, "the stamp keeps the turn it was first delivered on"


def test_a_damaged_request_is_no_request_rather_than_an_exception(data_dir):
    sr.path(data_dir).parent.mkdir(parents=True, exist_ok=True)
    sr.path(data_dir).write_text("{not json", encoding="utf-8")
    assert sr.read(data_dir) is None
    assert sr.note(354, data_dir) == ""


def test_a_request_that_is_not_an_object_is_ignored(data_dir):
    sr.path(data_dir).parent.mkdir(parents=True, exist_ok=True)
    sr.path(data_dir).write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    assert sr.read(data_dir) is None


def test_clear_removes_it_and_reports_whether_there_was_one(data_dir):
    assert sr.clear(data_dir) is False
    sr.write(a_request(), data_dir)
    assert sr.clear(data_dir) is True
    assert sr.read(data_dir) is None


def test_the_request_lives_in_the_run_the_pointer_names(data_dir):
    """Same resolution as the heartbeat and `agent-half.txt`: one request, one playthrough."""
    run = data_dir / "runs" / "china--1"
    run.mkdir(parents=True)
    (data_dir / "current").write_text("china--1", encoding="utf-8")
    assert sr.path() == run / sr.REQUEST_NAME
