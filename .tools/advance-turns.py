"""Advance several turns without a round trip per interruption.

The play loop's expensive part is not the game, it is the number of separate calls: an AI
diplomacy session blocks `end_turn`, and answering it costs a call, and there can be two or three
of them a turn. Measured T292-T293: five `end` calls, three of which returned the same
"call end_turn() again" answer, and 43 units skipped in a turn that never advanced.

So this drains whatever is blocking and then ends the turn, repeatedly:

  - a pending diplomacy session is answered here. **Phoenicia (the civ we are at war with) is
    always NEGATIVE** - the directive forbids peace, and a war session is where peace is offered.
    Every other civ is answered POSITIVE, because a second front is what the strategy cannot
    afford and nothing else on offer is worth a refusal.
  - `skip_remaining_units` is *not* called: `execute_end_turn` handles the unit blocker itself,
    and skipping first is what threw 43 units' movement away on a turn that never advanced.

    python .tools/advance-turns.py --turns 3
    python .tools/advance-turns.py --turns 2 --march 27:33,16 23:38,15

`--march` runs the given move orders at the START of every turn, before anything can skip them.
Order syntax is `INDEX:X,Y` and the index is a `unit_index` (the number in brackets in
`play-turn.py units`), **not** the `unit_id` the staging plan reports - passing a unit_id silently
matches nothing, which is how a march was issued and no unit moved.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from civ_mcp import end_turn as end_turn_module  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

WAR_ENEMY = 5  # Phoenicia: the civ this operation declared on
MAX_DRAIN = 6


async def current_turn(gs) -> int:
    overview = await gs.get_game_overview()
    return int(getattr(overview, "turn", 0) or 0)


async def drain_diplomacy(gs) -> int:
    """Answer every open session. Returns how many were answered."""
    answered = 0
    for _ in range(MAX_DRAIN):
        sessions = await gs.get_diplomacy_sessions()
        if not sessions:
            return answered
        for session in sessions:
            pid = int(getattr(session, "other_player_id", 0) or 0)
            response = "NEGATIVE" if pid == WAR_ENEMY else "POSITIVE"
            try:
                reply = await gs.diplomacy_respond(pid, response)
            except Exception as exc:  # noqa: BLE001
                print(f"    p{pid} respond {response} failed: {exc}")
                continue
            answered += 1
            print(f"    p{pid} {response} -> {reply}")
        await asyncio.sleep(1.5)
    return answered


async def march(gs, orders: list[tuple[int, int, int]]) -> None:
    """One move per order, re-reading the unit list between them.

    An order names an index; `get_units` is re-read inside the loop so a unit that stopped
    mid-path cannot be picked twice or block the one behind it.
    """
    spent: set[int] = set()
    for index, tx, ty in orders:
        for unit in await gs.get_units():
            if unit.unit_index != index or unit.unit_index in spent:
                continue
            if unit.moves_remaining <= 0:
                print(f"    [{index}] no moves left")
                spent.add(index)
                break
            reply = await gs.move_unit(unit.unit_index, tx, ty)
            spent.add(unit.unit_index)
            print(f"    [{index}] {unit.unit_type} ({unit.x},{unit.y}) -> ({tx},{ty})")
            print(f"      {reply}")
            break
        else:
            print(f"    [{index}] not found")


def parse_orders(specs: list[str]) -> list[tuple[int, int, int]]:
    orders: list[tuple[int, int, int]] = []
    for spec in specs:
        index, _, tile = spec.partition(":")
        tx, ty = (int(v) for v in tile.split(","))
        orders.append((int(index), tx, ty))
    return orders


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=1)
    ap.add_argument("--march", action="append", default=[], metavar="INDEX:X,Y")
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    orders = parse_orders(args.march)

    start = await current_turn(gs)
    print(f"starting turn: {start}")
    target = start + args.turns

    for _ in range(args.turns * 4):
        turn = await current_turn(gs)
        if turn >= target:
            break
        if orders:
            print(f"  T{turn}: march")
            await march(gs, orders)
        print(f"  T{turn}: drain diplomacy")
        await drain_diplomacy(gs)
        print(f"  T{turn}: end")
        try:
            reply = await end_turn_module.execute_end_turn(gs)
        except Exception as exc:  # noqa: BLE001
            print(f"    end raised: {exc}")
            break
        text = str(reply or "")
        print(f"    {text[:600]}")
        await asyncio.sleep(2)

    end = await current_turn(gs)
    print(f"final turn: {end}  (asked for {target})")
    return 0 if end >= target else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
