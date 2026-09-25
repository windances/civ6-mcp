"""Condemn Heretic: the verb that destroys an enemy religious unit.

`unit_action(action="attack")` cannot do this. Its target resolver *does* reach a non-combat unit on
the tile (`lua/units.py`, the fallback in the enemy scan), but the attack builder refuses any target
whose owner we are at peace with (`ERR:NOT_AT_WAR`), and the game's own rule agrees: the string
`LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION` in the install's `InGameText.xml` reads
"A Religious unit in this tile belongs to a player you are not at war with."

The game's verb is a **command**, not a UnitOperation - `UNITCOMMAND_CONDEMN_HERETIC` in
`Base/Assets/Gameplay/Data/UnitCommands.xml`, issued by the game's own UnitPanel as
`UnitManager.RequestCommand(unit, UnitCommandTypes.CONDEMN_HERETIC)` and pre-checked with
`UnitManager.CanStartCommand(unit, command, nil, true)` (UnitPanel.lua:419). There is no target
parameter: the engine picks the adjacent religious unit, which is why the Lua reports every candidate
before it fires.

Measured against the live game's files on 2026-09-26 (install under `D:\\SteamLibrary\\...`).
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import lua as lq  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

CONDEMNED = (
    "OK:CONDEMNED|传教士 of 俄罗斯 at (54,38)|candidates:1|verify_tile:54,38"
)


class FakeConn:
    """The two calls `condemn_heretic` makes: the command, then the tile re-read."""

    def __init__(self, write_lines, read_lines=()):
        self.write_lines = list(write_lines)
        self.read_lines = list(read_lines)
        self.writes: list[str] = []
        self.reads: list[str] = []

    async def execute_write(self, lua, timeout=5.0):
        self.writes.append(lua)
        return self.write_lines

    async def execute_read(self, lua, timeout=5.0):
        self.reads.append(lua)
        return self.read_lines


class TestTheCommandIsTheGamesOwn:
    def test_it_uses_the_command_not_an_operation(self):
        lua = lq.build_condemn_heretic(1441804)
        assert "UnitCommandTypes.CONDEMN_HERETIC" in lua
        assert "UnitManager.RequestCommand(unit, command)" in lua
        # An operation name would be wrong: the game defines this as a UnitCommand only.
        assert "UnitOperationTypes.CONDEMN" not in lua

    def test_it_pre_checks_the_way_the_games_ui_does(self):
        lua = lq.build_condemn_heretic(1441804)
        assert "UnitManager.CanStartCommand(unit, command, nil, true)" in lua

    def test_it_reports_the_target_before_firing(self):
        lua = lq.build_condemn_heretic(1441804)
        assert lua.index('print("CANDIDATE|"') < lua.index("UnitManager.RequestCommand")
        assert "verify_tile:" in lua

    def test_it_knows_the_religious_unit_types(self):
        lua = lq.build_condemn_heretic(1441804)
        for unit in ("UNIT_MISSIONARY", "UNIT_APOSTLE", "UNIT_INQUISITOR", "UNIT_GURU"):
            assert unit in lua


class TestRefusalsAreNamed:
    def test_no_adjacent_religious_unit(self):
        lua = lq.build_condemn_heretic(1)
        assert "ERR:NO_RELIGIOUS_TARGET" in lua

    def test_a_peace_time_target_gets_the_games_own_reason(self):
        lua = lq.build_condemn_heretic(1)
        assert "ERR:REQUIRES_WAR" in lua
        assert "LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION" in lua


class TestTheActionMethod:
    def test_a_kill_is_verified_against_the_tile(self):
        conn = FakeConn([CONDEMNED], read_lines=[])
        gs = GameState(conn)
        out = asyncio.run(gs.condemn_heretic(1441804))
        assert out.startswith("CONDEMNED|")
        assert "tile (54,38) now empty" in out
        assert conn.reads, "the tile must be re-read rather than trusting the request"

    def test_a_surviving_unit_is_reported_rather_than_assumed_dead(self):
        conn = FakeConn([CONDEMNED], read_lines=["UNIT|UNIT_MISSIONARY|100/100|owner:1"])
        gs = GameState(conn)
        out = asyncio.run(gs.condemn_heretic(1441804))
        assert "STILL THERE" in out and "UNIT_MISSIONARY" in out

    def test_a_refusal_is_returned_unchanged_and_not_verified(self):
        conn = FakeConn(["ERR:REQUIRES_WAR|Condemn Heretic needs a war declaration"])
        gs = GameState(conn)
        out = asyncio.run(gs.condemn_heretic(1))
        assert out.startswith("Error: REQUIRES_WAR")
        assert conn.reads == []

    def test_the_builder_is_what_was_executed(self):
        conn = FakeConn([CONDEMNED], read_lines=[])
        gs = GameState(conn)
        asyncio.run(gs.condemn_heretic(1441804))
        # `dismiss_popup` writes its own Lua first, so look for the condemn among the writes.
        assert any("CONDEMN_HERETIC" in lua for lua in conn.writes)
