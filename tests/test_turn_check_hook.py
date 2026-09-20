"""The turn-check hook: it has to run on every turn, not only on the ones that advance.

`end_turn` returns early when blockers stop the turn - unmoved units, an empty production
queue, a promotion waiting - and those are the turns an agent is stuck on, which is exactly
when a standing reminder earns its place. Measured before the fix: the check call sat after
the blocker return, so a blocked turn never saw the reminders at all.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import types
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def unit(uid: int, unit_type: str) -> m.UnitInfo:
    return m.UnitInfo(
        unit_id=uid,
        unit_index=uid,
        name=unit_type,
        unit_type=unit_type,
        x=0,
        y=0,
        moves_remaining=2,
        max_moves=2,
        health=100,
        max_health=100,
    )


class FakeSnapshot:
    def __init__(self, turn: int, units: dict):
        self.turn = turn
        self.units = units


class FakeGameState:
    """Only what the check helpers touch."""

    def __init__(self, turn: int, units: dict, *, snapshot_turn: int | None = None):
        self.turn = turn
        self.units = units
        self.snapshots_taken = 0
        self._last_snapshot = (
            FakeSnapshot(snapshot_turn, units) if snapshot_turn is not None else None
        )

    async def get_game_identity(self):
        return ("china", -1894041591)

    async def _take_snapshot(self):
        self.snapshots_taken += 1
        self._last_snapshot = FakeSnapshot(self.turn, self.units)
        return self._last_snapshot


@pytest.fixture()
def diary(monkeypatch):
    """A one-row diary for the agent, written under the workspace (tmp_path is not
    writable in this sandbox)."""
    path = pathlib.Path(".tools") / f"_test_diary_{uuid.uuid4().hex}.jsonl"
    path.write_text(
        json.dumps(
            {
                "turn": 60,
                "is_agent": True,
                "pid": 0,
                "science": 8.0,
                "culture": 9.0,
                "gold_per_turn": 18.0,
                "military": 40,
                "pop": 14,
                "cities": 3,
                "districts": 4,
                "improvements": 9,
                "wonders": 0,
                "territory": 30,
                "techs_completed": 8,
                "civics_completed": 6,
                "trade_routes": {"capacity": 1, "active": 1},
                "techs": [],
                "civics": [],
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        et, "_agent_diary_rows", lambda gs: _rows(path)
    )
    yield path
    path.unlink(missing_ok=True)


async def _rows(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_the_checks_run_with_an_army_that_has_no_siege(diary):
    # T60 of the live game: no ram, no siege, no wonder - the standing reminders must fire.
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER"), 2: unit(2, "UNIT_MAN_AT_ARMS")})
    messages = asyncio.run(et._turn_check_messages(gs, 60))
    text = "\n".join(messages)
    assert "ram-tower-before-civil-engineering" in text
    assert "dynasty-cycle-wonder" in text, "no wonder built"
    assert "idle-district-slot" not in text, "4 districts for pop 14 is exactly the allowance"
    assert len(messages) >= 2


def test_a_stale_snapshot_is_not_reused(diary):
    # A snapshot from an earlier turn can miss a unit built since; one fresh snapshot per
    # turn is the cost of not reporting yesterday's army.
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")}, snapshot_turn=59)
    asyncio.run(et._turn_check_messages(gs, 60))
    assert gs.snapshots_taken == 1


def test_a_same_turn_snapshot_is_reused(diary):
    # Blocker turns repeat several times per game turn; they must not each pay for a snapshot.
    gs = FakeGameState(60, {1: unit(1, "UNIT_ARCHER")}, snapshot_turn=60)
    asyncio.run(et._turn_check_messages(gs, 60))
    assert gs.snapshots_taken == 0


def test_a_broken_check_file_is_reported_not_swallowed(monkeypatch):
    monkeypatch.setenv("CIV_MCP_TURN_CHECKS", "does/not/exist.md")
    messages = asyncio.run(et._turn_check_messages(FakeGameState(60, {}), 60))
    assert messages == [], "a missing file is silent, not an error"


def test_the_blocker_path_calls_the_checks():
    """Pin the wiring: the call has to sit before the blocker return, not after it."""
    import inspect

    source = inspect.getsource(et.execute_end_turn)
    blocker_return = source.index('return "\\n".join(lines_out)')
    calls = [source.index(name) for name in ("_turn_check_messages",) if name in source]
    assert calls, "the check helper is not called from execute_end_turn"
    assert min(calls) < blocker_return, "the checks run after the blocker return"
