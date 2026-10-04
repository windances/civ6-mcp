"""Wait until the human has finished with the military, then hand the turn back.

The division of labour says the human commands the military units and the Great Generals, and the
agent commands everything else. The mechanical problem is the turn boundary, and it is worse than it
looks: **`end_turn` does not refuse while a unit still has movement.** An `ENDTURN_BLOCKING_UNITS`
blocker is auto-resolved by `_sweep_unmoved_units` (`src/civ_mcp/end_turn.py:3613-3643`), which
fortifies combat units and skips whatever still has moves, and the turn advances. A session that
follows the division, orders its own units and calls `end_turn` therefore forfeits every military
unit's turn to the sweep, silently. The single exception is a unit with a *legal attack*, which makes
`end_turn` bounce with `UNUSED ATTACK at end_turn: ...` - that only helps while an attack is pending,
so it is not a guard.

That makes this wait the guard rather than a convenience, and it runs **before** `end_turn`.

**The human is finished when no military unit can still act** - the engine's own answer,
`IsReadyToMove()`, surfaced as `ready_to_move`. Movement alone is the wrong test, and it deadlocks
the wait rather than merely misreporting it: a unit parked by a skip (`ACTIVITY_HOLD`), one on sentry
(`ACTIVITY_SENTRY`) and one running an operation (`ACTIVITY_OPERATION`) all keep their movement for
the rest of the turn *and across turns*, while the engine reports that they cannot act. Waiting on
`moves_remaining > 0` therefore waits forever on units the human has already dealt with. Measured on
the live match when this was fixed: 10 military units had movement and **9 of them could not act**, so
the first version of this tool would never have returned 0 at all.

A unit the human means to leave alone is one they will `skip`, `fortify` or `alert` to close their
half, and any of those sets an activity the engine reports as unable to act - which is why the
activity is the test and a raw movement count is not.

    python .tools/wait-for-human.py                 # up to 30 min, poll every 10 s
    python .tools/wait-for-human.py --timeout 900 --interval 5
    python .tools/wait-for-human.py --once          # report only, do not wait

Read-only: it orders nothing at all. It exists so that a session under the division of labour has a
defined place to stop, rather than filling the gap with moves the human did not ask for.

**It cannot be run by the session that is playing.** FireTuner serves one client, and a live
session's own MCP server holds that client for the length of the session
(`src/civ_mcp/server.py:290-369` keeps one `GameConnection` for the lifespan). A second client
connects and then dies - measured with a connection deliberately held open, in both an idle and a
busy state: `ConnectionError: GameCore_Tuner/InGame states not found. Make sure a game is in
progress (not at the main menu)`. The session is told to poll its **own** `get_units` instead; this
script is for the human, or for an observer with no session attached. It exits 2, with that
explanation, when the tuner refuses it.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402


def is_the_humans(unit) -> bool:
    """A military unit, or a Great General or Great Admiral - the units the human commands.

    A Great General or Admiral has no combat strength, so the combat test alone would have left the
    human's own commanders movable by the session. The live match had both at once: a general and an
    admiral, each with a move in hand.
    """
    if (unit.combat_strength or 0) > 0:
        return True
    kind = str(unit.unit_type).upper()
    return "GENERAL" in kind or "ADMIRAL" in kind


def can_still_act(unit) -> bool:
    """Whether the human can still give this unit an order this turn.

    Three cases, in order. No movement left is done whatever else is true. A server started before
    the activity column existed reports every unit as `ready_to_move` (the field's default), so when
    the activity is absent the movement is all there is to go on - the old behaviour, which waits
    rather than advancing and is therefore the safe direction. Otherwise the engine's own
    `IsReadyToMove()` decides, which is what keeps a held, sentried or operating unit out of the
    wait.
    """
    if unit.moves_remaining <= 0:
        return False
    if not str(getattr(unit, "activity", "") or ""):
        return True
    return bool(unit.ready_to_move)


async def holding(gs) -> list:
    """The units the human can still act with: military, plus the Great Generals and Admirals."""
    return [u for u in await gs.get_units() if is_the_humans(u) and can_still_act(u)]


async def main() -> int:
    # Reconfigured here rather than at import so the module can be imported by a test without
    # touching the process's stdout.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=1800, help="seconds to wait (default 30 min)")
    ap.add_argument("--interval", type=int, default=10, help="seconds between reads")
    ap.add_argument("--once", action="store_true", help="report once and exit; never wait")
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
        return await _wait(conn, GameState(conn), args)
    except ConnectionError as exc:
        # On a connection refused because a game is not running, `connect()` itself is usually what
        # raises; when another client holds the tuner the connect succeeds and the first *read*
        # raises instead, so the guard has to cover the whole wait and not just the connect.
        print(f"the tuner refused this client: {exc}")
        print(
            "FireTuner serves one client at a time, and a playing session's own MCP server holds it\n"
            "for the whole session. Run this only when no session is attached - a session that must\n"
            "wait for the human has to poll its own get_units, not call this script."
        )
        return 2
    finally:
        await conn.disconnect()


async def _wait(conn, gs, args) -> int:
    deadline = time.time() + args.timeout
    last_sig = None
    while True:
        waiting = await holding(gs)
        if not waiting:
            print(
                "the human's half is done: no military unit, great general or admiral can still act"
            )
            return 0

        # Print the list when it changes and keep quiet while it does not, so a 30 minute wait is a
        # readable log rather than the same rows every ten seconds. The heartbeat is a timestamp, so
        # silence still says the tool is alive.
        sig = tuple(sorted((u.unit_index, u.x, u.y, u.moves_remaining, u.activity) for u in waiting))
        if sig != last_sig:
            stamp = time.strftime("%H:%M:%S")
            print(f"{stamp}  {len(waiting)} unit(s) the human can still act with:")
            for unit in waiting[:12]:
                print(
                    f"  [{unit.unit_index:>2}] {unit.unit_type:<24} ({unit.x:>3},{unit.y:>3}) "
                    f"mv{unit.moves_remaining:<5} {unit.activity or '?'}"
                )
            if len(waiting) > 12:
                print(f"  ... and {len(waiting) - 12} more")
            last_sig = sig
        else:
            print(f"{time.strftime('%H:%M:%S')}  still waiting on {len(waiting)} unit(s)")

        if args.once:
            print("--once: reporting only, not waiting")
            return 1
        if time.time() >= deadline:
            print(f"timed out after {args.timeout}s with {len(waiting)} unit(s) still able to act")
            return 1
        await asyncio.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
