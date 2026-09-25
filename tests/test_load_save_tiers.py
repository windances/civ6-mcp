"""How a save gets loaded: which Lua state is asked, and what the name comparison must do.

Both halves of this are pinned by a measured failure on 2026-09-25. `load_game_save` asked the
InGame state only, and the main menu has no InGame state — the tuner lists FrontEnd states there
— so every main-menu load fell through to OCR menu navigation, which needs the game window in
front and clicks a screen grab of it. And the comparison inside that tier was
`s.Name == "AutoSave_0099"` while the game's own list reports `AutoSave_0099.Civ6Save`, so even
in-game the fast path could not match. The result was three failed menu loads and two game
restarts to roll back one save, all avoidable.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import game_lifecycle as lf  # noqa: E402
from civ_mcp import game_launcher as gl  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class FakeConnection:
    """A tuner connection whose states answer from a script.

    ``answers`` maps a state index to what its poll returns; the query call is recognised by
    the Lua it carries, so a state can be made to answer NOT_FOUND, FOUND, or to raise.
    """

    def __init__(
        self,
        states: dict[int, str] | None = None,
        ingame_index: int | None = None,
        answers: dict[int, list[str]] | None = None,
        raise_on_poll: set[int] | None = None,
    ):
        self.lua_states = dict(states or {})
        self.ingame_index = ingame_index
        self.answers = dict(answers or {})
        self.raise_on_poll = set(raise_on_poll or ())
        self.sent: list[tuple[int, str]] = []
        self.reconnects = 0

    async def ensure_connected(self) -> None:
        return None

    async def reconnect(self) -> None:
        self.reconnects += 1

    async def execute_in_state(self, index: int, lua: str, timeout: float = 5.0):
        self.sent.append((index, lua))
        if "QuerySaveGameList" in lua:
            return ["QUERY_SENT"]
        if index in self.raise_on_poll:
            raise ConnectionError("cannot connect: the game is between Lua states")
        return list(self.answers.get(index, ["PENDING"]))


class TestWhichStateIsAsked:
    def test_in_game_asks_the_ingame_state(self):
        conn = FakeConnection(states={0: "InGame", 5: "LoadGameMenu"}, ingame_index=0)
        assert run(lf._save_list_states(conn)) == [(0, "InGame")]

    def test_at_the_main_menu_the_load_screen_states_are_asked(self):
        # Order matters only in that LoadGameMenu is the state that owns this flow
        # (LoadGameMenu.lua:459 queries, :440 loads); the others answer the same event.
        conn = FakeConnection(
            states={30: "FrontEnd", 5: "LoadGameMenu", 24: "MainMenu", 7: "Lobby"}
        )
        assert run(lf._save_list_states(conn)) == [
            (5, "LoadGameMenu"),
            (24, "MainMenu"),
            (30, "FrontEnd"),
        ]

    def test_a_connection_that_could_be_stale_is_re_discovered(self):
        # A connection opened at the main menu caches FrontEnd names only. Answering from that
        # cache would send the query to states that no longer exist once a game is loaded.
        conn = FakeConnection(states={5: "LoadGameMenu"})
        run(lf._save_list_states(conn))
        assert conn.reconnects == 1

    def test_no_state_at_all_is_an_empty_list(self):
        assert run(lf._save_list_states(FakeConnection())) == []


class TestTheLuaQuery:
    def test_the_name_is_compared_without_the_extension(self):
        # Measured: s.Name is "AutoSave_0099.Civ6Save", so the old equality test never matched.
        lua = lf._save_query_lua("AutoSave_0099")
        assert 'gsub("%.Civ6Save$", "")' in lua
        assert 'if n == "AutoSave_0099" then' in lua
        assert 'if s.Name == "AutoSave_0099" then' not in lua

    def test_it_loads_the_record_it_matched(self):
        lua = lf._save_query_lua("AutoSave_0099")
        assert "UI.QuerySaveGameList" in lua
        assert "Network.LoadGame(s, ServerType.SERVER_TYPE_NONE)" in lua

    def test_leave_game_failure_does_not_stop_the_load(self):
        # At the main menu there is no session to leave; the game's own path calls it too
        # (LoadGameMenu.lua:105), but an error there must not cost the load.
        assert 'pcall(function() Network.LeaveGame() end)' in lf._save_query_lua("X")


class TestIssuingTheLoad:
    def test_a_found_name_issues_the_load(self):
        conn = FakeConnection(
            states={5: "LoadGameMenu"}, answers={5: ["RESULT|FOUND"]}
        )
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", "AutoSave_0099")) is True
        assert any("Network.LoadGame" in lua for _, lua in conn.sent)

    def test_not_found_does_not_issue_it(self):
        conn = FakeConnection(
            states={5: "LoadGameMenu"}, answers={5: ["RESULT|NOT_FOUND"]}
        )
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", "AutoSave_0099")) is False

    def test_a_state_that_vanishes_is_a_load_not_a_failure(self):
        # The game blasts the FrontEnd context as the load begins (LoadGameMenu.lua:112), so
        # the reply never arrives. Reading that as failure is what makes a working load retry.
        conn = FakeConnection(states={5: "LoadGameMenu"}, raise_on_poll={5})
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", "AutoSave_0099")) is True


class TestLoadGameSave:
    def test_a_menu_state_is_used_and_the_landing_is_reported(self, monkeypatch):
        monkeypatch.setattr(
            gl, "_finish_load_sync", lambda name, wait_seconds=150: "Loaded: the game is at turn 99."
        )
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|FOUND"]})
        result = run(lf.load_game_save(conn, "AutoSave_0099"))
        assert "turn 99" in result
        assert "LoadGameMenu" in result
        assert conn.sent and all(index == 5 for index, _ in conn.sent)

    def test_a_name_only_a_later_state_has_is_still_loaded(self, monkeypatch):
        monkeypatch.setattr(
            gl, "_finish_load_sync", lambda name, wait_seconds=150: "Loaded: the game is at turn 99."
        )
        conn = FakeConnection(
            states={5: "LoadGameMenu", 24: "MainMenu"},
            answers={5: ["RESULT|NOT_FOUND"], 24: ["RESULT|FOUND"]},
        )
        result = run(lf.load_game_save(conn, "AutoSave_0099"))
        assert "MainMenu" in result
        assert {index for index, _ in conn.sent} == {5, 24}

    def test_the_requested_name_may_carry_the_extension(self, monkeypatch):
        monkeypatch.setattr(
            gl, "_finish_load_sync", lambda name, wait_seconds=150: "Loaded: the game is at turn 99."
        )
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|FOUND"]})
        result = run(lf.load_game_save(conn, "AutoSave_0099.Civ6Save"))
        assert 'if n == "AutoSave_0099" then' in conn.sent[0][1]
        assert "AutoSave_0099.Civ6Save" not in result

    def test_a_name_nothing_has_is_reported_not_clicked_through(self):
        # No state has it and no file has it: say so, rather than navigate a menu for it.
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|NOT_FOUND"]})
        result = run(lf.load_game_save(conn, "0_MCP_9999"))
        assert "not found" in result.lower()


class TestTheLandingStep:
    """`_finish_load_sync` is what makes "then call get_game_overview" true."""

    def test_a_readable_turn_is_the_result(self, monkeypatch):
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 99)
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        assert "turn 99" in gl._finish_load_sync("AutoSave_0099")

    def test_a_wrong_turn_is_a_warning_naming_both(self, monkeypatch):
        # Continue Game picks the newest save, so this is the check that catches a load that
        # resumed something else entirely.
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 117)
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        report = gl._finish_load_sync("AutoSave_0099")
        assert "WARNING" in report and "117" in report and "99" in report

    def test_a_game_already_loaded_makes_no_clicks(self, monkeypatch):
        # An in-game Lua load can land straight back in the game; the leader screen never
        # appears, so nothing may be clicked on the map.
        clicks = []
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 99)
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        monkeypatch.setattr(gl, "_click_continue_positional", lambda: clicks.append("pos"))
        monkeypatch.setattr(gl, "_click_continue_by_colour", lambda *a, **k: clicks.append("colour"))
        gl._finish_load_sync("AutoSave_0099")
        assert clicks == []
