"""Watch the match from outside the game, holding no connection.

FireTuner serves exactly one client, so a watcher that queries the game is a watcher that blocks the
player. Everything here is read off the filesystem instead - the newest save and the turn **inside**
it, the newest MCP call log and what its last calls were, and the diary's last agent row - so it can
run while somebody else is playing.

    python .tools/progress.py
    python .tools/progress.py --tail 12
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from civ_mcp import game_launcher as gl  # noqa: E402
from civ_mcp import handoff  # noqa: E402

DATA = ROOT / ".civ6-mcp-data"


def stamp(seconds: float) -> str:
    return time.strftime("%m-%d %H:%M:%S", time.localtime(seconds))


def run_dir() -> pathlib.Path:
    """The run the manifest says is current - not `newest by mtime`, which is another branch."""
    try:
        from civ_mcp import run_manifest

        return run_manifest.resolve_data_dir(DATA)
    except Exception:  # noqa: BLE001
        return DATA


def newest(pattern: str) -> pathlib.Path | None:
    """Newest match **inside the current run**, falling back to the data root.

    Scoped on purpose: a rollback leaves the abandoned branch's files in place with later mtimes than
    anything the new branch has written, so an unscoped search reports the wrong match's progress.
    """
    for base in (run_dir(), DATA):
        found = list(base.glob(pattern))
        if found:
            return max(found, key=lambda p: p.stat().st_mtime)
    return None


def other_branch_files(pattern: str) -> list[str]:
    """Files matching the pattern that are **not** in the current run - named, so they are ignorable."""
    here = run_dir()
    seen: list[str] = []
    for base in (DATA, *[p for p in DATA.glob("runs/*") if p.is_dir()]):
        if base == here:
            continue
        for found in base.glob(pattern):
            seen.append(f"{found.parent.name}/{found.name}")
    return seen


def save_line() -> str:
    newest_save = gl.get_newest_save()
    if not newest_save:
        return "  newest save   : none found"
    name, mtime = newest_save
    path = pathlib.Path(gl.SINGLE_SAVE_DIR) / f"{name}.Civ6Save"
    if not path.exists():
        path = pathlib.Path(gl.SAVE_DIR) / f"{name}.Civ6Save"
    try:
        turn = handoff.save_turn(path) if path.exists() else None
    except Exception:  # noqa: BLE001
        turn = None
    return (
        f"  newest save   : {name}  holds turn {turn}  written {stamp(mtime)}"
        f"   (name says {'?' if turn is None else turn})"
    )


def log_lines(tail: int) -> list[str]:
    path = newest("log_*.jsonl")
    if path is None:
        return ["  no MCP log yet"]
    out = [f"  newest log    : {path.name}  ({path.stat().st_size // 1024} KB, {stamp(path.stat().st_mtime)})"]
    rows = path.read_text(encoding="utf-8", errors="replace").splitlines()[-tail:]
    for row in rows:
        try:
            record = json.loads(row)
        except ValueError:
            continue
        tool = record.get("tool") or record.get("method") or "?"
        result = " ".join(str(record.get("result", ""))[:110].split())
        out.append(f"    {tool:<26} {result}")
    return out


def diary_line() -> str:
    path = newest("diary_*.jsonl")
    if path is None:
        return "  diary         : none"
    rows = path.read_text(encoding="utf-8", errors="replace").splitlines()
    turns = []
    for row in rows[-40:]:
        try:
            record = json.loads(row)
        except ValueError:
            continue
        turn = record.get("turn")
        if isinstance(turn, int):
            turns.append(turn)
    return (
        f"  diary         : {path.name}  {len(rows)} row(s), newest turn "
        f"{max(turns) if turns else '?'}  ({stamp(path.stat().st_mtime)})"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tail", type=int, default=6, help="how many recent calls to show")
    args = ap.parse_args()
    game = gl.game_status().splitlines()[0]
    print(f"  run           : {run_dir().name}")
    print(f"  game          : {game}")
    print(save_line())
    print(diary_line())
    print("\n".join(log_lines(args.tail)))
    strays = other_branch_files("log_*.jsonl") + other_branch_files("diary_*.jsonl")
    if strays:
        print(f"  other branches: {len(strays)} log/diary file(s) not in this run, "
              f"e.g. {strays[0]} - ignored on purpose")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
