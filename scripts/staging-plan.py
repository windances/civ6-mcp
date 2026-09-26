"""Print the staging plan for a target city, without an MCP session.

    .venv\\Scripts\\python.exe scripts\\staging-plan.py 58 39

The same plan `get_staging_plan` returns to a session, for the moments there is no session:
before a handoff, or while checking a plan somebody else wrote. It is read-only —it issues no
orders —and it takes the single FireTuner connection while it runs, so do not use it while a
session is playing.

The plan answers the three questions the doctrine's step 3b asks (human instruction 2026-09-26:
在集结前，规划集结方案，不能被堵住，不同部队移动力不一样，找到最优集结方案后，才开始执行): who goes
to which ring tile, who cannot fit (they take the ring's supply hexes or hold behind it), and
which turn the assault actually opens. Every distance and turn comes from the game's own
pathfinding.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

from civ_mcp import staging as st  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("x", type=int, help="target city X")
    ap.add_argument("y", type=int, help="target city Y")
    ap.add_argument("--turns", type=int, default=2, help="how many turns ahead to plan")
    ap.add_argument(
        "--next",
        help="the NEXT objective as x,y (the next city, or a barbarian camp): surplus units that"
        " are not needed for the supply line advance toward it instead of idling",
    )
    ap.add_argument(
        "--kill",
        help="a unit to eliminate as x,y (in practice a missionary): the MOBILE surplus (3+"
        " moves, cavalry above all) is sent to the tiles beside it to kill it or block its escape",
    )
    args = ap.parse_args()

    next_x = next_y = kill_x = kill_y = None
    for flag, name in ((args.next, "next"), (args.kill, "kill")):
        if not flag:
            continue
        try:
            x, y = (int(v) for v in flag.replace(" ", "").split(","))
        except ValueError:
            print(f"--{name} wants two integers: --{name} 58,39")
            return 2
        if name == "next":
            next_x, next_y = x, y
        else:
            kill_x, kill_y = x, y

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    try:
        gs = GameState(conn)
        plan = await gs.staging_plan(args.x, args.y, next_x, next_y, kill_x, kill_y)
        print(
            f"ring tiles: {len(plan.ring)}  units: {len(plan.units)}  options: {len(plan.options)}"
            + (f"  next ring: {len(plan.next_ring)}" if plan.next_ring else "")
        )
        print(st.render(st.assign(plan, turns_ahead=args.turns), plan))
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
