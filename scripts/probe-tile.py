"""Print the raw TileInfo for one or more tiles: terrain, feature, resource, improvement, owner.

Written for a contradiction the map narration and the city resource list disagreed on: the city
said 北京 had an unimproved NITER at (58,30) while the radius-1 narration of that same tile showed
no resource, and a Builder standing on it was refused a MINE with "tile has
FEATURE_FLOODPLAINS_GRASSLAND ... can build here: IMPROVEMENT_FARM". One of the two reads is wrong
and the answer decides whether Niter is ever improvable on this map.

Usage:
  .venv\\Scripts\\python.exe .tools\\probe-tile.py 58,30 57,27
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("CIV_MCP_DATA_DIR", str(ROOT / ".civ6-mcp-data"))
# The root holds one directory per playthrough plus a `current` pointer; resolve to the
# run before importing anything that reads the variable at import time.
from civ_mcp import run_manifest as _run_manifest  # noqa: E402
os.environ["CIV_MCP_DATA_DIR"] = str(
    _run_manifest.resolve_data_dir(os.environ["CIV_MCP_DATA_DIR"])
)

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402


async def main() -> int:
    if len(sys.argv) < 2:
        print("give tiles as x,y", file=sys.stderr)
        return 2
    wanted = []
    for arg in sys.argv[1:]:
        x, y = (int(v) for v in arg.split(","))
        wanted.append((x, y))

    conn = GameConnection()
    await conn.connect()
    gs = GameState(conn)
    try:
        # One call per tile, radius 0 kept off: ask for radius 1 and filter, which every build
        # accepts.
        for x, y in wanted:
            area = await gs.get_map_area(x, y, radius=1)
            tiles = getattr(area, "tiles", area)
            for tile in tiles:
                if getattr(tile, "x", None) != x or getattr(tile, "y", None) != y:
                    continue
                print(f"--- ({x},{y}) ---")
                for field in tile.__dataclass_fields__:
                    value = getattr(tile, field, None)
                    if value not in (None, [], {}, ""):
                        print(f"  {field}: {value}")
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
