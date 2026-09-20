"""Capture the Civ6 window, report brightness stats, and save a downscaled PNG."""
import sys

sys.path.insert(0, r"C:\mine\mine\ws_dsh\civ6\src")

from PIL import Image, ImageStat  # noqa: E402

from civ_mcp import game_launcher as gl  # noqa: E402

win = gl._find_game_window()
print("WINDOW:", win)
if win is None:
    raise SystemExit("no game window")

img = gl._capture_window(win.window_id)
print("capture size:", img.size if hasattr(img, "size") else "?")
stat = ImageStat.Stat(img.convert("L"))
print("mean brightness:", stat.mean[0], "extrema:", img.convert("L").getextrema())
small = img.convert("RGB").resize((img.width // 3, img.height // 3))
small.save(r"C:\mine\mine\ws_dsh\civ6\dsh-tools\shot.png")
print("saved dsh-tools/shot.png")
