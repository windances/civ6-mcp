"""Show the check-file sweep end to end, on a copy of the shipped rule file.

Read-only with respect to the game and to the repository: the shipped
`prompts/checks/turn-checks.md` is copied into a scratch directory, and the hook is then run
against that copy with a fake army that satisfies one goal (a Battering Ram) and a diary row
from the live T60 position. Prints the events the agent would see, a unified diff of the rule
file, and the backup that was taken.

    .venv\\Scripts\\python.exe .tools\\show-check-prune.py
"""

from __future__ import annotations

import asyncio
import difflib
import os
import pathlib
import shutil
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCRATCH = ROOT / ".tools" / f"_prune_demo_{uuid.uuid4().hex}"
SHIPPED = ROOT / "prompts" / "checks" / "turn-checks.md"


class Snap:
    turn = 61

    def __init__(self, units):
        self.units = units


class GS:
    """Only what the check hook touches."""

    def __init__(self, units):
        self._last_snapshot = Snap(units)
        self._briefing_turn = None

    async def get_game_identity(self):
        return ("china", -1894041591)

    async def _take_snapshot(self):
        return self._last_snapshot


def units():
    from civ_mcp.lua import models as m

    def unit(uid, kind):
        return m.UnitInfo(
            unit_id=uid, unit_index=uid, name=kind, unit_type=kind, x=0, y=0,
            moves_remaining=2, max_moves=2, health=100, max_health=100,
        )

    return {i: unit(i, kind) for i, kind in enumerate(
        ["UNIT_BATTERING_RAM", "UNIT_ARCHER", "UNIT_MAN_AT_ARMS", "UNIT_BUILDER"], start=1
    )}


def main() -> int:
    checks = SCRATCH / "turn-checks.md"
    SCRATCH.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SHIPPED, checks)
    os.environ["CIV_MCP_TURN_CHECKS"] = str(checks)
    os.environ["CIV_MCP_DATA_DIR"] = str(SCRATCH / "data")
    (SCRATCH / "data").mkdir(exist_ok=True)

    from civ_mcp import end_turn as et

    before = checks.read_text(encoding="utf-8")

    async def no_rows(_gs):
        return []

    et._agent_diary_rows = no_rows
    gs = GS(units())
    events = asyncio.run(et._check_turn_checks(gs, 61, gs._last_snapshot.units, {"wonders": 0}))

    print("events the agent sees at the end of the turn:")
    for event in events:
        print(f"  [p{event.priority}/{event.category}] {event.message}")

    after = checks.read_text(encoding="utf-8")
    print("\nrule file diff (shipped -> after the sweep):")
    for line in difflib.unified_diff(
        before.splitlines(), after.splitlines(), "turn-checks.md", "turn-checks.md", lineterm=""
    ):
        print(f"  {line}")

    archive = SCRATCH / "archive"
    print("\nbackups:")
    for path in sorted(archive.glob("*.md")):
        same = path.read_text(encoding="utf-8") == before
        print(f"  {path.relative_to(SCRATCH)}  ({path.stat().st_size} bytes, pre-edit: {same})")

    print("\nsecond sweep (idempotence):")
    from civ_mcp import turn_checks

    removed, backup = turn_checks.sweep_achieved(checks, {"ram-tower-before-civil-engineering": 61}, "again")
    print(f"  removed={removed} backup={backup}")

    import re

    left = [c.check_id for c in turn_checks.parse_checks(after)]
    print(f"\nrules left in the file: {', '.join(left) or '(none)'}")
    print(f"trace line: {re.search(r'<!-- achieved.*?-->', after).group(0)}")

    shutil.rmtree(SCRATCH, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
