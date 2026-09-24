"""Wait for Nationalism, walk a chariot next to another, and form a Corps.

The end-to-end test the human asked for. It loops:

1. run `.tools/probes/form-corps.lua` with FORM enabled - if the engine lists a FORM_CORPS target,
   the probe forms the Corps and this script stops, printing what changed;
2. otherwise march the movable Heavy Chariot toward Moscow along the game's own path, skip the
   rest, end the turn, and try again.

Nothing here chooses strategy: the only move is the one that puts two same-type units in reach of
each other, which is the precondition the game sets for the command.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

PROBE = pathlib.Path(".tools/probes/form-corps.lua")
ANCHOR = (54, 40)  # Moscow, where the chariot that took the city sits
MOVER = 2031633  # the Heavy Chariot out at (58,41)


async def attempt(conn, form: bool) -> list[str]:
    lua = PROBE.read_text(encoding="utf-8").replace(
        "FORM_OR_NOT", "true" if form else "false"
    )
    return await conn.execute_write(lua)


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=12)
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    try:
        for i in range(1, args.turns + 1):
            lines = await attempt(conn, form=True)
            joined = "\n".join(lines)
            print(f"--- attempt {i} ---")
            for line in lines:
                if line.startswith(("TARGET", "PAIR", "CAN", "FORM", "AFTER", "COUNT", "UNITS")):
                    print("  " + line)
            if "COUNT|" in joined:
                print("=== the game reported a formation change; stopping. ===")
                return 0

            path = await gs.get_pathing_estimate(MOVER, ANCHOR[0], ANCHOR[1])
            waypoints = [w for w in (path.waypoints or []) if w and w != "()"]
            if len(waypoints) < 2:
                print(f"  mover has no path toward {ANCHOR} ({waypoints}) - stopping.")
                return 0
            dest = waypoints[min(1, len(waypoints) - 1)]
            dx, dy = (int(v) for v in dest.strip("()").split(","))
            moved = await gs.move_unit(MOVER, dx, dy)
            print(f"  march {MOVER} -> {dest}: {moved.strip()[:160]}")
            await gs.skip_remaining_units()
            result = await gs.end_turn()
            m = re.search(r"Turn (\d+) -> (\d+)", result or "")
            print(f"  end_turn: {m.group(0) if m else result.strip()[:160]}")
            if not m:
                # A blocker (diplomacy, civic, world congress) - print and let the caller decide.
                print("  blocked: " + (result or "").strip().splitlines()[0][:160])
                return 0
    finally:
        await conn.disconnect()
    print("=== gave up without forming a Corps ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
