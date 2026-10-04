"""Whose move is it? Asked of the board, not of anybody's memory.

The `-HumanMilitary` division is a *sequence*: every turn the agent moves first - it orders every
unit and every city queue it owns - and the human then commands the military units, the Great
Generals and the Great Admirals. That leaves the human with one question, "can I start yet?", and
nothing in the loop answered it. `end_turn`'s units blocker cannot answer it: an
`ENDTURN_BLOCKING_UNITS` entry is raised while *any* unit still has moves, so it is up at the start
of nearly every turn and says nothing about whose turn it is to move.

So the answer is **derived, never reported**. A session asked to announce "my half is done" would
forget eventually, and would be wrong exactly when it mattered - while it sat on the gate with one
of its own builders still un-ordered. Instead every `get_notifications` call - the call a waiting
session makes - recomputes the split from the unit list, appends one line of it to the tool's
answer, and writes `agent-half.txt` beside the heartbeat:

    T351  YOUR MOVE  19:12:03
    the agent's half of T351 is done: every unit it owns is ordered.
    9 units can still act, and every one of them is yours:
      [ 0] UNIT_GREAT_ADMIRAL        ( 33, 24) mv5 awake
      ...

The file is for the human, who does not call tools; the appended line is for the session, which has
to know whether the units still holding the turn are its own or the human's before it waits on them.

**The predicate is the division, written once.** `is_the_humans` and `can_still_act` live here and
`.tools/wait-for-human.py` imports them rather than keeping a copy: two implementations of "whose
unit is this" would drift, and the drift would show up as the two of them disagreeing about the one
fact the whole division turns on.
"""

from __future__ import annotations

import logging
import pathlib
import time
from typing import Any, Iterable, Sequence

log = logging.getLogger(__name__)

#: Written into the run directory, beside `heartbeat.json` (same resolution, same reason: the file
#: belongs to one playthrough, and the playthrough is resolved when it is written).
REPORT_NAME = "agent-half.txt"

#: The listed units are capped: the file is read by a human, and a 40-unit roster pushes the answer
#: off the screen. The count is always stated, so nothing is hidden by the cap.
MAX_ROWS = 20

#: One line, in the same InGame context as everything else read here (`get_units` and the
#: notifications query both go through `execute_write`; `Game.GetCurrentGameTurn()` is happy in
#: either, and reading it here costs one round trip on a call that is already making one).
_TURN_LUA = (
    "local ok, t = pcall(function() return Game.GetCurrentGameTurn() end)\n"
    'if ok then print("TURN|" .. tostring(t)) end\n'
    'print("---END---")\n'
)


def is_the_humans(unit: Any) -> bool:
    """A military unit, or a Great General or Great Admiral - the units the human commands.

    A Great General or Admiral has no combat strength, so the combat test alone would have left the
    human's own commanders movable by the session.
    """
    if (getattr(unit, "combat_strength", 0) or 0) > 0:
        return True
    kind = str(getattr(unit, "unit_type", "") or "").upper()
    return "GENERAL" in kind or "ADMIRAL" in kind


def can_still_act(unit: Any) -> bool:
    """Whether anybody can still give this unit an order this turn.

    Movement is not the test. A unit parked by a `skip` (`ACTIVITY_HOLD`), one on `alert`
    (`ACTIVITY_SENTRY`), one asleep and one running an operation keep their movement for the rest of
    the turn *and across turns* while being unable to act - measured on the live match, 10 military
    units had movement and 9 of them could not act, so a count of movement waits on units that are
    already finished. `ready_to_move` is the engine's own answer, and it is the one used here.
    """
    if (getattr(unit, "moves_remaining", 0) or 0) <= 0:
        return False
    if not str(getattr(unit, "activity", "") or ""):
        return True
    return bool(getattr(unit, "ready_to_move", False))


def split(units: Iterable[Any]) -> tuple[list[Any], list[Any]]:
    """`(units the agent owns that can still act, units the human's that can still act)`."""
    live = [u for u in units if can_still_act(u)]
    return [u for u in live if not is_the_humans(u)], [u for u in live if is_the_humans(u)]


def verdict(agent: Sequence[Any], human: Sequence[Any]) -> str:
    """`"your move"`, `"agent working"` or `"turn can end"` - the whole answer, in one place."""
    if agent:
        return "agent working"
    if human:
        return "your move"
    return "turn can end"


def _moves(unit: Any) -> str:
    moves = float(getattr(unit, "moves_remaining", 0) or 0)
    return f"{int(moves)}" if moves == int(moves) else f"{moves:.1f}"


