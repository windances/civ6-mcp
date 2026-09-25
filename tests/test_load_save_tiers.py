"""How a save gets loaded: which Lua state is asked, and what the answer means.

Every rule here is pinned by a measured failure on 2026-09-25, when rolling back one save took
three failed loads and two game restarts:

* the only Lua tier ran in the `InGame` state, and the main menu has no `InGame` state — the
  tuner lists FrontEnd states there — so every menu load fell through to OCR navigation, which
  needs the game window in front and clicks a screen grab of it;
* the comparison inside that tier was `s.Name == "AutoSave_0099"` while the game's own list
  reports `AutoSave_0099.Civ6Save`, so even in-game it could not match;
* a load that started *and* finished inside the poll window looked like a state that never
  answered: the fresh FrontEnd context reports PENDING forever, the tier concluded "never
  answered", fell back to OCR, and the game sat on the leader screen with nobody to click
  CONTINUE. That one is what the user reported by hand.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import game_lifecycle as lf  # noqa: E402
from civ_mcp import game_launcher as gl  # noqa: E402

SAVE = "AutoSave_0099"


def run(coro):
    return asyncio.run(coro)


async def _no_sleep(seconds: float) -> None:
    """Stand-in for asyncio.sleep: the poll window is a real five seconds otherwise."""
    return None


@pytest.fixture(autouse=True)
def _instant_polls(monkeypatch):
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)


async def _async_menu_nav(name: str) -> str:
    """Stand-in for the OCR fallback, so a tier-2 test never clicks a real menu."""
    return f"menu nav for {name}"


class FakeConnection:
    """A tuner connection whose states answer from a script.

    ``answers`` maps a state index to what its poll returns; the query call is recognised by the
    Lua it carries, so a state can be made to answer NOT_FOUND, FOUND, LOST, PENDING, or to
    raise.
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
        self.gamecore_index = None
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


@pytest.fixture()
def at_the_menu(monkeypatch):
    """No game in progress and no turn in the save's name: the main-menu case."""
    monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: None)
    monkeypatch.setattr(gl, "_save_turn", lambda name: None)


@pytest.fixture()
def landing(monkeypatch):
    """A landing step that reports success without touching a game."""
    monkeypatch.setattr(
        gl, "_finish_load_sync", lambda name, wait_seconds=150: "Loaded: the game is at turn 99."
    )


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
        lua = lf._save_query_lua(SAVE)
        assert 'gsub("%.Civ6Save$", "")' in lua
        assert f'if n == "{SAVE}" then' in lua
        assert f'if s.Name == "{SAVE}" then' not in lua

    def test_it_loads_the_record_it_matched(self):
        lua = lf._save_query_lua(SAVE)
        assert "UI.QuerySaveGameList" in lua
        assert "Network.LoadGame(s, ServerType.SERVER_TYPE_NONE)" in lua

    def test_leave_game_failure_does_not_stop_the_load(self):
        # At the main menu there is no session to leave; the game's own path calls it too
        # (LoadGameMenu.lua:105), but an error there must not cost the load.
        assert 'pcall(function() Network.LeaveGame() end)' in lf._save_query_lua("X")

    def test_the_poll_reports_a_rebuilt_context_as_lost(self):
        # The markers the query set being gone is how a load that starts and ends inside the
        # poll window is recognised; without it the fresh context reads PENDING (2026-09-25).
        poll = lf._save_poll_lua()
        assert "ExposedMembers == nil or ExposedMembers.MCPLoadDone == nil" in poll
        assert "LOST" in poll


class TestReadingOneStatesAnswer:
    def test_found_means_the_load_was_issued(self):
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|FOUND"]})
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", SAVE)) == "FOUND"
        assert any("Network.LoadGame" in lua for _, lua in conn.sent)

    def test_not_found_is_the_games_own_answer(self):
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|NOT_FOUND"]})
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", SAVE)) == "NOT_FOUND"

    def test_a_state_that_vanishes_is_a_load_not_a_failure(self):
        # The game blasts the FrontEnd context as the load begins (LoadGameMenu.lua:112), so the
        # reply never arrives. Reading that as failure is what makes a working load retry.
        conn = FakeConnection(states={5: "LoadGameMenu"}, raise_on_poll={5})
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", SAVE)) == "FOUND"

    def test_a_rebuilt_context_is_a_load_not_a_silent_state(self):
        # Measured 2026-09-25: the tuner came back in about three seconds, so the poll read a
        # fresh context - markers gone - for all five states, and the load was called a failure.
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["LOST"]})
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", SAVE)) == "FOUND"

    def test_no_answer_at_all_is_silent(self):
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["PENDING"]})
        assert run(lf._lua_load_in_state(conn, 5, "LoadGameMenu", SAVE)) == "SILENT"


