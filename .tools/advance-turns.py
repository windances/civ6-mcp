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
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from civ_mcp import end_turn as end_turn_module  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

MAX_DRAIN = 6
MAX_ATTEMPTS_PER_TURN = 4


async def at_war_pids(gs) -> set[int]:
    """The player ids we are at war with, **read from the game**.

    Never a constant. Whom we are at war with is this match's state, and writing the id down is the
    same mistake as writing down a city name - but this one decides doctrine rather than display:
    the diplomacy policy below refuses peace to an enemy and accepts everything else, so a stale id
    makes it refuse peace to a friend and accept it from the enemy. Read it every drain, because a
    war also starts and ends inside a turn.
    """
    try:
        civs = await gs.get_diplomacy()
    except Exception as exc:  # noqa: BLE001
        print(f"    could not read diplomacy ({type(exc).__name__}); answering every session POSITIVE")
        return set()
    return {int(c.player_id) for c in civs if getattr(c, "is_at_war", False)}

# `end_turn` states the advance itself: "Turn 293 -> 294 | Score: ...". That statement is the
# engine's own claim and is not subject to the read staleness below.
TURN_CLAIM_RE = re.compile(r"Turn\s+(\d+)\s*->\s*(\d+)")


async def settled_turn(gs, tries: int = 6, delay: float = 3.0) -> int | None:
    """The turn number once two consecutive reads agree.

    A single read straight after `end_turn` can still be the **previous** turn - the same
    turn-boundary staleness the unit list is known for. Measured 2026-10-04: the read after the
    first `end` still said 293, so the loop believed the turn had not advanced, called `end` again,
    and the run advanced 293 -> 295 in one verdict (`expected T294, the turn is T295`). Two equal
    reads is the settled-frame rule this repo already uses for unit positions.
    """
    last = None
    for _ in range(tries):
        turn = await current_turn(gs)
        if turn is not None and turn == last:
            return turn
        last = turn
        await asyncio.sleep(delay)
    return last


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
        enemies = await at_war_pids(gs)
        if enemies:
            print(f"    at war with p{sorted(enemies)} - those sessions get NEGATIVE")
        for session in sessions:
            pid = int(getattr(session, "other_player_id", 0) or 0)
            response = "NEGATIVE" if pid in enemies else "POSITIVE"
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


def parse_orders(specs: list[str]) -> list[tuple[str, int, int]]:
    """`SELECTOR:X,Y` -> (selector, x, y).

    The selector is **not required to be an index**. An index is one match's state: a rollback or a
    new game renumbers every unit, so a plan written as `27:36,17` describes a unit that no longer
    exists. A selector may instead be

      `BOMBARD`   an upper-case fragment of `unit_type` - the nearest *unmoved* match to the target
      `nearest`   the nearest unmoved military unit to the target
      `27`        an exact `unit_index`, for when a read has just been taken and precision matters

    and `resolve()` prints which unit it picked, so the operator sees the identity the tool found
    instead of trusting one carried in from a note.
    """
    orders: list[tuple[str, int, int]] = []
    for spec in specs:
        selector, _, tile = spec.partition(":")
        tx, ty = (int(v) for v in tile.split(","))
        orders.append((selector.strip(), tx, ty))
    return orders


async def resolve(gs, selector: str, tx: int, ty: int, spent: set[int]):
    """The unit this selector means **right now**, or None.

    The distance is the game's own pathing estimate where it can give one, so the pick is the
    nearest *reachable* unit rather than the nearest by straight-line arithmetic - this repo has
    had hand hex distance wrong four times, and the wrap makes it worse.
    """
    candidates = [
        u
        for u in await gs.get_units()
        if u.unit_index not in spent and (u.combat_strength or 0) > 0
    ]
    if selector.isdigit():
        wanted = int(selector)
        return next((u for u in candidates if u.unit_index == wanted), None)
    if selector.lower() != "nearest":
        needle = selector.upper()
        candidates = [u for u in candidates if needle in str(u.unit_type).upper()]
    if not candidates:
        return None
    best, best_cost = None, None
    for unit in candidates:
        try:
            estimate = await gs.get_pathing_estimate(unit.unit_index, tx, ty)
            cost = int(getattr(estimate, "total_cost", -1) or -1)
        except Exception:  # noqa: BLE001
            cost = -1
        if cost < 0:  # unreachable, or no path to give: rank it last rather than first
            cost = 10**6
        if best_cost is None or cost < best_cost:
            best, best_cost = unit, cost
    return best


