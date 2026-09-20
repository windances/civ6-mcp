"""Click at physical screen coordinates (x y) using the MCP's own click helper."""
import sys

sys.path.insert(0, r"C:\mine\mine\ws_dsh\civ6\src")

from civ_mcp import game_launcher as gl  # noqa: E402

x, y = int(sys.argv[1]), int(sys.argv[2])
gl._click(x, y)
print(f"clicked {x},{y}")
