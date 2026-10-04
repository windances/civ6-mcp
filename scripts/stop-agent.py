"""Ask a running civ6 session to stop, and clean up only if it will not.

The session has no input channel: the harness CLI boots a profile and nothing else (`dsh --help` has
`web` and `plugin`), the headless profile answers one task and exits, and process control on Windows
cannot run a shutdown flow - `Stop-Process -Force` is `TerminateProcess`, and a synthesized Ctrl+C just
ends the process while the agent is inside a model call. So the request is a **file**, and the delivery
is a line the MCP appends to every tool result the session reads (`src/civ_mcp/stop_request.py`).

What that buys, over `civ6-clean.ps1` alone: the session gets to finish its half of the turn, write the
diary on the way out, and say where it stopped - instead of being killed mid-thought with the turn
unordered and the heartbeat still claiming a game is being played (measured 2026-10-04).

    python scripts\\stop-agent.py                    ask the session to stop, and return
    python scripts\\stop-agent.py --status           what is asked, who is playing, was it delivered
    python scripts\\stop-agent.py --cancel           withdraw the request
    python scripts\\stop-agent.py --wait 300         ask, then wait up to five minutes for it to go
    python scripts\\stop-agent.py --wait 300 --no-clean   report instead of cleaning up
    python scripts\\stop-agent.py --note "..."        a sentence the session will read

The fallback is the point: when the wait runs out, this runs `scripts\\civ6-clean.ps1 -KeepGame`, which
stops the agent and its MCP in the right order and deletes the heartbeats - and leaves the game
running, which is what a handover wants. `--no-clean` reports instead of doing that.

Exit codes:

    0   the request was left (no --wait), or the session stopped, or the fallback cleanup succeeded
    1   --wait expired and the cleanup was declined (--no-clean) or failed

The request is removed once the session is gone, whatever the path: a request left behind would stop
the *next* session on its first tool call. `--status` warns when it finds one with nobody playing.

**The run directory is resolved explicitly and passed everywhere.** `stop_request`'s own default reads
`CIV_MCP_DATA_DIR`, which a session gets from its launcher overlay and a plain shell does not - measured
in this script's first smoke test, where the request was written to `~/.civ6-mcp` instead of the run
being played. Same trap, same fix as `scripts/rollback-to-turn.py`.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import game_launcher as gl  # noqa: E402
from civ_mcp import run_manifest, stop_request  # noqa: E402

CLEAN = ROOT / "scripts" / "civ6-clean.ps1"
DATA_ROOT = ROOT / ".civ6-mcp-data"


def run_dir() -> pathlib.Path:
    """The run this checkout is playing, resolved the way every other caller resolves it."""
    return run_manifest.resolve_data_dir(DATA_ROOT)


def session_state(run: pathlib.Path) -> dict:
    """Who is playing, from passive signals only - this script never opens the tuner."""
    state: dict = {"heartbeat": None, "pid_alive": None, "playing": gl._other_active_session()}
    try:
        beat = json.loads((run / "heartbeat.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - a missing heartbeat is a stopped session, not an error
        return state
    pid = int(beat.get("pid") or 0)
    state["heartbeat"] = beat
    state["pid_alive"] = gl._pid_alive(pid)
    return state


def stopped(state: dict) -> bool:
    """True when nothing is playing any more.

    The heartbeat's pid is the immediate answer - it is what wrote the file - and
    `_other_active_session()` is the same predicate the handoff uses, so it is also accepted.
    """
    if state["pid_alive"] is False:
        return True
    return state["heartbeat"] is None and not state["playing"]


def describe(state: dict) -> str:
    beat = state["heartbeat"]
    if beat is None:
        return "no heartbeat: no session has written one for this run"
    age = max(0.0, time.time() - float(beat.get("ts") or 0))
    alive = {True: "alive", False: "gone", None: "unknown"}[state["pid_alive"]]
    return (
        f"heartbeat: phase={beat.get('phase')} turn={beat.get('turn')} pid={beat.get('pid')} "
        f"({alive}) written {age:.0f}s ago, run {beat.get('run_id')}"
    )


def show(request: dict | None, state: dict, run: pathlib.Path) -> None:
    print(f"run dir      {run}")
    if request is None:
        print("stop request none")
    else:
        asked = float(request.get("requested_at") or 0)
        print(f"stop request asked {max(0.0, time.time() - asked):.0f}s ago"
              f" ({time.strftime('%H:%M:%S', time.localtime(asked))})")
        if request.get("note"):
            print(f"             note: {request['note']}")
        if request.get("delivered_at"):
            print(f"             delivered to the session at "
                  f"T{request.get('delivered_turn')} "
                  f"({time.strftime('%H:%M:%S', time.localtime(float(request['delivered_at'])))})"
                  f" - so it has been told, pid {request.get('delivered_pid')}")
        else:
            print("             not delivered yet (no tool call has run since it was left)")
    print(describe(state))
    if state["playing"]:
        print(f"playing      {state['playing']}")
    if request is not None and stopped(state):
        print("WARNING      a request is in place with no session playing: the next session would")
        print("             stop on its first tool call. `--cancel` removes it.")


def leave_request(note: str | None, run: pathlib.Path) -> dict:
    existing = stop_request.read(run)
    if existing is not None:
        asked = time.strftime("%H:%M:%S", time.localtime(float(existing.get("requested_at") or 0)))
        print(f"a request is already in place (asked {asked}); left as it is")
        return existing
    request = {
        "requested_at": time.time(),
        "requested_by": "scripts/stop-agent.py",
        "mode": "after-turn",
        "note": (note or "").strip(),
        "delivered_at": None,
        "delivered_turn": None,
        "delivered_pid": None,
    }
    target = stop_request.write(request, run)
    try:
        shown = target.relative_to(ROOT)
    except ValueError:  # a data root outside the checkout is legal, just not printable that way
        shown = target
    print(f"stop request written to {shown}")
    print("the session reads it on its next tool call and stops after finishing its half;")
    print(f"if it does not, `--wait N` runs {CLEAN.relative_to(ROOT)} for it.")
    return request


def clean_up() -> int:
    """Stop the agent and its MCP, keep the game. The floor under the request."""
    print(f"\n--- fallback: {CLEAN.relative_to(ROOT)} -KeepGame ---")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(CLEAN), "-KeepGame"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in (result.stdout or "").splitlines():
        print("  " + line)
    for line in (result.stderr or "").splitlines():
        print("  " + line)
    # The script exits 1 when the tuner is still listening, which with -KeepGame is the game itself
    # holding its own port - the expected residue, not a failure. The plan lines say what it stopped.
    cleaned = "stopped      agent" in (result.stdout or "")
    print(f"fallback     exit {result.returncode}, "
          f"{'the agent was stopped' if cleaned else 'nothing was stopped'}")
    return 0 if cleaned else 1


def wait_for_stop(seconds: int, interval: int, auto_clean: bool, run: pathlib.Path) -> int:
    deadline = time.time() + seconds
    last = None
    while True:
        state = session_state(run)
        if stopped(state):
            print(f"\nthe session has stopped ({describe(state)})")
            stop_request.clear(run)
            print("stop request removed, so the next session will not stop on its first call")
            return 0
        line = describe(state)
        stamp = time.strftime("%H:%M:%S")
        if line == last:
            print(f"{stamp}  still playing")
        else:
            print(f"{stamp}  waiting: {line}")
            request = stop_request.read(run)
            if request and request.get("delivered_at"):
                print(f"{stamp}  the session has been told (T{request.get('delivered_turn')})")
            last = line
        if time.time() >= deadline:
            print(f"\nthe session did not stop within {seconds}s")
            if not auto_clean:
                print(f"--no-clean: stopping here. Run {CLEAN.relative_to(ROOT)} -KeepGame yourself.")
                return 1
            code = clean_up()
            stop_request.clear(run)
            print("stop request removed")
            return code
        time.sleep(interval)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", action="store_true", help="report the request and who is playing")
    ap.add_argument("--cancel", action="store_true", help="withdraw the request and exit")
    ap.add_argument("--wait", type=int, default=0, metavar="N",
                    help="wait up to N seconds, then fall back to civ6-clean.ps1 -KeepGame")
    ap.add_argument("--interval", type=int, default=10, help="seconds between reads (default 10)")
    ap.add_argument("--no-clean", action="store_true",
                    help="with --wait: report the timeout instead of cleaning up")
    ap.add_argument("--note", help="a sentence the session will read with the request")
    args = ap.parse_args()

    run = run_dir()

    if args.cancel:
        removed = stop_request.clear(run)
        print("stop request removed" if removed else "no stop request to remove")
        return 0

    if args.status:
        show(stop_request.read(run), session_state(run), run)
        return 0

    leave_request(args.note, run)
    if args.wait <= 0:
        return 0
    print(f"\nwaiting up to {args.wait}s for the session to stop...")
    return wait_for_stop(args.wait, max(2, args.interval), not args.no_clean, run)


if __name__ == "__main__":
    raise SystemExit(main())
