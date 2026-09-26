"""Print the turn (and a few identity facts) a .Civ6Save holds, without loading it.

`rollback-to-turn.py` can read the turn of a *numbered* save from its name, but a manual save
carries the turn inside the file only, and when the parser finds no timeline blocks it says
"turn unknown" and defers to a post-load check. A rollback to the wrong turn is expensive (the
game is relaunched and a save loaded), so this reads the file first and prints what it holds.

Usage:
  .venv\\Scripts\\python.exe scripts\\turn-of-save.py "<path to .Civ6Save>"
  .venv\\Scripts\\python.exe scripts\\turn-of-save.py --list      # every save, newest first

The turn this prints is the one that matters, because the two save families are numbered
differently: measured 2026-09-26 on three consecutive pairs, `0_MCP_NNNN` holds turn NNNN while
the game's own `AutoSave_NNNN` holds turn NNNN-1 (`0_MCP_0142` = T142, `AutoSave_0142` = T141).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

from civ_mcp import game_launcher as gl  # noqa: E402


def parser():
    spec = importlib.util.spec_from_file_location("parse_save", ROOT / "scripts" / "parse_save.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["parse_save"] = module
    spec.loader.exec_module(module)
    return module


def describe(path: Path, module) -> str:
    try:
        meta, _ = module.parse_save(path)
    except Exception as exc:  # noqa: BLE001 - an unreadable save is reported, not raised
        return f"{path.name}: UNREADABLE ({exc})"
    fields = [
        ("turn", getattr(meta, "game_turn", None)),
        ("leader", getattr(meta, "leader", None) or getattr(meta, "civ", None)),
        ("date", getattr(meta, "date", None) or getattr(meta, "game_date", None)),
        ("difficulty", getattr(meta, "difficulty", None)),
    ]
    body = ", ".join(f"{name}={value}" for name, value in fields if value not in (None, ""))
    return f"{path.name}: {body or 'no fields parsed'}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="?", help="a .Civ6Save file")
    ap.add_argument("--list", action="store_true", help="every save in both directories")
    args = ap.parse_args()
    module = parser()

    if args.list:
        paths: list[Path] = []
        for directory in (Path(gl.SAVE_DIR), Path(gl.SINGLE_SAVE_DIR)):
            if directory.is_dir():
                paths.extend(sorted(directory.glob("*.Civ6Save")))
        paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for path in paths:
            print(describe(path, module))
        return 0

    if not args.path:
        print("give a path, or --list", file=sys.stderr)
        return 2
    path = Path(args.path)
    if not path.is_file():
        print(f"no such file: {path}", file=sys.stderr)
        return 2
    print(describe(path, module))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
