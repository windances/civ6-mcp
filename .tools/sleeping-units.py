"""Which units are dormant, and what each one is doing instead of acting.

`UnitInfo` had no activity at all until this session, so a unit in `ACTIVITY_SLEEP` and a unit nobody
had ordered were the same record: full movement, no order, named by nothing. The only way to find a
dormant unit was to notice across turns that it never moved - which is exactly the kind of thing
nobody notices.

The vocabulary is the game's own, from its unit panel (`UnitPanel.lua:4054-4062`):

    ACTIVITY_AWAKE      ready
    ACTIVITY_SLEEP      dormant - it will not wake on its own
    ACTIVITY_HOLD       parked by a skip
    ACTIVITY_OPERATION  running an operation, e.g. a spy
    fortify_turns > 0   fortified (not an activity - the count is what says so)

    python .tools/sleeping-units.py
    python .tools/sleeping-units.py --all      # every unit, grouped by what it is doing
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

# The states that mean "this unit will not act until something wakes it". A fortify is not here on
# purpose: a fortified unit is doing its job, and `end_turn` fortifies by design.
DORMANT = ("ACTIVITY_SLEEP",)


def describe(unit) -> str:
    parts = [str(getattr(unit, "activity", "") or "?"), f"fortify {unit.fortify_turns}"]
    if not unit.ready_to_move:
        parts.append("not ready to move")
    return ", ".join(parts)


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="show every unit, grouped by activity")
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    units = await gs.get_units()

    counts = Counter(str(getattr(u, "activity", "") or "(unknown)") for u in units)
    print(f"=== {len(units)} unit(s), by activity ===")
    for activity, number in counts.most_common():
        print(f"  {activity:<22} {number}")

    dormant = [
        u for u in units if str(getattr(u, "activity", "") or "") in DORMANT
    ]
    print(f"\n=== dormant ({len(dormant)}) ===")
    if not dormant:
        print("  none - nothing is asleep")
    for u in dormant:
        print(f"  [{u.unit_index:>2}] {u.unit_type:<24} ({u.x:>3},{u.y:>3}) {describe(u)}")

    if args.all:
        print("\n=== everything ===")
        for u in sorted(units, key=lambda u: (str(getattr(u, "activity", "")), u.unit_type)):
            print(
                f"  [{u.unit_index:>2}] {u.unit_type:<24} ({u.x:>3},{u.y:>3}) "
                f"mv{u.moves_remaining:<4} {describe(u)}"
            )

    unknown = [u for u in units if not str(getattr(u, "activity", "") or "")]
    if unknown:
        print(
            f"\n  NOTE: {len(unknown)} unit(s) report no activity at all. That is the *unknown* "
            f"reading, not 'awake' - a server started before the column existed answers this way."
        )
    await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
