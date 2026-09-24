"""Run a Lua snippet against the live game and print what comes back, line by line.

The MCP exposes named tools; this is the escape hatch for a *question* (a read-only probe) whose
answer is one `print`. It connects to the tuner, sends the snippet, and echoes the raw protocol
lines - no parsing, so nothing is hidden. It never calls a write path, so `--lua` must be read-only
by construction: no `end_turn`, no unit or city orders.

    .venv\\Scripts\\python.exe .tools\\live-lua.py --lua-file .tools\\probes\\loyalty-encoding.lua
    .venv\\Scripts\\python.exe .tools\\live-lua.py --lua "print('TURN|' .. Game.GetCurrentGameTurn())"
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.lua._helpers import SENTINEL  # noqa: E402


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lua", help="a read-only Lua snippet to run")
    ap.add_argument("--lua-file", help="a file holding a read-only Lua snippet")
    ap.add_argument("--state", choices=("ingame", "gamecore"), default="ingame",
                    help="which Lua state to run in (GameCore has the player/tech/civic APIs)")
    args = ap.parse_args()
    if not args.lua and not args.lua_file:
        ap.error("give --lua or --lua-file")

    lua = args.lua if args.lua else pathlib.Path(args.lua_file).read_text(encoding="utf-8")
    if SENTINEL not in lua:
        lua = lua + f'\nprint("{SENTINEL}")\n'

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    try:
        run = conn.execute_write if args.state == "ingame" else conn.execute_read
        lines = await run(lua)
    finally:
        await conn.disconnect()

    for line in lines:
        if line == SENTINEL or line == "---END---":
            continue
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
