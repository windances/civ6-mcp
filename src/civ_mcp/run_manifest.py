"""The run a session belongs to, and the assertion that the game matches it.

Every stored thing the tooling keeps resolves off ``{civ}_{seed}`` - the diary's name, the retired
goals in ``turn-checks-state.json``, the ``(game: ...)`` trace in the rule file. That key is derived
from whatever game happens to be loaded, so a session has no way to notice that the game changed
under it, and two playthroughs of the same civ and seed are indistinguishable by construction
(``diary_path`` accepts ``run_id`` and ignores it, on purpose, so a restart continues the same
diary).

Measured 2026-10-03, and the reason this module exists: a session played on, turn after turn, while
the loaded game had been swapped from ``china_911679432`` to ``china_-1894041591``. Every read
looked fine. Nothing in the tooling compared the game to an expectation, because there was no
expectation to compare it to.

So a run names itself once and then asserts:

* ``run.json`` beside the diary says which run this data directory belongs to and which
  ``(civ, seed)`` it expects;
* every session start reads the game and compares - a match is quiet, a mismatch is loud;
* ``(civ, seed)`` stops being the **key** and becomes the **assertion**. It was never a good key
  (two runs of one seed share it); it is an excellent check, because it is exactly what the game
  can be asked.

This is deliberately the small half of the design: it adds no directories and moves no files, so it
works with the layout that exists today and is what the per-run directory layout would later carry.
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import time

log = logging.getLogger(__name__)

MANIFEST_NAME = "run.json"
FIELDS = ("run_id", "label", "civ", "seed", "created", "last_turn", "notes")

#: The root holds one directory per playthrough under this name, plus a `current` pointer.
RUNS_DIR = "runs"
CURRENT_NAME = "current"


def resolve_data_dir(root: pathlib.Path | str | None = None) -> pathlib.Path:
    """The directory a session should actually read: the **current run's**, when there is one.

    ``CIV_MCP_DATA_DIR`` points at the *root* - the directory that holds ``runs/`` - because that is
    where the pointer lives. Every module that resolves a stored path (the diary, the retired-goal
    state, the heartbeat) then works inside one playthrough's directory and cannot see another's,
    without any of those modules knowing that runs exist.

    Falls back to the root itself when there is no ``runs/`` directory or no pointer, so a checkout
    that has not been migrated behaves exactly as before.
    """
    base = pathlib.Path(
        root
        if root is not None
        else os.environ.get("CIV_MCP_DATA_DIR", pathlib.Path.home() / ".civ6-mcp")
    )
    runs = base / RUNS_DIR
    if not runs.is_dir():
        return base
    pointer = base / CURRENT_NAME
    if not pointer.exists():
        return base
    try:
        run_id = pointer.read_text(encoding="utf-8").strip()
    except OSError:
        return base
    target = runs / run_id
    return target if target.is_dir() else base


def data_root(root: pathlib.Path | str | None = None) -> pathlib.Path:
    """The directory that holds ``runs/`` - where data **shared by every playthrough** belongs.

    Two kinds of stored thing now exist and they resolve differently, which is the distinction that
    is easy to miss when wiring a new entry point:

    * **per-run** - the diary, the retired-goal state, the heartbeat. These resolve
      ``CIV_MCP_DATA_DIR``, which points at the run (``resolve_data_dir``).
    * **shared** - the localization table, the branch archives. These are built once for the machine
      and belong at the root.

    Measured 2026-10-03, right after the drivers started resolving to a run: `localization` looked
    for `loc-en-names.json` inside the run, did not find it, and every English name silently stopped
    working - the degradation is designed to be invisible, which is exactly why this needs a name.

    ``CIV_MCP_DATA_ROOT`` wins when a caller sets it. Otherwise the run directory is recognised by
    its parent being ``runs/``, so a wired driver needs no change.
    """
    explicit = os.environ.get("CIV_MCP_DATA_ROOT")
    if explicit:
        return pathlib.Path(explicit)
    base = pathlib.Path(
        root
        if root is not None
        else os.environ.get("CIV_MCP_DATA_DIR", pathlib.Path.home() / ".civ6-mcp")
    )
    if base.parent.name == RUNS_DIR:
        return base.parent.parent
    return base


def run_ids(root: pathlib.Path | str | None = None) -> list[str]:
    base = pathlib.Path(
        root
        if root is not None
        else os.environ.get("CIV_MCP_DATA_DIR", pathlib.Path.home() / ".civ6-mcp")
    )
    runs = base / RUNS_DIR
    if not runs.is_dir():
        return []
    return sorted(p.name for p in runs.iterdir() if p.is_dir())


def current(root: pathlib.Path | str | None = None) -> str:
    base = pathlib.Path(
        root
        if root is not None
        else os.environ.get("CIV_MCP_DATA_DIR", pathlib.Path.home() / ".civ6-mcp")
    )
    pointer = base / CURRENT_NAME
    try:
        return pointer.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def path(data_dir: pathlib.Path | str | None = None) -> pathlib.Path:
    if data_dir is not None:
        return pathlib.Path(data_dir) / MANIFEST_NAME
    return (
        pathlib.Path(os.environ.get("CIV_MCP_DATA_DIR", pathlib.Path.home() / ".civ6-mcp"))
        / MANIFEST_NAME
    )


def load(data_dir: pathlib.Path | str | None = None) -> dict | None:
    """The manifest, or None when this data directory has never been named."""
    target = path(data_dir)
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - a corrupt manifest is "unnamed", never a crash
        log.warning("run manifest unreadable at %s", target, exc_info=True)
        return None
    return data if isinstance(data, dict) else None


def save(manifest: dict, data_dir: pathlib.Path | str | None = None) -> bool:
    target = path(data_dir)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        # newline="": text mode would rewrite every \n as os.linesep on Windows.
        tmp.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8", newline=""
        )
        tmp.replace(target)
    except OSError:
        log.warning("could not write %s", target, exc_info=True)
        return False
    return True


def make(run_id: str, label: str = "", civ: str = "", seed: int = 0, notes: str = "") -> dict:
    return {
        "run_id": run_id,
        "label": label or run_id,
        "civ": civ,
        "seed": seed,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "last_turn": 0,
        "notes": notes,
    }


def init(
    run_id: str,
    label: str = "",
    civ: str = "",
    seed: int = 0,
    notes: str = "",
    data_dir: pathlib.Path | str | None = None,
    replace: bool = False,
) -> tuple[dict | None, str]:
    """Write a manifest. Refuses to overwrite an existing one unless ``replace``."""
    existing = load(data_dir)
    if existing is not None and not replace:
        return existing, (
            f"refused: {path(data_dir)} already names run {existing.get('run_id')!r}; "
            f"pass --replace to rename it"
        )
    manifest = make(run_id, label, civ, seed, notes)
    if existing and existing.get("last_turn"):
        manifest["last_turn"] = existing["last_turn"]
    return (manifest, "written") if save(manifest, data_dir) else (None, "write failed")


def touch(turn: int, data_dir: pathlib.Path | str | None = None) -> dict | None:
    """Record how far this run has been played. A no-op when there is no manifest."""
    manifest = load(data_dir)
    if manifest is None or not isinstance(turn, int) or turn <= 0:
        return manifest
    if int(manifest.get("last_turn") or 0) < turn:
        manifest["last_turn"] = turn
        save(manifest, data_dir)
    return manifest


def verify(
    manifest: dict | None, civ: str, seed: int
) -> tuple[str, str]:
    """``(state, detail)`` for the game in front of us against the run's expectation.

    ``unset`` - the data directory has no manifest, so there is nothing to assert. ``unnamed`` -
    a manifest exists but recorded no identity. ``ok`` / ``mismatch`` otherwise. ``mismatch`` is the
    one that matters: it is the session being pointed at a different playthrough.
    """
    if manifest is None:
        return "unset", ""
    expected_civ = manifest.get("civ") or ""
    expected_seed = manifest.get("seed") or 0
    if not expected_civ and not expected_seed:
        return "unnamed", f"run {manifest.get('run_id')!r} records no civ/seed to check"
    if str(expected_civ) == str(civ) and int(expected_seed) == int(seed):
        return "ok", ""
    return "mismatch", (
        f"run {manifest.get('run_id')!r} expects {expected_civ}_{expected_seed}, "
        f"the loaded game is {civ}_{seed}"
    )


def lines(civ: str, seed: int, data_dir: pathlib.Path | str | None = None) -> list[str]:
    """The banner lines for the run: one line normally, and a loud one on a mismatch.

    Kept here rather than in the printers so that everything that reports a session reports the same
    thing - a mismatch that only one entry point mentions is a mismatch half the time.
    """
    manifest = load(data_dir)
    state, detail = verify(manifest, civ, seed)
    if state == "unset":
        return [
            "RUN      no run manifest - this session is unlabelled, so nothing checks which "
            "playthrough the game belongs to (scripts/run.py init --id <name> --label <text>)"
        ]
    if state == "ok":
        run_id = manifest.get("run_id")
        label = manifest.get("label") or ""
        last = int(manifest.get("last_turn") or 0)
        suffix = f' "{label}"' if label and label != run_id else ""
        where = f", played to T{last}" if last else ""
        return [f"RUN      {run_id}{suffix}  (civ/seed match{where})"]
    if state == "unnamed":
        return [f"RUN      {detail}"]
    return [
        f"RUN MISMATCH  {detail}",
        "         STOP: this data directory belongs to another playthrough. Playing on writes its "
        "diary, its retired goals and its saves into the wrong run - switch the game or the run "
        "before doing anything else.",
    ]
