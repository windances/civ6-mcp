"""Diagnose the Windows capture paths used by the OCR helpers."""
import sys

sys.path.insert(0, r"C:\mine\mine\ws_dsh\civ6\src")

from PIL import ImageStat  # noqa: E402

from civ_mcp import game_launcher as gl  # noqa: E402

win = gl._find_game_window()
print("WINDOW:", win)

for name, fn in (
    ("capture_window", lambda: gl._capture_window(win.window_id)),
    ("capture_window_win32", lambda: gl._capture_window_win32(win.window_id)),
):
    try:
        img = fn()
        stat = ImageStat.Stat(img.convert("L"))
        print(f"{name}: size={img.size} mean={stat.mean[0]:.1f} extrema={img.convert('L').getextrema()}")
    except Exception as exc:  # noqa: BLE001
        print(f"{name}: FAILED {exc!r}")

try:
    res = gl._ocr_fullscreen()
    print("ocr_fullscreen results:", len(res))
    for row in res[:25]:
        print("   ", row)
except Exception as exc:  # noqa: BLE001
    print("ocr_fullscreen FAILED", repr(exc))
