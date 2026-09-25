"""Test GameState layer against a live game.

Usage:
    uv run python scripts/test_game_state.py                    # smoke test: every reader
    uv run python scripts/test_game_state.py --map 52 36 --radius 3
    uv run python scripts/test_game_state.py --map 52 36 -r 8 --map-only

The map section reads one tile and its ring, `narrate_map` does the presenting, and the same
output is what `get_map_area` returns over MCP - terrain, features, resources, districts, yields,
ownership, `[fog]`, `[my: ...]` for our units and `**[...]**` for foreign ones. `--map` exists
because the interesting tile is usually not the first city: scouting a border means reading a
ring around a spot in the field, which this used to hard-code as city 1 with radius 1.

Requires Civ 6 to be running with EnableTuner=1 and a game in progress.
"""

import argparse
import asyncio
import sys

from civ_mcp.connection import GameConnection
from civ_mcp.game_state import GameState
from civ_mcp.narrate import (
    narrate_overview,
    narrate_units,
    narrate_cities,
    narrate_map,
    narrate_diplomacy,
    narrate_tech_civics,
)

# This console is cp936, and the names being read are Chinese and Cyrillic: without this a
# scouting read prints "(owned by ??????)" exactly where the answer is.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - an old interpreter or a redirected stream
        pass


async def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--map",
        nargs=2,
        type=int,
        metavar=("X", "Y"),
        help="centre the map read on this tile (default: the first city)",
    )
    parser.add_argument("--radius", "-r", type=int, default=1, help="map read radius (default 1)")
    parser.add_argument(
        "--map-only", action="store_true", help="print the map and nothing else"
    )
    args = parser.parse_args()

    conn = GameConnection()
    await conn.connect()
    gs = GameState(conn)

    cities = []
    if not args.map_only:
        # Overview
        ov = await gs.get_game_overview()
        print("=== OVERVIEW ===")
        print(narrate_overview(ov))

        # Units
        units = await gs.get_units()
        print("\n=== UNITS ===")
        print(narrate_units(units))

        # Cities
        cities, distances = await gs.get_cities()
        print("\n=== CITIES ===")
        print(narrate_cities(cities, distances))

    # Map — the requested tile, else the first city, else a default
    if args.map:
        cx, cy = args.map
    else:
        if not cities:  # --map-only skips the section that fills this in
            cities, _ = await gs.get_cities()
        cx, cy = (cities[0].x, cities[0].y) if cities else (0, 0)
    tiles = await gs.get_map_area(cx, cy, args.radius)
    print(f"\n=== MAP (around {cx},{cy}) radius {args.radius} ===")
    print(narrate_map(tiles))

    if not args.map_only:
        # Diplomacy
        civs = await gs.get_diplomacy()
        print("\n=== DIPLOMACY ===")
        print(narrate_diplomacy(civs))

        # Tech/Civics
        tc = await gs.get_tech_civics()
        print("\n=== TECH/CIVICS ===")
        print(narrate_tech_civics(tc))

    await conn.disconnect()


asyncio.run(main())
