"""Split the per-game diary at a turn boundary: keep the past, archive the future.

The diary is keyed per game, not per run, so a rollback to an earlier save leaves
the abandoned branch's entries in the same file. That is bad twice over: the
agent reads them as memory of a future that never happened (get_diary now clamps
them, see server.py::_clamp_diary_to_turn), and a replay that later reaches the
same turn numbers would write a second set of rows for turns that already have
one - two branches interleaved in one file.

This moves the rows after the boundary into a separate archive directory, keeps a
full backup of the originals, and leaves the live file holding exactly one branch.

Usage:
    .venv\\Scripts\\python.exe .tools\\archive-branch.py 59
    .venv\\Scripts\\python.exe .tools\\archive-branch.py 59 --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".civ6-mcp-data"

sys.path.insert(0, str(ROOT / "src"))
from _game import require_game, require_game_pair, current_game_key

from civ_mcp import run_manifest  # noqa: E402

#: The game this archives. It used to be a hardcoded match key, which is wrong twice over: it named
#: one playthrough whatever was loaded, and it was a *flat* path (`DATA/diary_<game>.jsonl`) - so
#: after the runs layout moved every diary into `runs/<run>/`, the split read a file that was not
#: there and moved nothing, silently. It now comes from the current run's manifest and is looked for
#: in the current run first, then every other run, then the flat root for a directory never migrated.
_FALLBACK_GAME = current_game_key()


def _current_game() -> str:
    manifest = run_manifest.load(run_manifest.resolve_data_dir(DATA)) or {}
    civ, seed = manifest.get("civ"), manifest.get("seed")
    return f"{civ}_{seed}" if civ and seed is not None else _FALLBACK_GAME


def _find_diary(game: str) -> tuple[Path, Path]:
    search = [
        run_manifest.resolve_data_dir(DATA),
        *sorted(p for p in (DATA / "runs").glob("*") if p.is_dir()),
        DATA,
    ]
    for base in search:
        diary = base / f"diary_{game}.jsonl"
        if diary.exists():
            return diary, base / f"diary_{game}_cities.jsonl"
    # Nothing found: return the current run's path so `main` can refuse and say where it looked.
    fallback = run_manifest.resolve_data_dir(DATA)
    return fallback / f"diary_{game}.jsonl", fallback / f"diary_{game}_cities.jsonl"


GAME = _current_game()
DIARY, CITIES = _find_diary(GAME)


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path.name}: line {i} is not JSON: {exc}") from exc
    return rows


def write_rows(path: Path, rows: list[dict]) -> None:
    text = "".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")


def turn_of(row: dict) -> int:
    return int(row.get("turn") or 0)


def describe(rows: list[dict]) -> str:
    if not rows:
        return "none"
    turns = sorted({turn_of(r) for r in rows})
    return f"{len(rows)} rows, turns {turns[0]}..{turns[-1]}"


def archive_boundary(boundary: int, dry_run: bool = False) -> int:
    """Split the diary at ``boundary``: turns after it move to an archive. Returns exit code."""
    if not DIARY.exists():
        print(f"{DIARY} not found")
        return 2

    diary = load(DIARY)
    cities = load(CITIES)
    if not diary:
        print(f"{DIARY.name} has no rows")
        return 2

    future = [r for r in diary if turn_of(r) > boundary]
    if not future:
        print(f"nothing after T{boundary} in {DIARY.name} - nothing to archive")
        return 0

    last_turn = max(turn_of(r) for r in future)
    archive = DATA / "branches" / f"abandoned-T{boundary + 1}-T{last_turn}"

    print(f"boundary        T{boundary}")
    print(f"live diary      {DIARY.name}: {describe(diary)}")
    print(f"live cities     {CITIES.name}: {describe(cities)}")
    print(f"to keep         {describe([r for r in diary if turn_of(r) <= boundary])}")
    print(f"to archive      {describe(future)}")
    print(f"archive dir     {archive.relative_to(ROOT)}")

    if dry_run:
        print("\n--dry-run: nothing written")
        return 0

    archive.mkdir(parents=True, exist_ok=True)

    # Full backup first, so the operation is reversible even if the split is wrong.
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = archive / f"backup-{stamp}"
    backup.mkdir(exist_ok=True)
    shutil.copy2(DIARY, backup / DIARY.name)
    if CITIES.exists():
        shutil.copy2(CITIES, backup / CITIES.name)

    write_rows(archive / f"diary_future_T{boundary + 1}_T{last_turn}.jsonl", future)
    write_rows(
        archive / f"diary_cities_future_T{boundary + 1}_T{last_turn}.jsonl",
        [r for r in cities if turn_of(r) > boundary],
    )

    kept = [r for r in diary if turn_of(r) <= boundary]
    kept_cities = [r for r in cities if turn_of(r) <= boundary]
    write_rows(DIARY, kept)
    if CITIES.exists():
        write_rows(CITIES, kept_cities)

    # Verify by reading back, rather than trusting the write.
    check_kept = load(DIARY)
    check_future = load(archive / f"diary_future_T{boundary + 1}_T{last_turn}.jsonl")
    ok = len(check_kept) + len(check_future) == len(diary)
    print(f"\nbackup          {backup.relative_to(ROOT)}")
    print(f"live now        {describe(check_kept)}")
    print(f"archived now    {describe(check_future)}")
    print(f"rows accounted for: {len(check_kept)} + {len(check_future)} = "
          f"{len(check_kept) + len(check_future)} of {len(diary)}  -> {'OK' if ok else 'MISMATCH'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("boundary", type=int, help="last turn to KEEP in the live diary")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return archive_boundary(args.boundary, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