async def march(gs, orders, replies: list[str], log: list[tuple]) -> None:
    """One move per order, re-reading the unit list between them.

    `get_units` is re-read inside the loop so a unit that stopped mid-path cannot be picked twice or
    block the one behind it, and each order's start position is recorded so the verifier can tell a
    march leg that progressed from one that did nothing.
    """
    spent: set[int] = set()
    for selector, tx, ty in orders:
        unit = await resolve(gs, selector, tx, ty, spent)
        if unit is None:
            reply = f"ERR: no unmoved unit matches {selector!r} for ({tx},{ty})"
            print(f"    {reply}")
            replies.append(reply)
            log.append((selector, (0, 0), (tx, ty), reply))
            continue
        start = (unit.x, unit.y)
        print(
            f"    {selector} -> {unit.unit_type} (unit_id {unit.unit_id}, index "
            f"{unit.unit_index}) at {start}"
        )
        if unit.moves_remaining <= 0:
            reply = f"NO_MOVES|{unit.unit_type} #{unit.unit_id} had none when the order was issued"
            print(f"      {reply}")
            replies.append(reply)
            log.append((unit.unit_index, start, (tx, ty), reply))
            spent.add(unit.unit_index)
            continue
        reply = await gs.move_unit(unit.unit_index, tx, ty)
        spent.add(unit.unit_index)
        print(f"      {reply}")
        replies.append(str(reply))
        log.append((unit.unit_index, start, (tx, ty), str(reply)))


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=1)
    ap.add_argument(
        "--march",
        action="append",
        default=[],
        metavar="SELECTOR:X,Y",
        help="a move order; SELECTOR is a unit_type fragment (BOMBARD), 'nearest', or an exact "
             "unit_index. A type or 'nearest' is preferred: an index is this match's state and a "
             "rollback renumbers every unit, so a plan written with indices describes units that "
             "no longer exist",
    )
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

    start = await settled_turn(gs)
    if start is None:
        print("could not read the starting turn")
        return 1
    target = start + args.turns
    print(f"starting turn: {start}  target: {target}")
    verdicts = []

    while True:
        turn = await settled_turn(gs)
        if turn is None:
            print("lost the turn number; stopping")
            break
        if turn >= target:
            break

        advanced = False
        # These belong to the *game turn*, not to the attempt: an `end` that bounces on a
        # diplomacy round and is called again is still the same turn, and resetting them per
        # attempt threw away every reply the turn had produced. Measured: a verdict reported
        # `bad_writes: []` for a turn whose march had returned three STACKING_CONFLICTs, because
        # the advance was observed on the attempt *after* the one that marched.
        turn_replies: list[str] = []
        turn_log: list[tuple] = []
        for attempt in range(MAX_ATTEMPTS_PER_TURN):
            before = await settled_turn(gs)
            if before is None:
                print("  could not read the turn number")
                break

            if orders and attempt == 0:
                print(f"  T{before}: march")
                await march(gs, orders, turn_replies, turn_log)
            print(f"  T{before}: drain diplomacy")
            await drain_diplomacy(gs, turn_replies)
            print(f"  T{before}: end")
            try:
                end_text = str(await end_turn_module.execute_end_turn(gs) or "")
            except Exception as exc:  # noqa: BLE001
                end_text = f"ERR: execute_end_turn raised {type(exc).__name__}: {exc}"
            turn_replies.append(end_text)
            print("    " + " ".join(end_text.split())[:400])

            after = await settled_turn(gs)
            if after is None or after <= before:
                continue

            # The turn moved, so this is the point at which its quality can be judged.
            claim = TURN_CLAIM_RE.search(end_text)
            expected = int(claim.group(2)) if claim else before + 1
            cities, _ = await gs.get_cities()
            positions = {u.unit_index: (u.x, u.y) for u in await gs.get_units()}
            save_name, save_turn = await tv.newest_save_turn()
            march_rows = [
                (index, start_pos, tgt, positions.get(index, start_pos), reply)
                for index, start_pos, tgt, reply in turn_log
            ]
            verdict = tv.verdict_from(
                turn_before=before,
                turn_after=after,
                expected=expected,
                engine_turn=after,
                cities=cities,
                replies=turn_replies,
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

    end = await settled_turn(gs)
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
