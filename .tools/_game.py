"""Whichever match is loaded right now - resolved, never written down.

Nine tools in this directory had one match's key written into them as a constant, in both the
`<civ>_<seed>` and the `("<civ>", <seed>)` form. That key is this match's: a rollback to a different branch, or a new game, gives a
different one, and a tool that silently reports on the wrong match is worse than one that refuses.
The previous audits missed all nine because the grep tool skips ignored paths and `.tools/` is
ignored - so the tools doing the running were the one place nobody looked.

The run manifest is the authority (`.civ6-mcp-data/runs/<run_id>/run.json`, or the root `run.json`
for a flat tree), because it is what the session banner and `scripts/run.py` already agree on.

    from _game import require_game, require_game_pair

    GAME = require_game()                 # "<civ>_<seed>"
    CIV, SEED = require_game_pair()       # ("<civ>", <seed>)

Both exit with a message rather than returning a default: a tool that cannot tell which match it is
looking at must say so, not pick one.
"""

from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))


def _manifest() -> dict | None:
    try:
        from civ_mcp import run_manifest
    except Exception:  # noqa: BLE001 - a missing library is "no answer", not a crash
        return None
    root = pathlib.Path(__file__).resolve().parents[1] / ".civ6-mcp-data"
    for candidate in (run_manifest.resolve_data_dir(root), root):
        try:
            found = run_manifest.load(candidate)
        except Exception:  # noqa: BLE001
            continue
        if found:
            return found
    return None


def current_game_pair() -> tuple[str, int] | None:
    """`(civ, seed)` for the loaded match, or None when it cannot be resolved.

    `CIV6_GAME` wins when it is set: it is the escape hatch for a tool pointed at a branch that is
    not the current one, and it keeps that choice explicit instead of editing a constant.
    """
    override = os.environ.get("CIV6_GAME")
    if override:
        civ, _, seed = override.partition("_")
        try:
            return civ, int(seed)
        except ValueError:
            return None
    manifest = _manifest()
    if not manifest:
        return None
    civ = str(manifest.get("civ") or "")
    seed = manifest.get("seed")
    if not civ or seed is None:
        return None
    try:
        return civ, int(seed)
    except (TypeError, ValueError):
        return None


def current_game_key() -> str | None:
    """`"<civ>_<seed>"` for the loaded match, or None."""
    pair = current_game_pair()
    return None if pair is None else f"{pair[0]}_{pair[1]}"


def require_game() -> str:
    key = current_game_key()
    if not key:
        raise SystemExit(
            "no current match: the run manifest does not name one. Set CIV6_GAME=<civ>_<seed> or "
            "point CIV6_MCP_DATA_DIR at the run you mean - this tool will not guess."
        )
    return key


def require_game_pair() -> tuple[str, int]:
    pair = current_game_pair()
    if not pair:
        raise SystemExit(
            "no current match: the run manifest does not name one. Set CIV6_GAME=<civ>_<seed> or "
            "point CIV6_MCP_DATA_DIR at the run you mean - this tool will not guess."
        )
    return pair