class TestLoadGameSave:
    def test_a_menu_state_is_used_and_the_landing_is_reported(self, at_the_menu, landing):
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|FOUND"]})
        result = run(lf.load_game_save(conn, SAVE))
        assert "turn 99" in result
        assert "LoadGameMenu" in result
        assert conn.sent and all(index == 5 for index, _ in conn.sent)

    def test_a_silent_state_hands_over_to_the_next_one(self, at_the_menu, landing):
        conn = FakeConnection(
            states={5: "LoadGameMenu", 24: "MainMenu"},
            answers={5: ["PENDING"], 24: ["RESULT|FOUND"]},
        )
        result = run(lf.load_game_save(conn, SAVE))
        assert "MainMenu" in result
        assert {index for index, _ in conn.sent} == {5, 24}

    def test_not_found_does_not_ask_the_other_states(self, at_the_menu, monkeypatch):
        # Every state returns the same list, so asking the rest is how a second load goes out
        # for a file that is simply not there. (Tier 2 then navigates, which is the OCR
        # fallback and not what this test is about.)
        monkeypatch.setattr(gl, "load_save_from_menu", _async_menu_nav)
        conn = FakeConnection(
            states={5: "LoadGameMenu", 24: "MainMenu", 30: "FrontEnd"},
            answers={5: ["RESULT|NOT_FOUND"]},
        )
        run(lf.load_game_save(conn, SAVE))
        assert {index for index, _ in conn.sent} == {5}

    def test_a_load_that_already_started_is_landed_not_re_issued(self, monkeypatch, landing):
        # The tuner is back and answering, but no state has our markers: something is opening.
        # Check for an open game before navigating a main menu that is not on screen.
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 99)
        monkeypatch.setattr(gl, "_save_turn", lambda name: None)
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["PENDING"]})
        result = run(lf.load_game_save(conn, SAVE))
        assert "already started" in result and "turn 99" in result

    def test_sitting_on_the_save_is_not_a_load(self, monkeypatch):
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 99)
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|FOUND"]})
        result = run(lf.load_game_save(conn, SAVE))
        assert "Already loaded" in result
        assert conn.sent == [], "nothing is asked of the game when the position is already open"

    def test_the_requested_name_may_carry_the_extension(self, at_the_menu, landing):
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|FOUND"]})
        result = run(lf.load_game_save(conn, f"{SAVE}.Civ6Save"))
        assert f'if n == "{SAVE}" then' in conn.sent[0][1]
        assert f"{SAVE}.Civ6Save" not in result

    def test_a_silent_front_end_is_asked_again(self, at_the_menu, monkeypatch):
        # 47s after a launch every FrontEnd state can be silent, because the front end is not
        # ready - not because the save is missing. Measured 2026-09-25: the same query answered
        # 207 saves a minute later, and the run in between had already fallen back to OCR.
        monkeypatch.setattr(gl, "load_save_from_menu", _async_menu_nav)
        conn = FakeConnection(states={5: "LoadGameMenu", 24: "MainMenu"})
        run(lf.load_game_save(conn, SAVE))
        asked = [index for index, lua in conn.sent if "QuerySaveGameList" in lua]
        assert asked == [5, 24, 5, 24, 5, 24], "two states, three rounds, in order"

    def test_a_name_nothing_has_is_reported_not_clicked_through(self, at_the_menu):
        # No state has it and no file has it: say so, rather than navigate a menu for it.
        conn = FakeConnection(states={5: "LoadGameMenu"}, answers={5: ["RESULT|NOT_FOUND"]})
        result = run(lf.load_game_save(conn, "0_MCP_9999"))
        assert "not found" in result.lower()


class TestTheLandingStep:
    """`_finish_load_sync` is what makes "then call get_game_overview" true."""

    def test_a_readable_turn_is_the_result(self, monkeypatch):
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 99)
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        assert "turn 99" in gl._finish_load_sync(SAVE)

    def test_a_wrong_turn_is_a_warning_naming_both(self, monkeypatch):
        # Continue Game picks the newest save, so this is the check that catches a load that
        # resumed something else entirely.
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 117)
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        report = gl._finish_load_sync(SAVE)
        assert "WARNING" in report and "117" in report and "99" in report

    def test_a_game_already_loaded_makes_no_clicks(self, monkeypatch):
        # An in-game Lua load can land straight back in the game; the leader screen never
        # appears, so nothing may be clicked on the map.
        clicks = []
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 99)
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        monkeypatch.setattr(gl, "_click_continue_positional", lambda: clicks.append("pos"))
        monkeypatch.setattr(gl, "_click_continue_by_colour", lambda *a, **k: clicks.append("colour"))
        gl._finish_load_sync(SAVE)
        assert clicks == []

    def test_the_continue_click_is_not_gated_on_the_ocr_signature(self, monkeypatch):
        # The control is drawn, not laid out, so the colour search is both the detector and the
        # click. It used to run only when `_leader_screen_detected` matched an OCR signature that
        # does not survive on that screen, so the one working method was never tried and two runs
        # on 2026-09-25 ended with the game parked on CONTINUE waiting for a human to click it.
        turns = iter([None, None, 99])
        clicks = []
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: next(turns, 99))
        monkeypatch.setattr(gl, "_save_turn", lambda name: 99)
        monkeypatch.setattr(gl, "_leader_screen_detected", lambda results: False)
        monkeypatch.setattr(gl.time, "sleep", lambda seconds: None)
        monkeypatch.setattr(
            gl, "_click_continue_by_colour", lambda *a, **k: bool(clicks.append("colour")) or True
        )
        report = gl._finish_load_sync(SAVE)
        assert clicks, "the colour search must be attempted without the OCR signature"
        assert "turn 99" in report
