"""Wait until the game says the turn can end, then hand it back.

The division of labour says the human commands the military units, the Great Generals and the Great
Admirals, and the agent commands everything else. The turn boundary is the problem, and it is worse
than it looks: **`end_turn` does not refuse while a unit still has movement.** An
`ENDTURN_BLOCKING_UNITS` blocker is auto-resolved by `_sweep_unmoved_units`
(`src/civ_mcp/end_turn.py:3613-3643`), which fortifies combat units and skips the rest, and the turn
advances. A session that follows the division, orders its own units and calls `end_turn` therefore
forfeits every military unit's turn to the sweep, silently.

**Ask the game, do not count units.** The signal is the game's own: it raises an
`ENDTURN_BLOCKING_UNITS` notification while any unit still has moves, and stops raising it the moment
the turn can end. That is the same fact `UI.CanEndTurn()` reports, and the MCP already relies on it
(`src/civ_mcp/end_turn.py:3689-3702`). Counting movement is the wrong test twice over: a unit parked
by a `skip` (`ACTIVITY_HOLD`), one on `alert` (`ACTIVITY_SENTRY`), one asleep and one running an
operation all keep their movement for the rest of the turn *and across turns* while being unable to
act - so a movement count waits forever on units the human has already dealt with. Measured on the
live match: 10 military units had movement and 9 of them could not act.

    python .tools/wait-for-human.py                 # up to 30 min, poll every 10 s
    python .tools/wait-for-human.py --timeout 900 --interval 5
    python .tools/wait-for-human.py --once          # report only, do not wait

Exit codes:

    0   the turn can end - no EndTurnBlocking remains. The human's half is done; call end_turn.
    1   still waiting (the units blocker is up), or the timeout expired, or --once found one.
    2   the tuner refused this client (see below).
    3   blocked, but NOT by units - an empty queue, an unspent promotion or similar. That is the
        agent's own work and waiting will not clear it, so it does not wait.

**It cannot be run by the session that is playing.** FireTuner serves one client, and a live
session's own MCP server holds that client for the length of the session
(`src/civ_mcp/server.py:290-369` keeps one `GameConnection` for the lifespan). A second client
connects and then dies - measured with a connection deliberately held open, in both an idle and a
busy state: `ConnectionError: GameCore_Tuner/InGame states not found`. The session is told to read
`get_notifications` itself instead; this script is for the human, or for an observer with no session
attached. It exits 2, with that explanation, when the tuner refuses it.

Read-only: it orders nothing at all.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import lua as lq  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

# The blocker that means "a unit still has moves". Every other blocker is the agent's own work.
UNITS_BLOCKER = "ENDTURN_BLOCKING_UNITS"

# Ask the game two ways at once, because they answer different halves of the question: UI.CanEndTurn()
# is the boolean the game's own End Turn button is driven by, and the notification pass names *which*
# blocker is up, which is what tells the human's half from the agent's.
STATE_LUA = f"""
local out = {{}}
local me = Game.GetLocalPlayer()
local ok, can = pcall(function() return UI.CanEndTurn() end)
out[#out+1] = "CANEND|" .. tostring(ok) .. "|" .. tostring(can)
local seen = {{}}
local list = NotificationManager.GetList(me)
if list then
  for _, nid in ipairs(list) do
    pcall(function()
      local e = NotificationManager.Find(me, nid)
      if e and not e:IsDismissed() then
        local bt = e:GetEndTurnBlocking()
        if bt and bt ~= 0 then
          local nm = "UNKNOWN"
          for k, v in pairs(EndTurnBlockingTypes) do
            if v == bt then nm = k end
          end
          seen[nm] = (seen[nm] or 0) + 1
        end
      end
    end)
  end
end
for k, v in pairs(seen) do out[#out+1] = "BLOCK|" .. k .. "|" .. v end
for _, l in ipairs(out) do print(l) end
print("{lq.SENTINEL}")
"""


def is_the_humans(unit) -> bool:
    """A military unit, or a Great General or Great Admiral - the units the human commands.

    A Great General or Admiral has no combat strength, so the combat test alone would have left the
    human's own commanders movable by the session.
    """
    if (unit.combat_strength or 0) > 0:
        return True
    kind = str(unit.unit_type).upper()
    return "GENERAL" in kind or "ADMIRAL" in kind


def can_still_act(unit) -> bool:
    """Whether the human can still give this unit an order this turn.

    Only used for the *detail* line under the units blocker - naming what the human still has. The
    decision comes from the game's own blocker, never from this count.
    """
    if unit.moves_remaining <= 0:
        return False
    if not str(getattr(unit, "activity", "") or ""):
        return True
    return bool(unit.ready_to_move)


async def game_state(conn) -> tuple[bool | None, dict[str, int]]:
    """`(can_end_turn, blockers)` straight from the game.

    `can_end_turn` is None when the UI call itself failed, in which case the blocker list is still
    what the decision is made on.
    """
    can_end: bool | None = None
    blockers: dict[str, int] = {}
    for line in await conn.execute_write(STATE_LUA):
        line = (line or "").strip()
        if line.startswith("CANEND|"):
            parts = line.split("|")
            if len(parts) >= 3 and parts[1] == "true":
                can_end = parts[2].strip().lower() == "true"
        elif line.startswith("BLOCK|"):
            _, name, count = (line.split("|") + ["", ""])[:3]
            blockers[name] = int(count) if count.isdigit() else 1
    return can_end, blockers


async def holding(gs) -> list:
    """The units the human can still act with - detail only, never the decision."""
    return [u for u in await gs.get_units() if is_the_humans(u) and can_still_act(u)]


def render(blockers: dict[str, int]) -> str:
    return ", ".join(f"{k} x{v}" for k, v in sorted(blockers.items())) or "none"


def decide(blockers: dict[str, int]) -> str:
    """What the blocker set means: `"go"`, `"wait"` or `"agent"`.

    The whole rule, in one place, so it can be tested without a game:

      * no blocker at all          -> the turn can end; the human's half is done.
      * the units blocker is up    -> the human still has units. Wait. Other blockers may be up at
                                      the same time; they are shown but do not change the answer,
                                      because the units blocker is the gate.
      * blockers but no units one  -> the agent's own work (empty queue, unspent promotion, ...).
                                      Waiting cannot clear it, so this must not consume the timeout.
    """
    if not blockers:
        return "go"
    if UNITS_BLOCKER in blockers:
        return "wait"
    return "agent"


async def _wait(conn, gs, args) -> int:
    deadline = time.time() + args.timeout
    last_sig = None
    while True:
        can_end, blockers = await game_state(conn)
        action = decide(blockers)

        if action == "go":
            note = "" if can_end is not False else " (UI.CanEndTurn disagrees, but no blocker is up)"
            print(f"the turn can end: no EndTurnBlocking remains{note}")
            return 0

        if action == "agent":
            # Not the human's half. Waiting cannot clear it, so say so and stop.
            print(f"blocked, but not by units: {render(blockers)}")
            print("this is the agent's own work - an empty queue, an unspent promotion, a governor")
            print("point. Waiting will not clear it, so the wait ends here and does not consume the")
            print("timeout.")
            return 3

        sig = tuple(sorted(blockers.items()))
        stamp = time.strftime("%H:%M:%S")
        if sig != last_sig:
            waiting = await holding(gs)
            print(f"{stamp}  the human still has units: {render(blockers)}")
            if waiting:
                print(f"  {len(waiting)} unit(s) can still act:")
                for unit in waiting[:12]:
                    print(
                        f"    [{unit.unit_index:>2}] {unit.unit_type:<24} "
                        f"({unit.x:>3},{unit.y:>3}) mv{unit.moves_remaining:<5} {unit.activity or '?'}"
                    )
                if len(waiting) > 12:
                    print(f"    ... and {len(waiting) - 12} more")
            last_sig = sig
        else:
            print(f"{stamp}  still waiting: {render(blockers)}")

        if args.once:
            print("--once: reporting only, not waiting")
            return 1
        if time.time() >= deadline:
            print(f"timed out after {args.timeout}s with {render(blockers)} still up")
            return 1
        await asyncio.sleep(args.interval)


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
        # When another client holds the tuner the connect succeeds and the first *read* raises
        # instead, so the guard has to cover the whole wait and not just the connect.
        print(f"the tuner refused this client: {exc}")
        print(
            "FireTuner serves one client at a time, and a playing session's own MCP server holds it\n"
            "for the whole session. Run this only when no session is attached - a session that must\n"
            "wait for the human reads get_notifications itself, not this script."
        )
        return 2
    finally:
        await conn.disconnect()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
