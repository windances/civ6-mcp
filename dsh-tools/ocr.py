"""Dump OCR text + coordinates from the Civ6 window (or full screen)."""
import sys

sys.path.insert(0, r"C:\mine\mine\ws_dsh\civ6\src")

from civ_mcp import game_launcher as gl  # noqa: E402

win = gl._find_game_window()
print("WINDOW:", win)
if win is not None:
    try:
        results = gl._ocr_game_window(win)
    except Exception as exc:  # noqa: BLE001
        print("game-window OCR failed:", exc)
        results = gl._ocr_fullscreen()
else:
    results = gl._ocr_fullscreen()

print("N:", len(results))
for text, x, y, w, h in results:
    print(f"{text!r}\t{x},{y}\t{w}x{h}")
