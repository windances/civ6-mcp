"""Verify the diary path is per-game and that telemetry writes to the same file."""

import sys
from pathlib import Path

sys.path.insert(0, "src")
from _game import require_game, require_game_pair, current_game_key

from civ_mcp.diary import diary_path  # noqa: E402
from civ_mcp.telemetry import LocalSink  # noqa: E402

DATA = Path(r"C:\mine\mine\ws_dsh\civ6\.civ6-mcp-data")
GAME = require_game_pair()
NEW_RUN = "brand-new-run-id"

sink = LocalSink(directory=DATA)
sink.start(NEW_RUN, {})
sink.bind_game(*GAME)

checks = [
    ("diary", diary_path(GAME[0], GAME[1], NEW_RUN).name),
    ("diary_cities", f"diary_{GAME[0]}_{GAME[1]}_cities.jsonl"),
    ("log", f"log_{GAME[0]}_{GAME[1]}_{NEW_RUN}.jsonl"),
]
for kind, expected in checks:
    got = sink._path(kind).name
    verdict = "OK" if got == expected else "MISMATCH"
    print(f"  {kind:14} {got:50} {verdict}")

# The agent's read path must resolve to the migrated file with real history.
p = diary_path(GAME[0], GAME[1], NEW_RUN)
print(f"\n  agent reads : {p.name}")
print(f"  exists      : {p.exists()}")
print(f"  size        : {p.stat().st_size if p.exists() else 0} bytes")
