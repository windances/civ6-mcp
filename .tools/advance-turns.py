"""Advance several turns, and refuse to call a turn done unless it actually was.

Two jobs, and the second is the one that matters.

**Drain and advance.** An AI diplomacy session blocks `end_turn`, answering it costs a call, and
there can be three a turn. A session with the civ we are at war with is always answered NEGATIVE
(the directive forbids peace, and a war session is where peace is offered); every other civ is
answered POSITIVE, because a second front is what this strategy cannot afford and nothing else on
offer is worth a refusal.

**Verify each turn.** A turn number going up is not evidence a turn worked. Measured 2026-10-04: a
two-turn run exited 0 while six units were ordered onto occupied tiles, two waypoints were water,
a research choice was left open, three cities went idle and `CHECK FAILED [finish-the-wounded]`
fired. So every turn is passed through `.tools/turn-verify.py`, which checks that the advance is
witnessed by two independent sources and that nothing inside the turn failed - and the run exits
non-zero if any turn did. `--json` emits the per-turn verdicts as data.

    python .tools/advance-turns.py --turns 2 --march 27:36,20 --march 23:40,17
    python .tools/advance-turns.py --turns 1 --json

`--march` runs the given move orders at the START of every turn, before anything can skip them:
`end` fortifies whatever still has moves, so a turn that then fails to advance has thrown the whole
army's movement away (measured T293: 43 units). Syntax is `INDEX:X,Y` and the index is a
`unit_index` (the number in brackets in `play-turn.py units`), **not** the `unit_id` the staging plan
reports - passing a unit_id silently matches nothing, which is how a march was issued and no unit
moved.

Output is line buffered. A background run whose stdout is a pipe otherwise holds every line until
the process exits, so a caller watching the job sees nothing at all and can only block on it.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from civ_mcp import end_turn as end_turn_module  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

WAR_ENEMY = 5  # Phoenicia: the civ this operation declared on
MAX_DRAIN = 6
MAX_ATTEMPTS_PER_TURN = 4


def _load_verifier():
    """`.tools/turn-verify.py` - a hyphen is not an importable name, so load it by path.

    Registered in `sys.modules` before execution because `@dataclass` resolves its own annotations
    through `cls.__module__`, and an unregistered module makes that lookup fail.
    """
    path = ROOT / ".tools" / "turn-verify.py"
    spec = importlib.util.spec_from_file_location("turn_verify_tool", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["turn_verify_tool"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


tv = _load_verifier()


async def current_turn(gs) -> int:
    overview = await gs.get_game_overview()
    return int(getattr(overview, "turn", 0) or 0)


async def drain_diplomacy(gs, replies: list[str]) -> int:
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
            replies.append(str(reply))
            print(f"    p{pid} {response} -> {reply}")
        await asyncio.sleep(1.5)
    return answered


async def march(gs, orders, replies: list[str], log: list[tuple]) -> None:
    """One move per order, re-reading the unit list between them.

    `get_units` is re-read inside the loop so a unit that stopped mid-path cannot be picked twice
    or block the one behind it, and each order's start position is recorded so the verifier can
    tell a march leg that progressed from one that did nothing.
    """
    spent: set[int] = set()
    for index, tx, ty in orders:
        for unit in await gs.get_units():
            if unit.unit_index != index or unit.unit_index in spent:
                continue
            if unit.moves_remaining <= 0:
                reply = f"NO_MOVES|[{index}] had no movement points when the order was issued"
                print(f"    {reply}")
                replies.append(reply)
                log.append((index, (unit.x, unit.y), (tx, ty), reply))
                spent.add(index)
                break
            start = (unit.x, unit.y)
            reply = await gs.move_unit(unit.unit_index, tx, ty)
            spent.add(unit.unit_index)
            print(f"    [{index}] {unit.unit_type} {start} -> ({tx},{ty})")
            print(f"      {reply}")
            replies.append(str(reply))
            log.append((index, start, (tx, ty), str(reply)))
            break
        else:
            print(f"    [{index}] not found in the unit list")


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
    ap.add_argument("--json", action="store_true", help="emit the per-turn verdicts as JSON")
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
    target = start + args.turns
    print(f"starting turn: {start}  target: {target}")
    verdicts = []

    while True:
        turn = await current_turn(gs)
        if turn >= target:
            break

        advanced = False
        for attempt in range(MAX_ATTEMPTS_PER_TURN):
            before = await current_turn(gs)
            replies: list[str] = []
            log: list[tuple] = []

            if orders and attempt == 0:
                print(f"  T{before}: march")
                await march(gs, orders, replies, log)
            print(f"  T{before}: drain diplomacy")
            await drain_diplomacy(gs, replies)
            print(f"  T{before}: end")
            try:
                end_text = str(await end_turn_module.execute_end_turn(gs) or "")
            except Exception as exc:  # noqa: BLE001
                end_text = f"ERR: execute_end_turn raised {type(exc).__name__}: {exc}"
            replies.append(end_text)
            print("    " + " ".join(end_text.split())[:400])

            after = await current_turn(gs)
            if after <= before:
                continue

            # The turn moved, so this is the point at which its quality can be judged.
            cities, _ = await gs.get_cities()
            positions = {u.unit_index: (u.x, u.y) for u in await gs.get_units()}
            save_name, save_turn = await tv.newest_save_turn()
            march_rows = [
                (index, start_pos, tgt, positions.get(index, start_pos), reply)
                for index, start_pos, tgt, reply in log
            ]
            verdict = tv.verdict_from(
                turn_before=before,
                turn_after=after,
                expected=before + 1,
                engine_turn=after,
                cities=cities,
                replies=replies,
                end_text=end_text,
                march=march_rows,
                save_name=save_name,
                save_turn=save_turn,
            )
            verdicts.append(verdict)
            print(verdict.render())
            advanced = True
            break

        if not advanced:
            print(f"  T{turn}: did not advance in {MAX_ATTEMPTS_PER_TURN} attempts")
            break
        await asyncio.sleep(2)

    end = await current_turn(gs)
    failed = [v for v in verdicts if not v.ok]
    print(f"final turn: {end}  (asked for {target})")
    print(f"turns verified: {len(verdicts)}  failed: {len(failed)}")
    if args.json:
        print(json.dumps(
            [{**v.__dict__, "problems": v.problems, "ok": v.ok} for v in verdicts],
            ensure_ascii=False, indent=2,
        ))
    return 0 if (end >= target and not failed) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
