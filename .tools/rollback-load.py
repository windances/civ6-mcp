"""Finish a rollback: leave the load screen, then load the branch's entry save by file name.

`scripts/rollback-to-turn.py` archives the abandoned branch correctly and then hands the load to
`game_launcher.load_save_from_menu`, which resolves a save **by file name** (`SAVE_DIR/<name>.Civ6Save`
or `SINGLE_SAVE_DIR/<name>.Civ6Save`). The rollback passes the save's *display* name instead
("... 288 ..."), that lookup misses both directories, and the restart ends on the Load Game screen
with the turn unreadable - measured 2026-10-04: `Load: FAILED: Save '<display name>' not found`,
`WARNING: expected turn 288, the game reports turn None`.

Retrying is not enough either: `load_save_from_menu` starts from the **main menu** and waits for
"Single Player", which never appears while the game sits on the load screen, so the retry burns its
whole 180 s budget and reports "the game is still starting".

So this does the two steps by hand, in the order the screen requires:
  1. click Back, so the main menu is where the loader expects it;
  2. `_navigate_to_save_sync(name, tab)`, which is the same function the loader would have called,
     with the tab chosen from where the file actually lives (`auto/` -> the Autosaves checkbox).

The PrintWindow / SetForegroundWindow pair is patched out for the same reason
`.tools/load-save.py` patches it: a capture during the loading phase has already made one game
disappear.

    python .tools/rollback-load.py AutoSave_0289
"""

from __future__ import annotations

import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from PIL import ImageGrab  # noqa: E402

from civ_mcp import game_launcher as gl  # noqa: E402

NAME = sys.argv[1] if len(sys.argv) > 1 else "AutoSave_0289"


def safe_capture(window_id=None):  # noqa: ARG001 - signature matches what we replace
    win = gl._find_game_window()
    if win is None:
        raise RuntimeError("no Civilization VI window found")
    return ImageGrab.grab(
        bbox=(win.x, win.y, win.x + win.w, win.y + win.h), all_screens=True
    )


gl._capture_window_win32 = safe_capture
gl._capture_window = safe_capture


def screen_kind() -> str:
    win = gl._find_game_window()
    if win is None:
        return "no-window"
    try:
        return gl._screen_kind(gl._ocr_game_window(win))
    except Exception as exc:  # noqa: BLE001
        return f"screen-read-failed: {exc}"


print(f"before: screen={screen_kind()}")

# 1. Back to the main menu. The label is localized; try the ones this game uses.
if "load" in screen_kind() or "Load" in screen_kind():
    for label in ("返回", "Back", "BACK"):
        if gl._click_text([label], timeout=6):
            print(f"clicked {label!r}")
            break
    else:
        print("could not find a Back button; trying the loader anyway")
    time.sleep(2)

print(f"after back: screen={screen_kind()}")

# 2. Load, choosing the tab from where the file lives - exactly as the loader does.
auto_path = pathlib.Path(gl.SAVE_DIR) / f"{NAME}.Civ6Save"
single_path = pathlib.Path(gl.SINGLE_SAVE_DIR) / f"{NAME}.Civ6Save"
if auto_path.exists():
    tab = "autosaves"
elif single_path.exists():
    tab = None
else:
    print(f"REFUSING: neither {auto_path} nor {single_path} exists")
    raise SystemExit(2)

print(f"navigating to {NAME} (tab={tab!r})")
print(gl._navigate_to_save_sync(NAME, tab))
time.sleep(2)
print(f"final: screen={screen_kind()}  turn={gl._game_turn_number()}")
