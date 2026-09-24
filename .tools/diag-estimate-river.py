"""Why does the combat estimate not show `river -5` for a pair that crosses a river?

Run the *real* estimate Lua (`build_combat_estimate_query`) with a debug line injected at the river
check, so the answer is the query's own view of `attPlot`, `isRanged` and the crossing call - not a
reconstruction of it. Read-only: `build_combat_estimate_query` only prints an ESTIMATE line.

    .venv\\Scripts\\python.exe .tools\\diag-estimate-river.py 1310724 53 40
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp import lua as lq  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402

CHECK = "if attPlot and tgtPlot:IsRiverCrossingToPlot(attPlot) then"
DEBUG = (
    'print("DBG|isRanged:" .. tostring(isRanged) .. "|ux:" .. tostring(ux) .. "|uy:" .. tostring(uy)'
    ' .. "|attPlot:" .. tostring(attPlot) .. "|tgtPlot:" .. tostring(tgtPlot)'
    ' .. "|cross:" .. tostring(attPlot and tgtPlot:IsRiverCrossingToPlot(attPlot))'
    ' .. "|dist:" .. tostring(dist)'
    ' .. "|range:" .. tostring(unitInfo and unitInfo.Range)'
    ' .. "|rangedCS:" .. tostring(unitInfo and unitInfo.RangedCombat)'
    ' .. "|attPlotRiver:" .. tostring(attPlot and attPlot:IsRiver())) '
)


async def main() -> int:
    unit_id = int(sys.argv[1])
    x, y = int(sys.argv[2]), int(sys.argv[3])
    lua = lq.build_combat_estimate_query(unit_id, x, y)
    if CHECK not in lua:
        print("the river check is not in the built Lua at all:")
        print(lua[:2000])
        return 1
    lua = lua.replace(CHECK, DEBUG + CHECK)

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    try:
        for line in await conn.execute_write(lua):
            print(line)
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
