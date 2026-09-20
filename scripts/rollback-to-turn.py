"""Roll the game back to a chosen turn: archive the future, then restart accordingly.

A rollback is three jobs, and doing only the first one is how a session ends up confused:

  1. **Archive the future.** Every autosave after the target turn is copied into a
     timestamped folder with a manifest, so the abandoned branch can be replayed, compared
     or restored later. The game prunes autosaves, so the archive also records that the set
     may be partial.
  2. **Archive the diary.** The diary is keyed per game, so the abandoned branch's rows sit
     in the same file the agent reads as memory. They are split off at the boundary
     (``.tools/archive-branch.py`` does the split; this calls it).
  3. **Restart the right way for the state the game is actually in.** That is not one
     command: with a game in progress the main menu is not on screen, so a bare load would
     wait out its timeouts - the launcher's own guard refuses it - while a game already at
     the main menu needs no restart at all, and a game that is not running needs a launch
     first. This script asks the game where it is and picks.

Usage:
  .venv\\Scripts\\python.exe scripts\\rollback-to-turn.py 59            # plan only
  .venv\\Scripts\\python.exe scripts\\rollback-to-turn.py 59 --apply    # archive + roll back
  .venv\\Scripts\\python.exe scripts\\rollback-to-turn.py 59 --archive-only
  .venv\\Scripts\\python.exe scripts\\rollback-to-turn.py 59 --force    # even if another session plays
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# The console on this machine is cp936, and save names are often Chinese: without this the
# candidate list is mojibake exactly when the user needs to read it.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - an old interpreter or a redirected stream
        pass

from civ_mcp import game_launcher as gl  # noqa: E402

ARCHIVE_ROOT = ROOT / ".civ6-mcp-data" / "branches"


def save_turn_from_file(path: Path) -> int | None:
    """The turn a save really holds, read from the file itself.

    A named save - a scenario entry point, a manual save - carries no turn in its name, and
    those are exactly the saves a rollback targets. The parser is the same one the diary
    import uses, so the plan states the turn it is about to load instead of discovering it
    afterwards.
    """
    spec = importlib.util.spec_from_file_location(
        "parse_save", ROOT / "scripts" / "parse_save.py"
    )
    if spec is None or spec.loader is None:
        return None
    try:
        module = importlib.util.module_from_spec(spec)
        # Register before executing: a module that is not in sys.modules breaks @dataclass,
        # which looks its own annotations up through sys.modules[cls.__module__].
        sys.modules["parse_save"] = module
        spec.loader.exec_module(module)
        meta, _ = module.parse_save(path)
        return int(meta.game_turn) or None
    except Exception:  # noqa: BLE001 - an unreadable save is labelled "?" and that is all
        return None


def load_archive_branch_module():
    """Import .tools/archive-branch.py (hyphenated name, so by path)."""
    path = ROOT / ".tools" / "archive-branch.py"
    spec = importlib.util.spec_from_file_location("archive_branch", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["archive_branch"] = module
    spec.loader.exec_module(module)
    return module


def turn_of_save(path: Path) -> int | None:
    import re

    match = re.search(r"(\d+)$", path.stem)
    return int(match.group(1)) if match else None


def inventory() -> list[dict]:
    """Every save on disk, with its directory and turn."""
    out = []
    for directory, kind in ((Path(gl.SINGLE_SAVE_DIR), "mcp"), (Path(gl.SAVE_DIR), "game")):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.Civ6Save")):
            stat = path.stat()
            out.append(
                {
                    "path": path,
                    "name": path.stem,
                    "dir": kind,
                    "turn": turn_of_save(path),
                    "bytes": stat.st_size,
                    "mtime": stat.st_mtime,
                }
            )
    out.sort(key=lambda row: (row["turn"] if row["turn"] is not None else -1, row["mtime"]))
    return out


def pick_target(saves: list[dict], turn: int, wanted: str | None = None) -> dict | None:
    """The save to load: an explicit name, else the save written at the start of ``turn``.

    Rollbacks often target a *named* save - a scenario entry point or a manual ground-control
    save - whose name carries no turn number, so an exact-turn search cannot find it. That is
    why ``--save`` exists and why the no-match case lists candidates instead of just failing.
    """
    if wanted:
        matches = [s for s in saves if s["name"].lower() == wanted.lower().removesuffix(".civ6save").lower()]
        return sorted(matches, key=lambda s: (s["dir"] != "mcp", -s["mtime"]))[0] if matches else None
    exact = [s for s in saves if s["turn"] == turn]
    if not exact:
        return None
    return sorted(exact, key=lambda s: (s["dir"] != "mcp", -s["mtime"]))[0]


def candidates(saves: list[dict], turn: int, limit: int = 8) -> list[dict]:
    """Saves worth offering when nothing matches the target turn exactly.

    Saves whose name carries a turn come first, nearest to the target; named saves (no turn
    in the name) follow, newest first, because their turn can only be read by parsing them.
    """
    numbered = sorted(
        (s for s in saves if s["turn"] is not None),
        key=lambda s: (abs(s["turn"] - turn), s["turn"]),
    )
    named = sorted((s for s in saves if s["turn"] is None), key=lambda s: -s["mtime"])
    return (numbered + named)[:limit]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def archive_saves(
    saves: list[dict], target: int, current: int | None, stamp: str, wanted: str | None = None
) -> Path:
    """Copy every save after ``target`` into a timestamped folder, with a manifest."""
    future = [s for s in saves if s["turn"] is not None and s["turn"] > target]
    # The name states the span actually archived, not the game's current turn: saves from
    # earlier branches can sit far above it (T175 alongside T61), and a folder called
    # "from-T73-T72" describes neither.
    turns = [s["turn"] for s in future]
    if turns:
        span = f"T{min(turns)}-T{max(turns)}"
    else:
        span = f"T{target + 1}-T{current if current is not None else target + 1}"

    # Idempotent: an archive for the same target and span is reused rather than duplicated.
    # A second run of this script otherwise copies the whole branch again (127 MB measured),
    # and running it twice is exactly what a cautious operator does.
    existing = sorted(ARCHIVE_ROOT.glob(f"rollback-to-T{target}-from-{span}-*"))
    reused = bool(existing)
    archive = existing[-1] if reused else ARCHIVE_ROOT / f"rollback-to-T{target}-from-{span}-{stamp}"
    (archive / "saves").mkdir(parents=True, exist_ok=True)
    if reused:
        print(f"reusing archive   {archive.relative_to(ROOT)} (same target and span)")

    manifest = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "rolled_back_to": target,
        "was_at_turn": current,
        "archive": str(archive.relative_to(ROOT)),
        "note": (
            "Autosaves written after the rollback point. The game prunes autosaves "
            "(MCP keeps 8, the game keeps 5), so the earliest turns of the abandoned "
            "branch may already be gone - what existed at archive time is what is here."
        ),
        "saves": [],
    }
    if reused:
        # Keep what an earlier run recorded: this run only adds what is missing.
        try:
            previous = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
            manifest["saves"] = list(previous.get("saves") or [])
            manifest["first_archived"] = previous.get("created")
            manifest["entry_point"] = previous.get("entry_point")
        except Exception:  # noqa: BLE001 - an unreadable manifest is rebuilt from scratch
            pass

    already = {entry["name"]: entry for entry in manifest["saves"]}
    copied_again = 0
    for save in future:
        destination = archive / "saves" / f"{save['name']}.Civ6Save"
        if destination.exists() and already.get(save["name"], {}).get("bytes") == save["bytes"]:
            copied_again += 1
            continue
        shutil.copy2(save["path"], destination)
        already[save["name"]] = {
            "name": save["name"],
            "turn": save["turn"],
            "from": f"{save['dir']}:{save['path'].name}",
            "bytes": save["bytes"],
            "mtime": datetime.fromtimestamp(save["mtime"]).isoformat(timespec="seconds"),
            "sha256": sha256(destination),
        }
    manifest["saves"] = [already[name] for name in sorted(already, key=lambda n: already[n]["turn"])]
    if reused:
        manifest["last_reused"] = datetime.now().isoformat(timespec="seconds")
        print(f"                  {len(future) - copied_again} new save(s), "
              f"{copied_again} already archived")

    # The save being loaded is kept too: a rollback is more useful when the exact entry
    # point travels with the branch it came from.
    entry = pick_target(saves, target, wanted)
    if entry:
        destination = archive / "saves" / f"{entry['name']}.Civ6Save"
        if not destination.exists():
            shutil.copy2(entry["path"], destination)
        manifest["entry_point"] = {
            "name": entry["name"],
            "from": f"{entry['dir']}:{entry['path'].name}",
            "sha256": sha256(destination),
        }

    (archive / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (archive / "README.txt").write_text(
        f"Abandoned branch archived {manifest['created']} before rolling back to T{target}.\n"
        f"Save files: {len(manifest['saves'])} (turns "
        f"{min([s['turn'] for s in manifest['saves']], default=target + 1)}.."
        f"{max([s['turn'] for s in manifest['saves']], default=target)}).\n"
        f"Diary rows for the same span may sit beside this folder under branches/.\n"
        f"To restore one: copy its .Civ6Save back into the game's Saves\\Single directory.\n"
        f"To compare branches: .tools/compare-branches.py\n",
        encoding="utf-8",
    )
    return archive


def assess() -> dict:
    """Where the game is right now, in the terms the decision below needs."""
    pids = gl._running_game_pids()
    other = gl._other_active_session()
    turn = gl._game_turn_number() if pids else None
    tuner = gl._is_tuner_port_open()
    newest = gl.get_newest_save()
    return {
        "running": bool(pids),
        "pids": pids,
        "other_session": other,
        "turn": turn,
        "tuner": tuner,
        "newest_save": newest[0] if newest else None,
    }


def decide(state: dict, target: int, entry: dict | None) -> tuple[str, str]:
    """The restart this state calls for, and why. Returns (action, reason)."""
    if state["other_session"]:
        return (
            "refuse",
            f"another session is playing ({state['other_session']}) - killing or loading "
            "now would interrupt it mid-turn",
        )
    if entry is None:
        return "refuse", f"no save exists for turn {target}"
    if not state["running"]:
        return "launch-then-load", "the game is not running, so it has to be launched first"
    if state["turn"] is None:
        return (
            "load-from-menu",
            "the game is up with no match loaded, so the main menu is on screen",
        )
    if state["turn"] == target:
        return "already-there", f"the game is already at turn {target}"
    if state["turn"] > target:
        return (
            "restart-and-load",
            f"a game is in progress at turn {state['turn']}: the main menu is not on screen, "
            "so the load needs a kill and relaunch",
        )
    return (
        "refuse",
        f"the game is at turn {state['turn']}, which is *before* turn {target} - this is not "
        "a rollback; load a later save explicitly if that is what you want",
    )


async def apply_plan(action: str, name: str, target: int, force: bool) -> str:
    if action == "load-from-menu":
        return await gl.load_save_from_menu(name)
    if action == "launch-then-load":
        launch = await gl.launch_game()
        return f"{launch} | Load: {await gl.load_save_from_menu(name)}"
    if action == "restart-and-load":
        return await gl.restart_and_load(name, force=force)
    return "nothing to do"


def verify(target: int, timeout: float = 120) -> int | None:
    deadline = time.time() + timeout
    turn = None
    while time.time() < deadline:
        turn = gl._game_turn_number()
        if turn == target:
            return turn
        time.sleep(3)
    return turn


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("turn", type=int, help="the turn to roll back to")
    parser.add_argument("--save", help="entry save by name when it carries no turn number")
    parser.add_argument("--apply", action="store_true", help="archive and roll back")
    parser.add_argument("--archive-only", action="store_true", help="archive, touch no game")
    parser.add_argument("--force", action="store_true", help="proceed despite another session")
    parser.add_argument("--no-diary", action="store_true", help="skip the diary split")
    args = parser.parse_args()
    target = args.turn

    saves = inventory()
    entry = pick_target(saves, target, args.save)
    state = assess()
    stamp = time.strftime("%Y%m%d-%H%M%S")

    # A named save's turn lives in the file, not in its name: read it before deciding, so the
    # plan states the turn it will load and a wrong entry point is caught before anything runs.
    entry_turn_note = ""
    if entry is not None and entry["turn"] is None:
        parsed = save_turn_from_file(entry["path"])
        if parsed is not None:
            entry["turn"] = parsed
            entry_turn_note = f" (turn {parsed}, read from the file)"
        else:
            entry_turn_note = (
                " (turn unknown: the name carries none and this save has no timeline "
                "blocks to read it from - the rollback verifies after loading)"
            )
    if entry is not None and entry["turn"] is not None and entry["turn"] != target:
        if args.force:
            print(f"NOTE: entry save '{entry['name']}' holds turn {entry['turn']}, not {target}; "
                  f"--force accepts it and rolls back to {entry['turn']} instead")
            target = entry["turn"]
        else:
            print(f"rollback target      T{target}")
            print(f"entry save           {entry['name']} holds turn {entry['turn']}, not {target}")
            print("\nrefusing: pass that turn instead, choose another save, or add --force "
                  "to roll back to the save's own turn")
            return 2

    action, reason = decide(state, target, entry)

    entry_label = f"{entry['name']} ({entry['dir']}){entry_turn_note}" if entry else "MISSING"
    future = [s for s in saves if s["turn"] is not None and s["turn"] > target]
    print(f"rollback target      T{target}")
    print(f"game state           running={state['running']} turn={state['turn']} "
          f"tuner={'listening' if state['tuner'] else 'down'} newest_save={state['newest_save']}")
    print(f"other session        {state['other_session'] or 'none'}")
    print(f"entry save           {entry_label}")
    print(f"saves after T{target}  {len(future)}")
    for save in future:
        print(f"   T{save['turn']:<4d} {save['name']:<20s} {save['dir']:<5s} "
              f"{save['bytes']:>9d}B  {datetime.fromtimestamp(save['mtime']):%m-%d %H:%M}")
    print(f"decision             {action}")
    print(f"   because           {reason}")

    if action == "refuse":
        if entry is None:
            print(f"\nno save for T{target}. Nearest saves (name, turn, dir, written):")
            for save in candidates(saves, target):
                turn = save["turn"] if save["turn"] is not None else "?"
                print(f"   {save['name']:<22s} T{turn!s:<5s} {save['dir']:<5s} "
                      f"{datetime.fromtimestamp(save['mtime']):%m-%d %H:%M}")
            print("\nIf the entry point is a named save (a scenario or a manual save whose "
                  "name carries no turn), pass it explicitly:\n"
                  f"   scripts\\rollback-to-turn.py {target} --save <name> [--apply]")
        print("\nrefusing: nothing was archived and the game was not touched")
        return 2

    if not (args.apply or args.archive_only):
        print(f"\nplan only. would archive to "
              f"{ARCHIVE_ROOT.relative_to(ROOT)}\\rollback-to-T{target}-from-...-{stamp} and "
              f"then {action}.")
        print("re-run with --apply to do it, or --archive-only to back up without touching the game.")
        return 0

    if not args.no_diary:
        module = load_archive_branch_module()
        if module is None:
            print("diary split   skipped (.tools/archive-branch.py not found)")
        else:
            print("\n--- diary split ---")
            code = module.archive_boundary(target, dry_run=False)
            print(f"diary split   exit {code}")

    archive = archive_saves(saves, target, state["turn"], stamp, args.save)
    print(f"\narchived      {archive.relative_to(ROOT)}")
    print(f"              {len(json.loads((archive / 'manifest.json').read_text(encoding='utf-8'))['saves'])} save file(s) + manifest.json + README.txt")

    if args.archive_only:
        print("\n--archive-only: the game was not touched")
        return 0

    print(f"\n--- rollback: {action} ---")
    result = asyncio.run(apply_plan(action, entry["name"], target, args.force))
    print(result)

    turn = verify(target)
    if turn == target:
        print(f"\nVERIFIED: the game is at turn {target}")
        return 0
    print(f"\nWARNING: expected turn {target}, the game reports turn {turn}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
