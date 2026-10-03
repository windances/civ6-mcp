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

It knows by reading, not by being told: **the human is finished when every military unit has no
movement left.** A unit the human means to leave alone is still a unit they will `skip` or `fortify`
to close their half, and that sets its movement to zero like any other order. The same goes for the
Great Generals and Great Admirals, which are the human's too but carry no combat strength. A unit
nobody touches keeps its moves, so the tool waits rather than deciding for them. So this polls
`get_units` and reports, and it is the one place where waiting is the correct action rather than a
failure to act.

    python .tools/wait-for-human.py                 # up to 30 min, poll every 10 s
    python .tools/wait-for-human.py --timeout 900 --interval 5
    python .tools/wait-for-human.py --once          # report only, do not wait

Read-only: it orders nothing at all. It exists so that a session under the division of labour has a
defined place to stop, rather than filling the gap with moves the human did not ask for.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402


def is_military(unit) -> bool:
    return (unit.combat_strength or 0) > 0


async def holding(gs) -> list:
    """The military units the human has not finished with, plus any great general or admiral moving.

    A Great General is included on purpose: it commands the army, so it is the human's like the units
    it leads. It has no combat strength, which is exactly why a filter on `combat_strength` alone
    would have let the session end the turn while the human was still placing one - matched here by
    its unit type instead. The Great Admiral is the same case at sea, and it is not hypothetical: the
    live match had one at (31,22) with a move in hand the first time this ran.
    """
    waiting = []
    for unit in await gs.get_units():
        if unit.moves_remaining <= 0:
            continue
        kind = str(unit.unit_type).upper()
        if is_military(unit) or "GENERAL" in kind or "ADMIRAL" in kind:
            waiting.append(unit)
    return waiting


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=1800, help="seconds to wait (default 30 min)")
    ap.add_argument("--interval", type=int, default=10, help="seconds between reads")
    ap.add_argument("--once", action="store_true", help="report once and exit; never wait")
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)

    deadline = time.time() + args.timeout
    last_sig = None
    while True:
        waiting = await holding(gs)
        if not waiting:
            print(
                "the human's half is done: no military unit, great general or admiral has movement left"
            )
            await conn.disconnect()
            return 0

        # Print the list when it changes and keep quiet while it does not, so a 30 minute wait is a
        # readable log rather than the same twelve rows every ten seconds. The heartbeat is a
        # timestamp, so silence still says the tool is alive.
        sig = tuple(sorted((u.unit_index, u.x, u.y, u.moves_remaining) for u in waiting))
        if sig != last_sig:
            stamp = time.strftime("%H:%M:%S")
            print(f"{stamp}  {len(waiting)} unit(s) still with the human:")
            for unit in waiting[:12]:
                print(
                    f"  [{unit.unit_index:>2}] {unit.unit_type:<24} ({unit.x},{unit.y}) "
                    f"mv{unit.moves_remaining}"
                )
            if len(waiting) > 12:
                print(f"  ... and {len(waiting) - 12} more")
            last_sig = sig
        else:
            print(f"{time.strftime('%H:%M:%S')}  still waiting on {len(waiting)} unit(s)")

        if args.once:
            print("--once: reporting only, not waiting")
            await conn.disconnect()
            return 1
        if time.time() >= deadline:
            print(f"timed out after {args.timeout}s with {len(waiting)} unit(s) still holding moves")
            await conn.disconnect()
            return 1
        await asyncio.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
