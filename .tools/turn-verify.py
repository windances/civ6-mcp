"""Decide whether a turn actually finished, and whether it finished *correctly*.

A turn number going up is not evidence that a turn worked. Measured 2026-10-04 in
china--1894041591: a two-turn run exited 0 while, inside it, six units were ordered onto tiles
another unit already stood on (`STACKING_CONFLICT`), two waypoints were water (`BLOCKED (water
tile)`), a research choice was left open, three cities finished their build and went idle, and a
`CHECK FAILED [finish-the-wounded]` rule fired - because a barbarian sat at 18 HP two tiles from a
unit with moves and nothing attacked it. Every one of those is invisible in "turn 291 -> 293".

So completion is checked in two layers and the layers are deliberately different kinds of claim:

**It happened** - the engine says so *and* an independent artifact agrees.
  - `get_game_overview().turn` is the engine's own statement.
  - the newest save on disk, with its turn read **from inside the file** rather than from its name,
    is the artifact. The name is not a witness: `civ_mcp.handoff.save_turn` documents that four of
    nine newest MCP saves were once named one turn low, and the game's own `AutoSave_NNNN` runs one
    ahead by design. Reading the file is what makes this a second opinion instead of a restatement.

**It was done right** - every one of these, each of which has fired for real:
  - no write came back a hard failure (`SILENT_FAILURE`, `MISSING_COORDS`, `ERR:`, `BLOCKED (`,
    `STACKING_CONFLICT`, `NO_MOVES`). `STOPPED_MID_PATH` is **not** in that list on purpose: it
    means the unit moved as far as its movement allowed, which is the normal end of a march leg.
  - no city is sitting on an empty queue.
  - the end-of-turn text carries no unresolved blocker (a pending diplomacy session, a completed
    research or civic, a finished build announcing `Now: nothing`).
  - every `CHECK FAILED [id]` is reported, so the caller can accept it in the diary or fix it.
  - every ordered unit either closed distance on its target or stopped for a reason that is the
    map's rather than ours.

`ok` is false when any of those fail. The report names each problem; it never summarizes a failure
into a bare boolean, because the whole point is that the boolean was already lying.

    python .tools/turn-verify.py --expect-turn 293          # check the state as it stands now
    python .tools/turn-verify.py --expect-turn 293 --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from civ_mcp import game_launcher as gl  # noqa: E402
from civ_mcp import handoff  # noqa: E402

# A write or an order that did not take effect. `STOPPED_MID_PATH` is deliberately absent: the unit
# walked as far as its movement allowed, which is an ordinary march leg, and treating it as a
# failure would flag every turn of a long march.
HARD_FAILURES = (
    "SILENT_FAILURE",
    "MISSING_COORDS",
    "ERR:",
    "STACKING_CONFLICT",
    "NO_MOVES",
    "BLOCKED (",
)

# A unit that did not move at all, for a reason that is the map's rather than a bad order. A
# `BLOCKED` that is *not* one of these is the target choice being wrong - as when a waypoint landed
# on water, which happened twice in one turn.
ACCEPTED_STOPS = (
    "foreign territory",
    "city-state territory",
    "Zone of Control",
)

CHECK_FAILED_RE = re.compile(r"CHECK FAILED\s*\[([^\]]+)\]")
BLOCKER_PHRASES = (
    "Cannot end turn",
    "Turn paused",
    "Research complete",
    "Civic complete",
    "Now: nothing",
    "Now: None",
)

IDLE_QUEUE = {"", "NONE", "NOTHING", "nothing"}


def hex_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Hex distance on Civ VI's offset grid, as the game itself counts it.

    Hand arithmetic in this repo got this wrong four times, so the formula is pinned by
    `tests/test_turn_verify.py` against six distances the *game* printed in a staging plan
    (`(68,21)->(26,11)` is 47, `(50,13)` is 25, `(48,13)` is 23, `(48,12)` is 22, `(44,24)` is 24).

    It does **not** model the east-west map wrap, so a pair whose shortest line crosses x=0 reads
    too far. Every distance this module compares is between a unit and a target in the same
    hemisphere, where the wrap cancels; the staging plan's one wrapped figure (`(82,7)` -> 30 against
    a straight-line 58) is the reason the limitation is written down instead of hidden.
    """

    def cube(col: int, row: int) -> tuple[int, int, int]:
        x = col - (row - (row & 1)) // 2
        z = row
        return x, -x - z, z

    ax, ay, az = cube(*a)
    bx, by, bz = cube(*b)
    return (abs(ax - bx) + abs(ay - by) + abs(az - bz)) // 2


def is_hard_failure(reply: str) -> bool:
    return any(marker in str(reply) for marker in HARD_FAILURES)


def is_accepted_stop(reply: str) -> bool:
    return any(reason in str(reply) for reason in ACCEPTED_STOPS)


def check_failures(end_text: str) -> list[str]:
    return CHECK_FAILED_RE.findall(end_text or "")


def blockers_in(end_text: str) -> list[str]:
    text = end_text or ""
    return [phrase for phrase in BLOCKER_PHRASES if phrase in text]


def idle_cities(cities) -> list[str]:
    idle = []
    for city in cities:
        building = str(getattr(city, "currently_building", "") or "").strip()
        if building in IDLE_QUEUE or int(getattr(city, "production_turns_left", 0) or 0) <= 0:
            idle.append(f"{city.name} (pop{city.population}, prod {city.production})")
    return idle


