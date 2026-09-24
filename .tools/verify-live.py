"""Run the read-only live verification against a running game, loading a save first.

Same checks as `.tools/live-capture-test.py`, but the save name lives here as a literal so that
CJK save names never have to survive a PowerShell argument round-trip (which has corrupted text
in this repo before). Nothing here writes to the game: no `end_turn`, no unit orders, no
`--capture`, no `--attack`.

    .venv\\Scripts\\python.exe .tools\\verify-live.py                    # load the newest save
    .venv\\Scripts\\python.exe .tools\\verify-live.py --save "NAME"      # load a specific save
    .venv\\Scripts\\python.exe .tools\\verify-live.py --no-load          # already in a game
"""

from __future__ import annotations

import pathlib
import runpy
import sys

DEFAULT_SAVE = "\u79e6\u59cb\u7687\uff08\u5927\u4e00\u7edf\uff09 121 \u516c\u5143125\u5e74"

HERE = pathlib.Path(__file__).resolve().parent


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    no_load = "--no-load" in args
    save = DEFAULT_SAVE
    if "--save" in args:
        i = args.index("--save")
        save = args[i + 1]
        del args[i : i + 2]
    args = [a for a in args if a != "--no-load"]

    sys.argv = ["live-capture-test.py"]
    if not no_load:
        sys.argv += ["--save", save]
    # --cities and --loyalty are read-only; --estimate needs a unit and a tile, so it stays opt-in.
    sys.argv += args or ["--cities", "--loyalty"]
    return runpy.run_path(str(HERE / "live-capture-test.py"), run_name="__main__") and 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
