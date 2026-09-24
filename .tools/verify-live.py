"""Run the read-only live verification against a running game, loading a save first.

Same checks as `.tools/live-capture-test.py`, but the save name lives here as a literal so that
CJK save names never have to survive a PowerShell argument round-trip (which has corrupted text
in this repo before). Nothing here writes to the game: no `end_turn`, no unit orders, no
`--capture`, no `--attack`.

    .venv\\Scripts\\python.exe .tools\\verify-live.py                    # load the newest save
    .venv\\Scripts\\python.exe .tools\\verify-live.py --save "NAME"      # load a specific save
    .venv\\Scripts\\python.exe .tools\\verify-live.py --no-load          # already in a game
    .venv\\Scripts\\python.exe .tools\\verify-live.py --no-load --get-cities   # get_cities' loyalty lines
    .venv\\Scripts\\python.exe .tools\\verify-live.py --no-load --raw-capture  # supply:C/T, raw

`--get-cities` is the one check that goes through the *tool* (`GameState.get_cities` +
`narrate_cities`) rather than the diagnostics: it is the MCP tool the agent reads every turn, so
it is where a loyalty reading has the widest reach. It prints only the lines that carry loyalty.
"""

from __future__ import annotations

import asyncio
import pathlib
import runpy
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
# Same reason live-capture-test.py does it: piped through PowerShell the console encoding is the
# ANSI code page, which turns every CJK city name into mojibake. The proxy path inherited this
# from the imported script; the direct --get-cities path has to do it itself.
sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_SAVE = "\u79e6\u59cb\u7687\uff08\u5927\u4e00\u7edf\uff09 121 \u516c\u5143125\u5e74"

HERE = pathlib.Path(__file__).resolve().parent


async def show_cities() -> int:
    """What `get_cities` says about loyalty, verbatim, for every one of our cities."""
    from civ_mcp import narrate as nr
    from civ_mcp.connection import GameConnection
    from civ_mcp.game_state import GameState

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    try:
        gs = GameState(conn)
        cities, distances = await gs.get_cities()
        text = nr.narrate_cities(cities, distances)
    finally:
        await conn.disconnect()

    print(f"=== get_cities: {len(cities)} cities, loyalty lines only (read-only) ===")
    shown = 0
    for line in (text or "").splitlines():
        if "Loyalty" in line or "loyalty" in line:
            print(line)
            shown += 1
    if not shown:
        print("  (no city reported a loyalty line: all are above 75 and not falling)")
    return 0


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    no_load = "--no-load" in args
    save = DEFAULT_SAVE
    if "--save" in args:
        i = args.index("--save")
        save = args[i + 1]
        del args[i : i + 2]
    args = [a for a in args if a != "--no-load"]

    if "--get-cities" in args:
        if not no_load:
            print("--get-cities reads the game as it stands; pass --no-load to skip this note.")
        return asyncio.run(show_cities())

    sys.argv = ["live-capture-test.py"]
    if not no_load:
        sys.argv += ["--save", save]
    # --cities, --loyalty and --raw-capture are read-only; --estimate needs a unit and a tile, so
    # it stays opt-in, and --capture/--attack order something and are never added here.
    sys.argv += args or ["--cities", "--loyalty"]
    return runpy.run_path(str(HERE / "live-capture-test.py"), run_name="__main__") and 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
