"""Print the target report for a city or camp, without an MCP session.

    .venv\\Scripts\\python.exe scripts\\target-report.py 58 42
    .venv\\Scripts\\python.exe scripts\\target-report.py 58 42 --reinforcements

The same block `get_target_report` returns to a session, for the moments there is no session:
the war rehearsal in `docs/retrospectives/2026-10-02-war-execution-rehearsal.md` is run this way,
because the session that wrote it does not hold the civ6 MCP tool surface.

It is **read-only** - it issues no orders - and it takes the single FireTuner connection while it
runs, so do not use it while a session is playing. `--reinforcements` adds the second half
(`get_reinforcements`): which turn each unit still in a queue reaches the rally.

The report is the pre-war analysis itself, in `tactics/07`'s order: the tile and its visibility,
the city on it (walls, HP pool, garrison, defence), the visible enemies within three tiles, and
the staging plan with its per-tile `FIRE` / `NO LINE OF SIGHT` verdicts. It works **before a
declaration** and in fog - which is the point: Gate 0 is "a candidate city is actually visible",
and Gates 1-3 are answered here.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# The data root holds one directory per playthrough plus a current pointer; resolve to the run
# before anything imports a module that reads CIV_MCP_DATA_DIR at import time.
import os as _os
from civ_mcp import run_manifest as _run_manifest
_os.environ.setdefault('CIV_MCP_DATA_DIR', str(pathlib.Path(__file__).resolve().parents[1] / '.civ6-mcp-data'))
_os.environ['CIV_MCP_DATA_DIR'] = str(_run_manifest.resolve_data_dir(_os.environ['CIV_MCP_DATA_DIR']))

from civ_mcp import narrate as nr  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("x", type=int, help="target tile x")
    ap.add_argument("y", type=int, help="target tile y")
    ap.add_argument(
        "--radius", type=int, default=3, help="how far to look for enemy units (default 3)"
    )
    ap.add_argument(
        "--reinforcements",
        action="store_true",
        help="also print which turn each queued unit reaches the rally",
    )
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    try:
        gs = GameState(conn)
        report = await gs.target_report(args.x, args.y, radius=args.radius)
        print(nr.narrate_target_report(report))
        if args.reinforcements:
            print()
            print(nr.narrate_reinforcements(await gs.reinforcements(args.x, args.y)))
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
