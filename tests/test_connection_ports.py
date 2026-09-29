"""The tuner can listen on 4319 after a save load, so the connection tries both ports.

Measured twice on 2026-09-29, in the session that was in play: after a save was loaded into a
running game the game's FireTuner listened on 4319 only, with nothing on 4318, and an MCP session
started against it sat at `phase: starting` because `GameConnection` only ever tried 4318. A fresh
launch binds 4318; when both ports listen, 4318 carries the full Lua state list. The two ports are
the same tuner on the same game, so 4319 is a legitimate fallback. The same fact is in
`docs/experiments/003-attempt-A3.md` (the tuner "moved from 4318 to 4319") and the repo's cleaner
already treats both as tuner ports (`scripts/civ6-clean.ps1`).

These tests need no game: they stub `tuner_client.connect`, which is the one low-level call that
opens a socket, and `tuner_client.handshake`, which needs a live Lua state list.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import connection, tuner_client  # noqa: E402
from civ_mcp.connection import GameConnection, tuner_port_candidates  # noqa: E402


class _FakeWriter:
    """Enough of a StreamWriter for `is_connected`, and nothing else."""

    def is_closing(self) -> bool:
        return False

    def close(self) -> None:  # pragma: no cover - only reached if a test disconnects
        return None


def _stub_tuner(monkeypatch, *, failing: tuple[int, ...] = ()) -> list[int]:
    """Stub the socket layer, refusing the ports in `failing`. Returns the ports tried."""
    tried: list[int] = []

    async def fake_connect(host: str, port: int, timeout: float = 5.0):
        tried.append(port)
        if port in failing:
            raise ConnectionRefusedError(f"refused {host}:{port}")
        return object(), _FakeWriter()

    async def fake_handshake(reader, writer):
        return "Civilization VI", ["0", "GameCore_Tuner", "1", "InGame"]

    monkeypatch.setattr(tuner_client, "connect", fake_connect)
    monkeypatch.setattr(tuner_client, "handshake", fake_handshake)
    return tried


class TestCandidatePorts:
    """The candidate list itself - the port the caller named comes first."""

    def test_the_two_known_tuner_ports_are_the_candidates(self):
        assert tuner_client.TUNER_PORTS == (4318, 4319), (
            "4318 and 4319 are the ports measured on this game; a third entry here "
            "would be an unmeasured guess"
        )
        assert tuner_port_candidates(tuner_client.DEFAULT_PORT) == [4318, 4319]

    def test_an_explicit_port_is_tried_before_the_default(self):
        """`GameConnection(port=4319)` must still try 4319 first, not 4318."""
        assert tuner_port_candidates(4319) == [4319, 4318]

    def test_an_unknown_configured_port_still_falls_back_to_both_known_ports(self):
        assert tuner_port_candidates(5000) == [5000, 4318, 4319]

    def test_the_default_connection_starts_on_the_default_port(self):
        assert GameConnection().port == tuner_client.DEFAULT_PORT


class TestConnectFallback:
    """`GameConnection.connect` - the order of attempts and what happens when one fails."""

    def test_the_default_connection_tries_4318_then_4319(self, monkeypatch):
        tried = _stub_tuner(monkeypatch, failing=(4318, 4319))
        conn = GameConnection()
        with pytest.raises(ConnectionError):
            asyncio.run(conn.connect())
        assert tried == [4318, 4319]

    def test_a_working_first_port_is_not_retried(self, monkeypatch):
        """Nothing changes when 4318 answers: one attempt, one handshake."""
        tried = _stub_tuner(monkeypatch)
        conn = GameConnection()
        asyncio.run(conn.connect())
        assert tried == [4318], "the fallback must not run when the first port works"
        assert conn.is_connected
        assert conn.ingame_index == 1

    def test_the_fallback_port_is_used_when_the_first_refuses(self, monkeypatch):
        tried = _stub_tuner(monkeypatch, failing=(4318,))
        conn = GameConnection()
        asyncio.run(conn.connect())
        assert tried == [4318, 4319]
        assert conn.is_connected, "the connection that answered on 4319 is the live one"
        assert conn.gamecore_index == 0
        assert conn.ingame_index == 1

    def test_an_explicit_port_is_honoured_first(self, monkeypatch):
        """A caller that names 4319 gets 4319 first, then the default behind it."""
        tried = _stub_tuner(monkeypatch, failing=(4319,))
        conn = GameConnection(port=4319)
        asyncio.run(conn.connect())
        assert tried == [4319, 4318]
        assert conn.is_connected

    def test_the_error_names_both_ports_and_keeps_the_tuner_hint(self, monkeypatch):
        _stub_tuner(monkeypatch, failing=(4318, 4319))
        conn = GameConnection()
        with pytest.raises(ConnectionError) as excinfo:
            asyncio.run(conn.connect())
        message = str(excinfo.value)
        assert "127.0.0.1:4318" in message and "127.0.0.1:4319" in message, message
        assert "EnableTuner=1" in message, message

    def test_an_explicit_port_is_reported_first_when_both_fail(self, monkeypatch):
        """The message names the ports in the order they were tried, and the socket
        refusal stays the cause rather than being swallowed."""
        _stub_tuner(monkeypatch, failing=(4318, 4319))
        conn = GameConnection(port=4319)
        with pytest.raises(ConnectionError) as excinfo:
            asyncio.run(conn.connect())
        message = str(excinfo.value)
        assert message.index("4319") < message.index("4318"), message
        assert isinstance(excinfo.value.__cause__, OSError)

    def test_a_timeout_on_the_first_port_is_not_fatal_either(self, monkeypatch):
        """`asyncio.TimeoutError` is caught alongside OSError, so a black-holed port
        (a firewall dropping packets rather than refusing them) still falls through."""
        tried: list[int] = []

        async def fake_connect(host: str, port: int, timeout: float = 5.0):
            tried.append(port)
            if port == 4318:
                raise asyncio.TimeoutError()
            return object(), _FakeWriter()

        async def fake_handshake(reader, writer):
            return "Civilization VI", ["0", "GameCore_Tuner", "1", "InGame"]

        monkeypatch.setattr(tuner_client, "connect", fake_connect)
        monkeypatch.setattr(tuner_client, "handshake", fake_handshake)

        conn = GameConnection()
        asyncio.run(conn.connect())
        assert tried == [4318, 4319]
        assert conn.is_connected
