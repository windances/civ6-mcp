"""A stop request the human can leave for a running session, delivered by the tool results it reads.

**Why a file and not a signal.** There is no signal that can reach this agent. The harness CLI boots a
profile and nothing else (`dsh --help` has `web` and `plugin`, no stop or interrupt), and the headless
profile is one-shot by design - *"answer one task, print the result, and exit"* - so a running session
has no input channel. What is left is process control, and none of it can run a shutdown flow: on
Windows `Stop-Process -Force` is `TerminateProcess`, there is no usable SIGTERM, and a synthesized
Ctrl+C only makes the *process* exit while the agent is inside a model call. Measured 2026-10-04: a
session killed that way left an unordered turn, no diary entry for it and a heartbeat still claiming a
game was being played.

**What can reach it is its own tool output.** Every result the server returns is in the session's
context - that is how `WHOSE MOVE|` reaches it, proved live the same day - so the request is a file and
the delivery is a line appended to every successful tool result.

**Delivery is recorded here, not by the agent.** The first time the line goes out, the MCP stamps
`delivered_at`, `delivered_turn` and `delivered_pid` into the request, so "the session was told and did
not stop" is something a person can read rather than guess. Honouring it is the session's own flow
(finish its half, end the turn only if nothing is holding it, exit), and the floor stays
`scripts/civ6-clean.ps1 -KeepGame`, which `scripts/stop-agent.py` runs when the request goes
unhonoured.

**The request is advisory on purpose** (human decision 2026-10-04): the MCP does not refuse the
session's calls, because a refusal can cut a move or a queue change in half and leave a worse position
than letting the turn finish. The nag on every result, the recorded delivery and the cleanup fallback
are what make it safe instead.
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import time
from typing import Any

log = logging.getLogger(__name__)

#: Beside the heartbeat and `agent-half.txt`, in the run directory: the request belongs to one
#: playthrough, and `run_manifest.resolve_data_dir` is what tells the two apart.
REQUEST_NAME = "stop-request.json"

#: How long ago the request was left, phrased for the line the session reads.
def _age(seconds: float) -> str:
    if seconds < 90:
        return f"{seconds:.0f}s ago"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m ago"
    return f"{seconds / 3600:.1f}h ago"


def path(data_dir: pathlib.Path | str | None = None) -> pathlib.Path:
    """Where the request lives - resolved at call time, the way the heartbeat resolves its own."""
    if data_dir is not None:
        return pathlib.Path(data_dir) / REQUEST_NAME
    from civ_mcp import run_manifest

    return run_manifest.resolve_data_dir() / REQUEST_NAME


def read(data_dir: pathlib.Path | str | None = None) -> dict[str, Any] | None:
    """The request in force, or None. An unreadable file is no request, never an exception."""
    try:
        data = json.loads(path(data_dir).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - a missing or damaged request is simply no request
        return None
    return data if isinstance(data, dict) else None


def write(request: dict[str, Any], data_dir: pathlib.Path | str | None = None) -> pathlib.Path:
    """Put a request in place (atomic tmp + rename, like every other small state file here)."""
    target = path(data_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(request, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(target)
    return target


def clear(data_dir: pathlib.Path | str | None = None) -> bool:
    """Withdraw the request. True when one was there."""
    target = path(data_dir)
    try:
        target.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError:  # noqa: BLE001 - a request that cannot be removed is reported by the caller
        log.debug("could not remove the stop request", exc_info=True)
        return False


def render(request: dict[str, Any], now: float | None = None) -> str:
    """The line the session reads - what to do, and what not to do."""
    asked = float(request.get("requested_at") or 0)
    age = _age(max(0.0, (time.time() if now is None else now) - asked)) if asked else "at an unknown time"
    note = str(request.get("note") or "").strip()
    lines = [
        f"STOP REQUESTED|the human asked this session to stop ({age}). Finish your own half, then:",
        "  * if nothing is holding the turn, `end_turn` with the five diary reflections, and stop;",
        "  * if the human's units are still holding it, leave the turn exactly where it is and stop -",
        "    do not end it, and do not order their units;",
        "  * either way, do not start another turn, and write your closing report before you exit.",
    ]
    if note:
        lines.insert(1, f"  their note: {note}")
    return "\n".join(lines)


def mark_delivered(turn: int = 0, data_dir: pathlib.Path | str | None = None) -> dict[str, Any] | None:
    """Record that the session has now been told. Written once; later calls leave it alone."""
    request = read(data_dir)
    if request is None or request.get("delivered_at"):
        return request
    request["delivered_at"] = time.time()
    request["delivered_turn"] = int(turn or 0)
    request["delivered_pid"] = os.getpid()
    try:
        write(request, data_dir)
    except Exception:  # noqa: BLE001 - the line still goes out even if the stamp cannot be written
        log.debug("could not stamp the stop request as delivered", exc_info=True)
    return request


def note(turn: int = 0, data_dir: pathlib.Path | str | None = None) -> str:
    """`""`, or the line to append to a tool result. Never raises: a tool must still return."""
    try:
        request = read(data_dir)
        if request is None:
            return ""
        request = mark_delivered(turn, data_dir) or request
        return render(request)
    except Exception:  # noqa: BLE001
        log.debug("could not read the stop request", exc_info=True)
        return ""
