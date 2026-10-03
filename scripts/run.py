"""Name this playthrough, and check that the loaded game is the one it names.

The tooling stores everything per ``{civ}_{seed}``, which is derived from whatever game is loaded -
so a session cannot tell that the game was swapped underneath it, and two playthroughs of the same
civ and seed are the same key by construction. This is the smallest thing that fixes the first half:
a manifest that says which run this data directory belongs to and which identity it expects, and a
check that runs at the start of every session.

    run.py status                     # what this directory believes, and what the game says
    run.py init --id china-a --label "China conquest A"
    run.py init --id china-a --label "..." --from-game   # take civ/seed from the loaded game
    run.py touch --turn 116           # record progress (play-turn.py end does this too)
    run.py clear                      # unname this directory

`init --from-game` is the careful way: it reads identity from the game *by default* rather than
taking it on the command line, so the manifest cannot be written against the wrong save.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("CIV_MCP_DATA_DIR", str(ROOT / ".civ6-mcp-data"))

from civ_mcp import run_manifest  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402


async def read_identity() -> tuple[str, int] | None:
    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"  could not reach the game: {exc}")
        return None
    try:
        gs = GameState(conn)
        return await gs.get_game_identity()
    except Exception as exc:  # noqa: BLE001
        print(f"  could not read the identity: {type(exc).__name__}: {exc}")
        return None
    finally:
        await conn.disconnect()


def show(manifest: dict | None, identity: tuple[str, int] | None) -> int:
    target = run_manifest.path()
    print(f"data directory : {target.parent}")
    print(f"manifest       : {target}  ({'present' if target.exists() else 'absent'})")
    if manifest is None:
        print("                 no run is named here; nothing checks which playthrough is loaded")
    else:
        for field in run_manifest.FIELDS:
            print(f"  {field:<14} {manifest.get(field)!r}")
    if identity is None:
        print("game           : unreachable")
        return 0
    print(f"game           : {identity[0]}_{identity[1]}")
    state, detail = run_manifest.verify(manifest, *identity)
    verdict = {
        "unset": "UNNAMED - the directory has no manifest to check against",
        "unnamed": f"NO IDENTITY RECORDED - {detail}",
        "ok": "MATCH",
        "mismatch": f"MISMATCH - {detail}",
    }[state]
    print(f"verdict        : {verdict}")
    return 0 if state in ("ok", "unset", "unnamed") else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="verb", required=True)

    sub.add_parser("status", help="what this directory believes and what the game says")

    init = sub.add_parser("init", help="name this directory as a run")
    init.add_argument("--id", required=True, dest="run_id")
    init.add_argument("--label", default="")
    init.add_argument("--notes", default="")
    init.add_argument("--civ", default="")
    init.add_argument("--seed", type=int, default=0)
    init.add_argument("--from-game", action="store_true", help="take civ/seed from the loaded game")
    init.add_argument("--replace", action="store_true")

    touch = sub.add_parser("touch", help="record how far this run has been played")
    touch.add_argument("--turn", type=int, required=True)

    sub.add_parser("clear", help="remove the manifest")
    args = ap.parse_args()

    if args.verb == "status":
        return show(run_manifest.load(), asyncio.run(read_identity()))

    if args.verb == "init":
        civ, seed = args.civ, args.seed
        if args.from_game or not civ:
            identity = asyncio.run(read_identity())
            if identity is None:
                print("refused: --from-game needs the game, and it could not be read")
                return 1
            civ, seed = identity
            print(f"identity taken from the game: {civ}_{seed}")
        manifest, message = run_manifest.init(
            args.run_id, args.label, civ, seed, args.notes, replace=args.replace
        )
        print(message)
        if manifest is None:
            return 1
        print(f"  run_id={manifest['run_id']!r} expects {manifest['civ']}_{manifest['seed']}")
        return 0

    if args.verb == "touch":
        manifest = run_manifest.touch(args.turn)
        if manifest is None:
            print("no manifest in this directory; run `run.py init` first")
            return 1
        print(f"  {manifest['run_id']}: played to T{manifest['last_turn']}")
        return 0

    if args.verb == "clear":
        target = run_manifest.path()
        if target.exists():
            target.unlink()
            print(f"removed {target}")
        else:
            print("nothing to remove")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