def _row(unit: Any) -> str:
    index = getattr(unit, "unit_index", None)
    seat = f"[{index:>2}] " if isinstance(index, int) else ""
    activity = str(getattr(unit, "activity", "") or "").replace("ACTIVITY_", "").lower() or "awake"
    return (
        f"  {seat}{str(getattr(unit, 'unit_type', '?') or '?'):<24} "
        f"({getattr(unit, 'x', 0):>3},{getattr(unit, 'y', 0):>3}) mv{_moves(unit)} {activity}"
    )


def _rows(units: Sequence[Any]) -> list[str]:
    rows = [_row(u) for u in units[:MAX_ROWS]]
    if len(units) > MAX_ROWS:
        rows.append(f"  ... and {len(units) - MAX_ROWS} more")
    return rows


def render(turn: int | None, units: Iterable[Any], when: float | None = None) -> str:
    """The file the human reads: whose move, at what time, and what each side still holds."""
    agent, human = split(units)
    head = f"T{turn}" if turn else "T?"
    stamp = time.strftime("%H:%M:%S", time.localtime(time.time() if when is None else when))
    kind = verdict(agent, human)

    if kind == "your move":
        lines = [
            f"{head}  YOUR MOVE  {stamp}",
            "the agent's half is done: every unit and every city queue it owns is ordered.",
            f"{len(human)} unit(s) can still act, and every one of them is yours:",
            *_rows(human),
            "the turn cannot end until they have orders (or are skipped).",
        ]
    elif kind == "agent working":
        lines = [
            f"{head}  AGENT STILL WORKING  {stamp}",
            f"{len(agent)} unit(s) the agent owns can still act - its own, not yours:",
            *_rows(agent),
            "nothing is waiting on you yet: this is the agent's half of the turn.",
        ]
    else:
        lines = [
            f"{head}  NOTHING IS HOLDING THE TURN  {stamp}",
            "no unit on either side can still act, so the units blocker is down and the turn can end.",
            "if you have not played this turn, wake a unit: a parked unit looks the same whether you",
            "parked it or the game's end-of-turn sweep did, so this is not proof that you moved.",
        ]
    return "\n".join(lines) + "\n"


def summary(turn: int | None, units: Iterable[Any]) -> str:
    """The one line appended to `get_notifications`, for the session rather than the human."""
    agent, human = split(units)
    head = f"T{turn}" if turn else "T?"
    kind = verdict(agent, human)

    if kind == "your move":
        return (
            f"WHOSE MOVE|your move|{head}: the agent's half is done - {len(human)} unit(s) can still "
            "act and all of them are the human's; wait for them"
        )
    if kind == "agent working":
        named = ", ".join(
            f"{getattr(u, 'unit_type', '?')} at ({u.x},{u.y})" for u in agent[:3]
        )
        more = f" and {len(agent) - 3} more" if len(agent) > 3 else ""
        return (
            f"WHOSE MOVE|agent working|{head}: {len(agent)} of your own units can still act - "
            f"{named}{more}; order or skip them, the turn cannot end until you do"
        )
    return (
        f"WHOSE MOVE|nothing is holding the turn|{head}: no unit on either side can still act, so the "
        "turn can end - which is not proof the human has played: a unit parked by a skip looks "
        "exactly like one the game's own end-of-turn sweep parked"
    )


def write(text: str) -> pathlib.Path | None:
    """Write the report into the current run. Never raises - this is an observation, not a gate."""
    try:
        from civ_mcp import run_manifest

        target = run_manifest.resolve_data_dir() / REPORT_NAME
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(target)
        return target
    except Exception:  # noqa: BLE001 - a side-report must not fail the tool that carries it
        log.debug("could not write the agent-half report", exc_info=True)
        return None


async def _turn(gs: Any) -> int | None:
    """The turn, read in the same breath as the units. An unreadable turn is unknown, not fatal."""
    try:
        for line in await gs.conn.execute_write(_TURN_LUA):
            if (line or "").startswith("TURN|"):
                return int(line.split("|", 1)[1])
    except Exception:  # noqa: BLE001 - the report still says whose move it is without a turn
        log.debug("could not read the turn for the agent-half report", exc_info=True)
    return None


async def report_for(gs: Any) -> str:
    """Recompute the split, write the file, and return the line to append. Never raises.

    Called from `get_notifications` - the call a session makes while it waits, which is exactly when
    the answer matters - so the file is refreshed at the moment the human needs to read it and the
    session is told whether the units still holding the turn are its own.
    """
    try:
        units = await gs.get_units()
    except Exception:  # noqa: BLE001 - a side-report must not turn a working tool into a failure
        log.debug("could not read the units for the agent-half report", exc_info=True)
        return ""
    turn = await _turn(gs)
    if write(render(turn, units)) is not None:
        log.debug("agent-half report refreshed for T%s", turn)
    return summary(turn, units)