@dataclass
class TurnVerdict:
    """One turn's answer, with every problem named separately."""

    turn_before: int
    turn_after: int
    expected: int | None = None
    engine_turn: int | None = None
    save_name: str | None = None
    save_turn: int | None = None
    bad_writes: list[str] = field(default_factory=list)
    idle: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    march_problems: list[str] = field(default_factory=list)
    not_checked: list[str] = field(default_factory=list)

    @property
    def advanced(self) -> bool:
        return self.turn_after > self.turn_before

    @property
    def witnessed(self) -> bool:
        """The engine and the save file agree the turn is where we think it is."""
        return (
            self.engine_turn is not None
            and self.save_turn is not None
            and self.engine_turn == self.save_turn
        )

    @property
    def problems(self) -> list[str]:
        found: list[str] = []
        if not self.advanced:
            found.append(
                f"the turn did not advance: {self.turn_before} -> {self.turn_after}"
            )
        if self.expected is not None and self.turn_after != self.expected:
            found.append(f"expected T{self.expected}, the turn is T{self.turn_after}")
        if not self.witnessed:
            found.append(
                f"the turn is not witnessed by two sources: engine={self.engine_turn} "
                f"save={self.save_name}={self.save_turn}"
            )
        found += [f"write failed: {w}" for w in self.bad_writes]
        found += [f"city on an empty queue: {c}" for c in self.idle]
        found += [f"unresolved blocker in the turn result: {b}" for b in self.blockers]
        found += [f"march made no progress and not for the map's reason: {m}" for m in self.march_problems]
        return found

    @property
    def ok(self) -> bool:
        return not self.problems

    def render(self) -> str:
        head = (
            f"T{self.turn_before} -> T{self.turn_after}"
            + (f" (expected T{self.expected})" if self.expected is not None else "")
            + ("  OK" if self.ok else "  FAILED")
        )
        lines = [head]
        witness = (
            f"  witness    engine=T{self.engine_turn}  save={self.save_name}"
            f"=T{self.save_turn}  ({'agree' if self.witnessed else 'DISAGREE'})"
        )
        lines.append(witness)
        for problem in self.problems:
            lines.append(f"  PROBLEM    {problem}")
        if self.checks_failed:
            lines.append(
                "  checks     failing, must be accepted in the diary or fixed: "
                + ", ".join(self.checks_failed)
            )
        if self.not_checked:
            lines.append("  unverified " + "; ".join(self.not_checked))
        return "\n".join(lines)


def verdict_from(
    *,
    turn_before: int,
    turn_after: int,
    expected: int | None = None,
    engine_turn: int | None = None,
    cities=None,
    replies=(),
    end_text: str = "",
    march: tuple = (),
    save_name: str | None = None,
    save_turn: int | None = None,
) -> TurnVerdict:
    """The pure half: everything except the queries. Testable without a game."""
    verdict = TurnVerdict(
        turn_before=turn_before,
        turn_after=turn_after,
        expected=expected,
        engine_turn=engine_turn,
        save_name=save_name,
        save_turn=save_turn,
    )
    for reply in replies:
        if is_hard_failure(reply):
            verdict.bad_writes.append(" ".join(str(reply).split())[:160])
    if cities is not None:
        verdict.idle = idle_cities(cities)
    verdict.blockers = blockers_in(end_text)
    verdict.checks_failed = check_failures(end_text)
    for index, start, target, end, reply in march:
        if tuple(start) == tuple(end) and not is_accepted_stop(reply):
            verdict.march_problems.append(
                f"[{index}] stayed at {tuple(start)} en route to {tuple(target)}: "
                f"{' '.join(str(reply).split())[:120]}"
            )
    return verdict


async def newest_save_turn() -> tuple[str | None, int | None]:
    """The newest save's name and the turn **inside the file** - the independent witness."""
    newest = gl.get_newest_save()
    if not newest:
        return None, None
    name = newest[0]
    path = pathlib.Path(gl.SINGLE_SAVE_DIR) / f"{name}.Civ6Save"
    if not path.exists():
        path = pathlib.Path(gl.SAVE_DIR) / f"{name}.Civ6Save"
    if not path.exists():
        return name, None
    try:
        return name, handoff.save_turn(path)
    except Exception:  # noqa: BLE001 - an unreadable save is "no witness", not a crash
        return name, None


async def verify_live(expected: int) -> TurnVerdict:
    """Check the state as it stands, with no knowledge of how the turn was played."""
    from civ_mcp.connection import GameConnection
    from civ_mcp.game_state import GameState

    conn = GameConnection()
    await conn.connect()
    try:
        gs = GameState(conn)
        overview = await gs.get_game_overview()
        cities, _ = await gs.get_cities()
        name, save_turn = await newest_save_turn()
        engine_turn = int(getattr(overview, "turn", 0) or 0)
        verdict = verdict_from(
            turn_before=engine_turn - 1,
            turn_after=engine_turn,
            expected=expected,
            engine_turn=engine_turn,
            cities=cities,
            save_name=name,
            save_turn=save_turn,
        )
        verdict.not_checked.append(
            "writes and march progress: only a runner that recorded them can judge those"
        )
        return verdict
    finally:
        await conn.disconnect()


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-turn", type=int, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    verdict = await verify_live(args.expect_turn)
    if args.json:
        print(json.dumps({**verdict.__dict__, "problems": verdict.problems, "ok": verdict.ok},
                         ensure_ascii=False, indent=2))
    else:
        print(verdict.render())
    return 0 if verdict.ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
