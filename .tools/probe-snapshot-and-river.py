"""Reproduce (or confirm fixed) the post-turn snapshot failure, and probe the Moscow river edge.

Two read-only things:

1. `GameState._take_snapshot()` - the call that answered
   `LuaError: ERR:Runtime Error: [string "..."]:65: function expected instead of nil` and left
   "no unit list available for T122 at all" after Moscow was captured. It reads four queries
   (overview, units, cities, stockpiles); this prints which one fails and the full traceback.
2. Whether an attack out of Moscow crosses a river - the one shape in which `river -5` can be
   seen, checked with the same call the estimate makes (`units.py`: `tgtPlot:IsRiverCrossingToPlot`).
   pcall's *second* return is the value; reading the first was a bug of mine earlier today.

    .venv\\Scripts\\python.exe .tools\\probe-snapshot-and-river.py
"""

from __future__ import annotations

import asyncio
import pathlib
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp import lua as lq  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

MOSCOW = (54, 40)


async def main() -> int:
    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    try:
        print("=== snapshot ===")
        try:
            snap = await gs._take_snapshot()
            print(f"OK: turn {snap.turn}, {len(snap.units)} units, {len(snap.cities)} cities")
        except Exception:  # noqa: BLE001
            print("FAILED:")
            traceback.print_exc()

        print("\n=== units query, both states ===")
        for state, call in (("InGame(write)", conn.execute_write), ("GameCore(read)", conn.execute_read)):
            try:
                lines = await call(lq.build_units_query())
                got = [x for x in lines if x and not x.startswith("SENTINEL")]
                print(f"  {state}: {len(got)} line(s); first={got[0][:70] if got else '(none)'}")
            except Exception as exc:  # noqa: BLE001
                print(f"  {state}: FAILED {type(exc).__name__}: {str(exc)[:140]}")

        print("\n=== river edges around Moscow ===")
        lua = """
local me = Game.GetLocalPlayer()
local cx, cy = 54, 40
local cityPlot = Map.GetPlot(cx, cy)
for dx = -1, 1 do for dy = -1, 1 do
    local nx, ny = cx + dx, cy + dy
    if (dx ~= 0 or dy ~= 0) and Map.GetPlot(nx, ny)
        and Map.GetPlotDistance(cx, cy, nx, ny) == 1 then
        local ok, cross = pcall(function()
            return cityPlot:IsRiverCrossingToPlot(Map.GetPlot(nx, ny))
        end)
        local who = "empty"
        local stack = Map.GetUnitsAt(nx, ny)
        if stack then
            for u in stack:Units() do
                local info = GameInfo.Units[u:GetType()]
                who = (u:GetOwner() == me and "ours:" or "enemy:")
                    .. tostring(info and info.UnitType or "?")
            end
        end
        print("EDGE|" .. nx .. "," .. ny .. "|river:" .. tostring(ok and cross or false) .. "|" .. who)
    end
end end
print("MOSCOW|owner:" .. tostring(cityPlot and Cities.GetCityInPlot(cx, cy)
    and Cities.GetCityInPlot(cx, cy):GetOwner()))
"""
        for line in await conn.execute_write(lua):
            print("  " + line)
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
