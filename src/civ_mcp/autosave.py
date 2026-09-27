"""Platform-aware autosave helpers.

On Windows, Network.SaveGame writes custom 0_MCP_NNNN saves reliably.
On Linux (Aspyr port), Network.SaveGame silently fails — we fall back
to the game's own AutoSave_NNNN files in the auto/ subdirectory.
"""

import glob
import logging
import os
import sys

log = logging.getLogger(__name__)

_IS_LINUX = sys.platform == "linux"


def get_latest_autosave() -> str | None:
    """Return the name of the latest autosave (no extension).

    On Windows: latest 0_MCP_NNNN in Single/ dir.
    On Linux: latest AutoSave_NNNN in Single/auto/ dir.
    Returns None if no saves found.
    """
    from .game_launcher import SAVE_DIR, SINGLE_SAVE_DIR

    if _IS_LINUX:
        # Game's own autosaves: auto/AutoSave_NNNN.Civ6Save
        pattern = os.path.join(SAVE_DIR, "AutoSave_*.Civ6Save")
    else:
        # MCP autosaves: 0_MCP_NNNN.Civ6Save
        pattern = os.path.join(SINGLE_SAVE_DIR, "0_MCP_*.Civ6Save")

    saves = glob.glob(pattern)
    if not saves:
        # Cross-platform fallback
        alt_pattern = os.path.join(
            SAVE_DIR if not _IS_LINUX else SINGLE_SAVE_DIR,
            ("0_MCP_*.Civ6Save" if _IS_LINUX else "AutoSave_*.Civ6Save"),
        )
        saves = glob.glob(alt_pattern)

    if not saves:
        return None

    # Sort by modification time, newest first
    saves.sort(key=os.path.getmtime, reverse=True)
    # Return name without extension
    return os.path.splitext(os.path.basename(saves[0]))[0]


def get_autosave_for_turn(turn: int) -> str:
    """Return the expected autosave name for a specific turn.

    On Windows: 0_MCP_NNNN
    On Linux: AutoSave_NNNN (game's own, may not be exact turn match)
    """
    if _IS_LINUX:
        return f"AutoSave_{turn:04d}"
    return f"0_MCP_{turn:04d}"


def saves_work_on_this_platform() -> bool:
    """Whether Network.SaveGame writes custom saves reliably."""
    return not _IS_LINUX


def verified_save_name(written: str, real_turn: int | None) -> str | None:
    """The name an MCP save should carry, given the turn its **file** actually holds.

    `0_MCP_NNNN` is an invariant the recovery verification rests on (`game_launcher._save_turn`,
    `handoff.save_turn`), and it broke in the field: the name is built from the same post-advance
    read that sometimes prints `Turn 203 -> 203`, so measured 2026-09-27 four of the nine newest
    MCP saves held one turn more than their name claimed (`0_MCP_0215` holds T216, `0_MCP_0212`
    holds T213). Returns None when the name is already right, when the file's turn could not be
    read, or when the name is not an MCP save - the game's own `AutoSave_NNNN` deliberately runs
    one ahead of the turn it holds, and renaming it would break that.
    """
    if real_turn is None or not written.startswith("0_MCP_"):
        return None
    expected = f"0_MCP_{real_turn:04d}"
    return None if written == expected else expected
