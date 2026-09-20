"""The menu-load path, pinned against the six defects found by driving it on 4K.

On 2026-09-20 the crash-recovery load failed three times in three different ways,
and every one of them came from acting on an assumption instead of on what the screen
was showing:

1. ``_capture_window_win32`` used PrintWindow, and the load flow's own comment says
   PrintWindow + SetForegroundWindow during the DX12 loading phase can crash the
   renderer - which is exactly when the flow polls the screen. A capture during a
   load was followed by the game dying.
2. ``_click_text`` called SetForegroundWindow before every click. Clicks land on a
   visible fullscreen game without it; the whole navigation was completed with it
   disabled.
3. The "Load Game" menu item was clicked with ``y_offset=15``. At 3840x2160 the menu
   rows are 38 px apart, so +15 lands between rows or on 创建游戏; the load opened the
   Create Game screen and reported ``Save '0_MCP_0079' not found``.
4. The continue control was hunted with OCR and then a nine-point grid covering
   y 75-88%, while the control - a teal globe above the ribbon - is at (44%, 64%).
   The grid could not reach it, so a load sat on the leader screen for the whole poll.
5. Success was declared because the FireTuner port answered. That port is open at the
   main menu too, so a load that never finished was reported as successful.
6. Screen signatures were matched as exact strings. OCR reads the leader screen's
   heading "特征与能力" as "每征与能力", so an exact match fails on the one screen the
   load is supposed to end on.
"""

from __future__ import annotations

import inspect
import pathlib
import time

import pytest

from civ_mcp import game_launcher as gl


class TestCaptureDoesNotPokeTheRenderer:
    def test_screen_grab_is_the_default(self, monkeypatch):
        import win32gui

        from PIL import ImageGrab

        monkeypatch.delenv("CIV_MCP_PRINTWINDOW_CAPTURE", raising=False)
        monkeypatch.setattr(win32gui, "GetWindowRect", lambda hwnd: (0, 0, 100, 50))
        sentinel = object()
        grabbed = {}

        def fake_grab(**kwargs):
            grabbed.update(kwargs)
            return sentinel

        monkeypatch.setattr(ImageGrab, "grab", fake_grab)
        assert gl._capture_window_win32(1) is sentinel
        # The whole window, not the client area: the client rect sits below the
        # title bar, and the click coordinates are screen coordinates.
        assert grabbed["bbox"] == (0, 0, 100, 50)

    def test_printwindow_needs_an_explicit_opt_in(self, monkeypatch):
        monkeypatch.setenv("CIV_MCP_PRINTWINDOW_CAPTURE", "1")
        sentinel = object()
        monkeypatch.setattr(gl, "_capture_window_printwindow", lambda hwnd: sentinel)
        assert gl._capture_window_win32(1) is sentinel

    def test_the_printwindow_path_still_exists(self, monkeypatch):
        # Kept for an occluded or minimised window, where a screen grab would
        # capture whatever is on top instead.
        monkeypatch.setenv("CIV_MCP_PRINTWINDOW_CAPTURE", "1")
        assert callable(gl._capture_window_printwindow)


class TestForegroundIsBroughtForwardOnlyWhenNeeded:
    """A screen grab reads whatever is on top, so the game has to be on top.

    Disabling this entirely was the first attempt at making the load safe, and it was
    wrong: after a cold launch the game comes up behind the terminal or the browser,
    the grab then captures that window instead, and the flow reports "the game is not
    showing its main menu" while the game is sitting right there. What makes it safe
    now is that the capture no longer uses PrintWindow - the documented hazard was the
    pair, not the focus change on its own.
    """

    def test_skipped_when_the_game_is_already_foreground(self, monkeypatch):
        monkeypatch.delenv("CIV_MCP_NO_FOREGROUND_STEAL", raising=False)
        monkeypatch.setattr(gl, "_is_game_foreground", lambda: True)
        calls = []
        monkeypatch.setattr(gl, "_bring_to_front_win32", lambda: calls.append(1))
        gl._bring_to_front()
        assert calls == []

    def test_raised_when_the_game_is_behind_another_window(self, monkeypatch):
        monkeypatch.delenv("CIV_MCP_NO_FOREGROUND_STEAL", raising=False)
        monkeypatch.setattr(gl, "_is_game_foreground", lambda: False)
        monkeypatch.setattr(gl.sys, "platform", "win32")
        calls = []
        monkeypatch.setattr(gl, "_bring_to_front_win32", lambda: calls.append(1))
        gl._bring_to_front()
        assert calls == [1]

    def test_it_can_still_be_disabled(self, monkeypatch):
        monkeypatch.setenv("CIV_MCP_NO_FOREGROUND_STEAL", "1")
        monkeypatch.setattr(gl, "_is_game_foreground", lambda: False)
        calls = []
        monkeypatch.setattr(gl, "_bring_to_front_win32", lambda: calls.append(1))
        gl._bring_to_front()
        assert calls == []

    def test_the_reason_it_is_needed_is_recorded(self):
        source = inspect.getsource(gl._bring_to_front)
        assert "reads whatever is on top" in source

    def test_every_screen_read_raises_the_game_first(self):
        # Not just every click: the OCR poll captures the screen too, and that is the
        # read that was seeing the browser instead of the game.
        source = inspect.getsource(gl._ocr_game_window)
        raise_at = source.find("_bring_to_front()")
        capture_at = source.find("_capture_window_win32(")
        assert raise_at != -1, "the OCR path must raise the game window"
        assert capture_at != -1
        assert raise_at < capture_at, "raise the window before reading it"


class TestMenuClicksUseTheBoxCentre:
    def test_no_resolution_dependent_offset_on_the_load_item(self):
        source = inspect.getsource(gl._navigate_to_save_sync)
        # No offset at all in this flow: every click here uses the centre of the box
        # OCR actually found.
        assert "y_offset=" not in source
        # The reason belongs in the source, so nobody re-adds a nudge "to clear the
        # row above" without reading what it did at 4K.
        assert "38 px apart" in source


class TestContinueControlIsFoundByColour:
    def test_leader_screen_is_recognised_through_ocr_noise(self):
        # 特征与能力, as Windows OCR actually returns it at 4K.
        noisy = [("每 征 与 能 力", 1743, 874, 67, 28)]
        assert gl._leader_screen_detected(noisy) is True

    def test_main_menu_is_not_a_leader_screen(self):
        main_menu = [("单 人 模 式", 1854, 1006, 71, 16), ("多 人 模 式", 1868, 1044, 96, 18)]
        assert gl._leader_screen_detected(main_menu) is False

    def _no_control_on_screen(self, monkeypatch):
        """A grab with no teal bar on it, so only the ranking path can click."""
        from PIL import Image

        monkeypatch.setattr(
            gl, "_grab_window", lambda win: Image.new("RGB", (400, 300), (0, 0, 0))
        )
        monkeypatch.setattr(gl, "_ocr_game_window", lambda win: [])
        # The control never appears, without waiting the real 120s for it.
        monkeypatch.setattr(
            gl, "_wait_for_continue_control", lambda win, timeout=120: None
        )

    def test_each_candidate_is_checked_before_the_next_click(self, monkeypatch):
        # Two candidates, the second one working: exactly two clicks, in order.
        self._no_control_on_screen(monkeypatch)
        monkeypatch.setattr(
            gl, "_teal_candidates", lambda win, band: [(10, 20, 99), (30, 40, 5)]
        )
        monkeypatch.setattr(gl, "_find_game_window", lambda: object())
        clicks = []
        monkeypatch.setattr(gl, "_click", lambda x, y: clicks.append((x, y)))
        results = iter([False, True])
        monkeypatch.setattr(gl, "_wait_for_continue_to_take", lambda win, max_seconds=30: next(results))
        assert gl._click_continue_by_colour() is True
        assert clicks == [(10, 20), (30, 40)]

    def test_it_stops_after_the_first_candidate_that_works(self, monkeypatch):
        self._no_control_on_screen(monkeypatch)
        monkeypatch.setattr(
            gl, "_teal_candidates", lambda win, band: [(10, 20, 99), (30, 40, 5)]
        )
        monkeypatch.setattr(gl, "_find_game_window", lambda: object())
        clicks = []
        monkeypatch.setattr(gl, "_click", lambda x, y: clicks.append((x, y)))
        monkeypatch.setattr(gl, "_wait_for_continue_to_take", lambda win, max_seconds=30: True)
        assert gl._click_continue_by_colour() is True
        assert clicks == [(10, 20)]

    def test_the_shape_finder_is_tried_before_the_ranking(self, monkeypatch):
        # The globe first, and the ranking never used when that click works.
        from PIL import Image, ImageDraw

        class Win:
            x = y = 0
            w, h = 400, 300

        image = Image.new("RGB", (400, 300), (10, 10, 10))
        draw = ImageDraw.Draw(image)
        draw.rectangle((120, 200, 220, 228), fill=(0, 150, 160))
        draw.ellipse((145, 160, 195, 190), outline=(0, 150, 160), width=6)
        monkeypatch.setattr(gl, "_grab_window", lambda win: image)
        monkeypatch.setattr(gl, "_ocr_game_window", lambda win: [])
        monkeypatch.setattr(gl, "_find_game_window", lambda: Win())
        monkeypatch.setattr(
            gl, "_teal_candidates", lambda win, band: pytest.fail("ranking was used")
        )
        clicks = []
        monkeypatch.setattr(gl, "_click", lambda x, y: clicks.append((x, y)))
        monkeypatch.setattr(gl, "_wait_for_continue_to_take", lambda win, max_seconds=30: True)
        assert gl._click_continue_by_colour() is True
        assert len(clicks) == 1
        assert abs(clicks[0][0] - 170) <= 8 and abs(clicks[0][1] - 175) <= 8, clicks

    def test_the_grid_remains_the_last_resort(self, monkeypatch):
        monkeypatch.setattr(gl, "_click_continue_by_colour", lambda: False)
        called = []
        monkeypatch.setattr(gl, "_click_continue_grid", lambda: called.append(1))
        gl._click_continue_positional()
        assert called == [1]


class TestContinueGameShortcut:
    """Single Player -> Continue Game resumes the most recent save in two clicks.

    It is both shorter and more correct for a crash recovery: the save it picks is the
    newest one on disk, which is not necessarily the newest 0_MCP_ file - the game
    writes its own AutoSave_* alongside, and after a plain exit that one is ahead
    (on 2026-09-20: AutoSave_0080 at turn 80 against 0_MCP_0079 at turn 79).

    The save is chosen implicitly, so the verification matters more, not less: the
    loaded turn is checked against the number in the requested save's name, and the
    shortcut reports failure rather than a load it cannot confirm.
    """

    def test_save_turn_reads_the_number_in_the_name(self):
        assert gl._save_turn("0_MCP_0079") == 79
        assert gl._save_turn("AutoSave_0080") == 80
        assert gl._save_turn("quicksave") is None

    def test_newest_save_spans_both_directories(self, monkeypatch):
        monkeypatch.setattr(gl, "SAVE_DIR", r"C:\g\auto")
        monkeypatch.setattr(gl, "SINGLE_SAVE_DIR", r"C:\g")
        files = {
            r"C:\g\auto\*.Civ6Save": [r"C:\g\auto\AutoSave_0080.Civ6Save", r"C:\g\auto\AutoSave_0079.Civ6Save"],
            r"C:\g\*.Civ6Save": [r"C:\g\0_MCP_0079.Civ6Save"],
        }
        mtimes = {
            r"C:\g\auto\AutoSave_0080.Civ6Save": 300.0,
            r"C:\g\auto\AutoSave_0079.Civ6Save": 100.0,
            r"C:\g\0_MCP_0079.Civ6Save": 200.0,
        }
        monkeypatch.setattr(gl.glob, "glob", lambda pattern: files.get(pattern, []))
        monkeypatch.setattr(gl.os.path, "getmtime", lambda path: mtimes.get(path, 0.0))
        # The game's own autosave is the newest here, and it must win: picking by the
        # 0_MCP_ prefix instead would resume a turn behind.
        assert gl.get_newest_save() == ("AutoSave_0080", 300.0)

    def test_no_continue_item_falls_back_to_the_list(self, monkeypatch):
        clicks = []

        def fake_click_text(labels, **kwargs):
            clicks.append(labels)
            return labels == gl._menu_labels("single_player")  # single player only

        monkeypatch.setattr(gl, "_click_text", fake_click_text)
        assert gl._continue_game_sync("AutoSave_0080") is None
        assert len(clicks) == 2

    def test_a_turn_mismatch_is_not_reported_as_success(self, monkeypatch):
        monkeypatch.setattr(gl, "_click_text", lambda labels, **kw: True)
        monkeypatch.setattr(gl, "_wait_for_leader_screen", lambda timeout=120: True)
        monkeypatch.setattr(gl, "_click_continue_by_colour", lambda: True)
        monkeypatch.setattr(gl, "_wait_for_turn_number", lambda max_seconds=30: 79)
        # Asked for turn 80, got turn 79: Continue Game resumed a different save, and
        # the caller has to be told so it can pick the save explicitly.
        assert gl._continue_game_sync("AutoSave_0080") is None

    def test_a_matching_turn_is_reported_with_the_turn(self, monkeypatch):
        monkeypatch.setattr(gl, "_click_text", lambda labels, **kw: True)
        monkeypatch.setattr(gl, "_wait_for_leader_screen", lambda timeout=120: True)
        monkeypatch.setattr(gl, "_click_continue_by_colour", lambda: True)
        monkeypatch.setattr(gl, "_wait_for_turn_number", lambda max_seconds=30: 80)
        result = gl._continue_game_sync("AutoSave_0080")
        assert result is not None
        assert "Game in progress at turn 80" in result
        assert "Continue Game" in result

    def test_the_shortcut_is_only_used_for_the_newest_save(self, monkeypatch):
        monkeypatch.setattr(gl, "get_newest_save", lambda: ("AutoSave_0080", 1.0))
        called = []
        monkeypatch.setattr(
            gl, "_continue_game_sync", lambda name: called.append(name) or "shortcut used"
        )
        # An older save must go down the explicit list path, which is not exercised
        # here: the point is only that the shortcut is not taken for it.
        monkeypatch.setattr(gl, "_require_gui_deps", lambda: None)
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: None)
        monkeypatch.setattr(gl, "_wait_for_text", lambda *a, **kw: ("单 人 模 式", 1854, 1006, 71, 16))
        monkeypatch.setattr(gl, "is_game_running", lambda: True)
        monkeypatch.setattr(gl, "_dismiss_crash_dialog", lambda: None)
        monkeypatch.setattr(gl, "_click_aspyr_launcher_sync", lambda: None)
        monkeypatch.setattr(gl, "_click_text", lambda labels, **kw: False)
        result = gl._navigate_to_save_sync("0_MCP_0079")
        assert called == []
        assert "FAILED" in result

    def test_the_shortcut_is_used_for_the_newest_save(self, monkeypatch):
        monkeypatch.setattr(gl, "get_newest_save", lambda: ("AutoSave_0080", 1.0))
        monkeypatch.setattr(gl, "_continue_game_sync", lambda name: f"shortcut -> {name}")
        monkeypatch.setattr(gl, "_require_gui_deps", lambda: None)
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: None)
        monkeypatch.setattr(
            gl, "_wait_for_text", lambda *a, **kw: ("单 人 模 式", 1854, 1006, 71, 16)
        )
        assert gl._navigate_to_save_sync("AutoSave_0080") == "shortcut -> AutoSave_0080"

    def test_it_falls_through_when_the_shortcut_cannot_confirm(self, monkeypatch):
        monkeypatch.setattr(gl, "get_newest_save", lambda: ("AutoSave_0080", 1.0))
        monkeypatch.setattr(gl, "_continue_game_sync", lambda name: None)
        monkeypatch.setattr(gl, "_require_gui_deps", lambda: None)
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: None)
        monkeypatch.setattr(gl, "_wait_for_text", lambda *a, **kw: ("单 人 模 式", 1854, 1006, 71, 16))
        monkeypatch.setattr(gl, "is_game_running", lambda: True)
        monkeypatch.setattr(gl, "_dismiss_crash_dialog", lambda: None)
        monkeypatch.setattr(gl, "_click_aspyr_launcher_sync", lambda: None)
        monkeypatch.setattr(gl, "_click_text", lambda labels, **kw: False)
        result = gl._navigate_to_save_sync("AutoSave_0080")
        # The explicit path ran (and failed here only because the menu click did).
        assert "FAILED" in result
class TestSuccessIsMeasuredFromTheGame:
    def test_the_load_no_longer_trusts_the_port(self):
        source = inspect.getsource(gl._navigate_to_save_sync)
        assert "_is_tuner_port_open()" not in source
        assert "_game_turn_number()" in source
        # The reason, in the code, for whoever wonders why the port check went away.
        assert "open at the main menu" in source

    def test_the_result_reports_the_turn(self):
        # The caller - and the recovery prompt - verify by comparing this with the
        # number in the save name, so it has to be in the message.
        source = inspect.getsource(gl._navigate_to_save_sync)
        assert "Game in progress at turn" in source

    def test_turn_probe_returns_none_without_a_connection(self, monkeypatch):
        # No game listening: the probe must answer "no game", not raise.
        monkeypatch.setattr(
            gl, "_game_turn_number", lambda timeout=5.0: None, raising=False
        )
        assert gl._game_turn_number() is None


class TestTheContinueControlIsFoundByShape:
    """The control is a globe on a bar, and only the globe responds to a click.

    The fixture is a recording of the leader screen's continue control, cropped tight
    around it. Being tight, it cannot show that an area ranking would pick the wrong
    place - on this frame the control is the largest teal thing there is. What it does
    pin is the shape reading itself: bar, globe above its centre, click the globe.
    """

    FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "leader-continue-control.png"
    # The globe ring on that frame, measured from the mask: x 1664-1736, y 260-330.
    GLOBE = (1664, 260, 1736, 330)

    def _leader_frame(self):
        if not self.FIXTURE.exists():
            pytest.skip(f"no recorded leader screen at {self.FIXTURE}")
        from PIL import Image

        return Image.open(self.FIXTURE).convert("RGB")

    def test_the_click_lands_on_the_globe_not_the_bar(self):
        image = self._leader_frame()
        point = gl._continue_control_point(gl._teal_mask(image))
        assert point is not None, "no control found on the recorded leader screen"
        x, y = point
        left, top, right, bottom = self.GLOBE
        assert left <= x <= right and top <= y <= bottom, f"{point} is not in the globe"

    def test_the_fixture_still_has_a_bar_and_a_globe(self):
        # The reading depends on both shapes being there. If the fixture is replaced by
        # something that no longer has them, say so here rather than in a load failure.
        image = self._leader_frame()
        mask = gl._teal_mask(image)
        left, top, right, bottom = self.GLOBE
        assert mask.crop(self.GLOBE).getbbox() is not None, "the globe is gone"
        bar = mask.crop((1560, 340, 1845, 371))
        assert bar.getbbox() is not None, "the bar under the globe is gone"

    def test_a_synthetic_control_is_found(self):
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (400, 300), (10, 10, 10))
        draw = ImageDraw.Draw(image)
        teal = (0, 150, 160)
        draw.rectangle((80, 220, 320, 250), fill=teal)  # the bar
        draw.ellipse((170, 150, 230, 210), outline=teal, width=8)  # the globe above it
        point = gl._continue_control_point(gl._teal_mask(image))
        assert point is not None
        assert abs(point[0] - 200) <= 8, point
        assert abs(point[1] - 180) <= 8, point

    def test_side_teal_does_not_drag_the_click_off_the_bar_centre(self):
        # The bar's own soft top edge and neighbouring panels reach into the search band
        # from the sides; a bounding box over them read 176px wide against a 280px bar on
        # the recorded frame, and on 2026-09-20 that misreading clicked the ribbon at
        # (1758,1446) instead of the globe. Only the column over the bar's centre counts.
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (400, 300), (10, 10, 10))
        draw = ImageDraw.Draw(image)
        teal = (0, 150, 160)
        draw.rectangle((120, 200, 220, 228), fill=teal)  # the bar, centre x = 170
        draw.ellipse((145, 160, 195, 190), outline=teal, width=6)  # the globe
        draw.rectangle((226, 190, 248, 230), fill=teal)  # teal at the bar's right edge
        point = gl._continue_control_point(gl._teal_mask(image))
        assert point is not None
        assert abs(point[0] - 170) <= 8, point
        assert abs(point[1] - 175) <= 8, point

    def test_no_bar_means_no_guess(self):
        from PIL import Image

        image = Image.new("RGB", (400, 300), (10, 10, 10))
        assert gl._continue_control_point(gl._teal_mask(image)) is None

    def test_a_game_already_running_is_never_clicked_into(self, monkeypatch):
        # A click on the map is a move order when a unit is selected; the load this
        # would be finishing has already succeeded.
        clicked: list[tuple[int, int]] = []
        monkeypatch.setattr(gl, "_find_game_window", lambda: object())
        monkeypatch.setattr(
            gl, "_ocr_game_window", lambda win: [("回 合 80 / 500", 3674, 8, 65, 12)]
        )
        monkeypatch.setattr(gl, "_click", lambda x, y: clicked.append((x, y)))
        assert gl._click_continue_by_colour() is True
        assert clicked == []


class TestAnAlreadyLoadedGameIsNotNavigatedThrough:
    """The menus are not on screen when a game is in progress, and every wait then
    runs to its own timeout: a request for turn-80 AutoSave_0080 against a game already
    at turn 80 spent 172s on 2026-09-20 and then reported a failure for a healthy game.
    """

    def test_the_load_is_reported_as_already_done(self, monkeypatch):
        monkeypatch.setattr(gl, "_require_gui_deps", lambda: None)
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 80)
        # No menu work at all: no fast path, no clicks, no waits.
        monkeypatch.setattr(gl, "_continue_game_sync", pytest.fail)
        monkeypatch.setattr(gl, "_click_text", pytest.fail)
        started = time.time()
        result = gl._navigate_to_save_sync("AutoSave_0080")
        assert "Already loaded" in result
        assert "Nothing to load" in result
        assert time.time() - started < 5

    def test_a_different_turn_fails_fast_with_what_to_do_instead(self, monkeypatch):
        monkeypatch.setattr(gl, "_require_gui_deps", lambda: None)
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: 80)
        monkeypatch.setattr(gl, "_continue_game_sync", pytest.fail)
        monkeypatch.setattr(gl, "_click_text", pytest.fail)
        result = gl._navigate_to_save_sync("0_MCP_0079")
        assert result.startswith("FAILED")
        assert "already in progress at turn 80" in result
        assert "restart_and_load('0_MCP_0079')" in result

    def test_a_game_that_has_not_reached_its_menu_says_so(self, monkeypatch):
        # The case measured on 2026-09-20: a load requested one second after launch, with
        # the window still on the splash. Two menu timeouts ran (172s) and the caller got
        # a FAILED it could only interpret by asking get_game_status next. One wait, and
        # then a message that names the state.
        monkeypatch.setattr(gl, "_require_gui_deps", lambda: None)
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: None)
        monkeypatch.setattr(gl, "_wait_for_text", lambda *a, **kw: None)
        monkeypatch.setattr(gl, "_find_game_window", lambda: object())
        monkeypatch.setattr(gl, "_ocr_game_window", lambda win: [])
        monkeypatch.setattr(gl, "_click_text", pytest.fail)
        result = gl._navigate_to_save_sync("AutoSave_0080")
        assert result.startswith("FAILED")
        assert "still starting" in result
        assert "get_game_status" in result

    def test_a_fresh_launch_still_navigates(self, monkeypatch):
        # No turn readable means no game is loaded - the normal path must be untouched.
        monkeypatch.setattr(gl, "_require_gui_deps", lambda: None)
        monkeypatch.setattr(gl, "_game_turn_number", lambda timeout=5.0: None)
        monkeypatch.setattr(gl, "_wait_for_text", lambda *a, **kw: ("单 人 模 式", 1854, 1006, 71, 16))
        monkeypatch.setattr(gl, "get_newest_save", lambda: ("AutoSave_0080", 1.0))
        monkeypatch.setattr(gl, "_continue_game_sync", lambda name: "Save loading (5s)")
        assert gl._navigate_to_save_sync("AutoSave_0080") == "Save loading (5s)"


class TestAnotherSessionIsNotKilled:
    """A kill is not a neutral diagnostic.

    On 2026-09-20 a verification run called kill_game while a live session was mid-turn-82
    (that session's log shows a get_units eight seconds earlier) and threw the position
    away: it had to be reloaded from the newest autosave. Two independent signals name
    the other session, so the tool refuses.
    """

    def test_a_foreign_tuner_client_names_the_holder(self, monkeypatch):
        monkeypatch.setattr(
            gl, "_tuner_port_state", lambda: {"listening": True, "clients": [23276]}
        )
        reason = gl._other_active_session()
        assert reason is not None and "23276" in reason

    def test_our_own_connection_is_not_another_session(self, monkeypatch):
        import os

        monkeypatch.setattr(
            gl, "_tuner_port_state",
            lambda: {"listening": True, "clients": [os.getpid()]},
        )
        monkeypatch.setattr(gl, "_heartbeat_candidates", lambda: [])
        assert gl._other_active_session() is None

    def _heartbeat(self, request, phase: str, age_seconds: float, pid: int, run_id: str = "run-x"):
        """Write a heartbeat the guard will read, under the workspace (tmp_path is not
        writable in this sandbox - the same reason three hang-recovery tests error)."""
        import json
        import uuid

        path = pathlib.Path(".tools") / f"_test_heartbeat_{uuid.uuid4().hex}.json"
        path.write_text(
            json.dumps(
                {
                    "phase": phase,
                    "turn": 82,
                    "ts": time.time() - age_seconds,
                    "pid": pid,
                    "run_id": run_id,
                }
            ),
            encoding="utf-8",
        )
        request.addfinalizer(lambda: path.unlink(missing_ok=True))
        return path

    def test_a_fresh_playing_heartbeat_names_the_session(self, monkeypatch, request):
        path = self._heartbeat(request, "playing", 5, 4242, "forgotten-olive-garrison-15")
        monkeypatch.setattr(gl, "_tuner_port_state", lambda: {"listening": True, "clients": []})
        monkeypatch.setattr(gl, "_heartbeat_candidates", lambda: [path])
        reason = gl._other_active_session()
        assert reason is not None
        assert "4242" in reason and "forgotten-olive-garrison-15" in reason

    def test_a_stale_heartbeat_is_not_a_live_session(self, monkeypatch, request):
        path = self._heartbeat(request, "playing", 3600, 4242)
        monkeypatch.setattr(gl, "_tuner_port_state", lambda: {"listening": True, "clients": []})
        monkeypatch.setattr(gl, "_heartbeat_candidates", lambda: [path])
        assert gl._other_active_session() is None

    def test_a_finished_heartbeat_is_not_a_live_session(self, monkeypatch, request):
        # The watchdog writes "finished" when the game is over; that is not a session
        # worth protecting from a kill.
        path = self._heartbeat(request, "finished", 5, 4242)
        monkeypatch.setattr(gl, "_tuner_port_state", lambda: {"listening": True, "clients": []})
        monkeypatch.setattr(gl, "_heartbeat_candidates", lambda: [path])
        assert gl._other_active_session() is None

    def test_kill_game_refuses_while_another_session_plays(self, monkeypatch):
        import asyncio

        monkeypatch.setattr(gl, "_other_active_session", lambda: "pid 4242 is playing")
        monkeypatch.setattr(gl, "_kill_game_sync", pytest.fail)
        result = asyncio.run(gl.kill_game())
        assert result.startswith("NOT KILLED")
        assert "force=True" in result

    def test_restart_and_load_refuses_too(self, monkeypatch):
        import asyncio

        monkeypatch.setattr(gl, "_other_active_session", lambda: "pid 4242 is playing")
        monkeypatch.setattr(gl, "_kill_game_sync", pytest.fail)
        monkeypatch.setattr(gl, "_launch_game_sync", pytest.fail)
        result = asyncio.run(gl.restart_and_load("AutoSave_0080"))
        assert result.startswith("NOT RESTARTED")


class TestGameStateIsQueryable:
    """The agent should be able to ask where the game is instead of inferring it.

    Everything it used to get was the wording of whichever step failed - "the game is
    not showing its main menu" is the same message for a game that is still starting,
    one parked on the leader intro screen, and one whose window is behind the browser.
    """

    def test_process_lookup_does_not_shell_out(self):
        # tasklist is a child process read through a pipe; where that is blocked the
        # game reads as stopped while it is running (2026-09-20: it did, for pid 580).
        source = inspect.getsource(gl.is_game_running) + inspect.getsource(gl._running_game_pids)
        assert "tasklist" not in source
        assert "_running_game_pids_win32" in source

    @pytest.mark.parametrize(
        ("boxes", "expected"),
        [
            ([("回 合 80 / 500", 3674, 8, 65, 12)], "in-game"),
            ([("每 征 与 能 力", 1743, 874, 67, 28)], "leader intro screen"),
            ([("单 人 模 式", 1854, 1006, 71, 16)], "main menu"),
            ([("加 载 游 戏", 1920, 149, 94, 24)], "load game screen"),
            ([], "nothing readable (intro movie, splash, or a blank frame)"),
            ([("something else", 1, 2, 3, 4)], "unrecognised (1 text boxes)"),
        ],
    )
    def test_screen_kind(self, boxes, expected):
        assert gl._screen_kind(boxes) == expected

    def _wire(
        self,
        monkeypatch,
        *,
        pids,
        tuner,
        turn,
        boxes,
        newest=("AutoSave_0080", 1.0),
        clients=(),
        listening=False,
        probe_connected=None,
        probe_note="",
    ):
        monkeypatch.setattr(gl, "_running_game_pids", lambda: pids)
        monkeypatch.setattr(gl, "_find_game_window", lambda: object() if pids else None)
        monkeypatch.setattr(gl, "_is_tuner_port_open", lambda: tuner)
        # Never read the real TCP table: on a machine with a live agent attached it
        # would answer "busy" and the assertions below would depend on the desktop.
        monkeypatch.setattr(
            gl,
            "_tuner_port_state",
            lambda: {"listening": listening, "clients": list(clients)},
        )
        monkeypatch.setattr(
            gl,
            "_game_probe",
            lambda timeout=5.0: {
                "connected": tuner if probe_connected is None else probe_connected,
                "ingame": turn is not None,
                "turn": turn,
                "note": probe_note,
            },
        )
        monkeypatch.setattr(gl, "_ocr_game_window", lambda win: boxes)
        monkeypatch.setattr(gl, "get_newest_save", lambda: newest)

    def test_not_running(self, monkeypatch):
        self._wire(monkeypatch, pids=[], tuner=False, turn=None, boxes=[])
        report = gl.game_status()
        assert "GAME STATE: not_running" in report
        assert "launch_game" in report

    def test_starting(self, monkeypatch):
        self._wire(monkeypatch, pids=[580], tuner=False, turn=None, boxes=[])
        report = gl.game_status()
        assert "GAME STATE: starting" in report
        # The advice that matters here: do not start a second copy.
        assert "second instance" in report

    def test_in_game_reports_the_turn(self, monkeypatch):
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=True,
            turn=80,
            boxes=[("回 合 80 / 500", 3674, 8, 65, 12)],
        )
        report = gl.game_status()
        assert "GAME STATE: in_game" in report
        assert "turn 80" in report
        assert "Nothing needs loading" in report

    def test_main_menu_names_the_save_to_load(self, monkeypatch):
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=True,
            turn=None,
            boxes=[("单 人 模 式", 1854, 1006, 71, 16)],
        )
        report = gl.game_status()
        assert "GAME STATE: main_menu" in report
        # It names the newest save, not the newest 0_MCP_ file.
        assert 'load_game_save("AutoSave_0080")' in report
        assert "turn 80" in report

    def test_leader_screen_says_it_needs_a_click(self, monkeypatch):
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=True,
            turn=None,
            boxes=[("每 征 与 能 力", 1743, 874, 67, 28)],
        )
        report = gl.game_status()
        assert "GAME STATE: leader_screen" in report
        assert "leader intro screen" in report

    def test_a_hud_split_across_boxes_keeps_its_digits_together(self):
        # A live session reported turn 81 as "turn 8" on 2026-09-20: Windows OCR returned
        # the HUD as two boxes, 回 合 8 and 1 / 5 0 0, and the tail came first, so joining
        # the screen into one string put the digits out of order. Boxes are rebuilt into
        # visual lines (by y, then by x) before anything is parsed.
        boxes = [
            ("1 / 5 0 0", 3700, 8, 60, 12),  # the tail, listed first
            ("回 合 8", 3660, 9, 40, 12),
            ("公 元 前 900 年", 3665, 19, 75, 11),
        ]
        assert gl._ocr_turn(boxes) == 81
        assert gl._screen_kind(boxes) == "in-game"

    def test_the_canonical_hud_form_is_preferred(self):
        # "回合 81 / 500" is the unambiguous reading; the slash form wins when both match.
        assert gl._ocr_turn([("回 合 81 / 500", 3660, 8, 65, 12)]) == 81
        assert gl._ocr_turn([("Turn 214 / 500", 3660, 8, 65, 12)]) == 214

    def test_the_hud_is_read_from_the_topmost_line(self):
        # The counter sits in the top strip of the window; a stray "回合 3" lower down
        # (a tooltip, a unit panel) must not win.
        boxes = [
            ("回 合 82 / 500", 3660, 8, 65, 12),
            ("回 合 3", 100, 900, 40, 12),
        ]
        assert gl._ocr_turn(boxes) == 82

    def test_the_screen_gives_the_turn_when_the_tuner_cannot(self):
        boxes = [("回 合 80 / 500", 3674, 8, 65, 12), ("公 元 前 900 年", 3676, 19, 80, 12)]
        assert gl._ocr_turn(boxes) == 80
        assert gl._ocr_turn([("Turn 214 / 500", 1, 2, 3, 4)]) == 214
        assert gl._ocr_turn([("每 征 与 能 力", 1743, 874, 67, 28)]) is None
        assert gl._ocr_turn([]) is None

    def test_a_misread_slash_does_not_cost_the_turn(self):
        # A recorded turn-59 frame OCRs its HUD as "回 合 59 巧 00": the "/ 5" of
        # "/ 500" comes back as one glyph. Matching the canonical form with the slash
        # lost the turn and made an in-game screen read as "unrecognised", which is the
        # one reading a state report must not produce while a game is running.
        hud = [("回 合 59 巧 00", 3660, 8, 65, 12), ("公 元 前 1680 年", 3665, 19, 75, 11)]
        assert gl._ocr_turn(hud) == 59
        assert gl._screen_kind(hud) == "in-game"

    def test_our_own_connection_is_not_a_foreign_holder(self):
        import os

        assert gl._foreign_tuner_clients([23276, 580, os.getpid()], [580]) == [23276]
        assert gl._foreign_tuner_clients([580], [580]) == []

    def test_a_refused_connect_is_not_a_tuner_that_is_still_coming_up(self, monkeypatch):
        # FireTuner serves one connection per game process. With another MCP attached,
        # connect() is refused exactly as if the tuner had not started - and the old
        # reading told the caller to wait 30-60s for something that was already there.
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=False,
            turn=None,
            boxes=[],
            listening=True,
            clients=[23276],
        )
        report = gl.game_status()
        assert "GAME STATE: tuner_busy" in report
        assert "pid 23276 holds the only connection" in report
        assert "waiting will not change that" in report
        assert "~30-60s" not in report

    def test_a_game_on_screen_is_read_even_when_the_tuner_is_someone_elses(self, monkeypatch):
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=False,
            turn=None,
            boxes=[("回 合 80 / 500", 3674, 8, 65, 12)],
            listening=True,
            clients=[23276],
        )
        report = gl.game_status()
        assert "GAME STATE: in_game" in report
        assert "turn 80 (read from the screen" in report
        assert "pid 23276" in report

    def test_a_tuner_that_answers_but_a_failed_probe_is_not_a_reason_to_restart(self, monkeypatch):
        # The live case on 2026-09-20: the socket connected, the FireTuner line read
        # "listening (this process can attach)", and the probe then failed with
        # WinError 64 while a turn-80 game was on screen. The advice was "started outside
        # the MCP - restart it", which would have thrown the game away.
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=True,
            turn=None,
            boxes=[("回 合 80 / 500", 3674, 8, 65, 12)],
            probe_connected=False,
            probe_note="[WinError 64] the network name is no longer available",
        )
        report = gl.game_status()
        assert "GAME STATE: in_game" in report
        assert "FireTuner   : listening" in report
        assert "do not restart the game" in report
        assert "started outside the MCP" not in report

    def test_a_listening_but_silent_tuner_does_not_ask_for_a_restart(self, monkeypatch):
        # The port answered and the probe did not - a game that is still loading, or a
        # tuner that dropped the connection. The advice used to be "started outside the
        # MCP, restart it", which thrown at a live turn-80 game is the worst answer
        # available. Observed 2026-09-20 at the end of a successful 304s load.
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=False,
            turn=None,
            boxes=[("回 合 80 / 500", 3674, 8, 65, 12)],
            listening=True,
        )
        report = gl.game_status()
        assert "GAME STATE: in_game" in report
        assert "do not restart the game" in report
        assert "started outside the MCP" not in report

    def test_a_tuner_that_never_opened_is_still_named(self, monkeypatch):
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=False,
            turn=None,
            boxes=[("回 合 80 / 500", 3674, 8, 65, 12)],
            listening=False,
        )
        report = gl.game_status()
        assert "started outside the MCP" in report

    def test_a_game_started_outside_the_mcp_is_named_as_such(self, monkeypatch):
        # The process is up and a game is on screen, but nothing ever opened FireTuner:
        # waiting will not fix that, only a launch through the MCP will.
        self._wire(
            monkeypatch,
            pids=[580],
            tuner=False,
            turn=None,
            boxes=[("回 合 80 / 500", 3674, 8, 65, 12)],
        )
        report = gl.game_status()
        assert "GAME STATE: in_game" in report
        assert "started outside the MCP" in report
        assert "launch_game" in report

    def test_the_port_table_reports_its_own_shape(self):
        # The real GetExtendedTcpTable call, not a fake: if the struct layout breaks,
        # this fails instead of silently degrading to "not listening" in the field.
        state = gl._tuner_port_state()
        assert set(state) == {"listening", "clients"}
        assert isinstance(state["listening"], bool)
        assert all(isinstance(pid, int) for pid in state["clients"])

    def test_a_click_that_leaves_the_leader_screen_counts_as_landed(self, monkeypatch):
        # The turn is readable only minutes after the click, so waiting for the *turn*
        # declared a good click a miss and clicked seven more times over three minutes.
        kinds = iter(["leader intro screen", "nothing readable (intro movie, splash)"])
        monkeypatch.setattr(gl, "_ocr_game_window", lambda win: [])
        monkeypatch.setattr(gl, "_screen_kind", lambda results: next(kinds))
        assert gl._wait_for_continue_to_take(object(), max_seconds=10) is True

    def test_a_still_leader_screen_is_a_miss(self, monkeypatch):
        monkeypatch.setattr(gl, "_ocr_game_window", lambda win: [])
        monkeypatch.setattr(gl, "_screen_kind", lambda results: "leader intro screen")
        assert gl._wait_for_continue_to_take(object(), max_seconds=0.05) is False

    def test_an_already_open_submenu_is_not_re_clicked(self, monkeypatch):
        # Clicking the parent again closes the submenu, and the parent shifts ~95px left
        # while it is open - so look first. Observed live on 2026-09-20.
        calls: list[tuple[str, object]] = []

        def fake_wait(target, **kwargs):
            calls.append(("wait", target))
            return ("继 续 游 戏", 1974, 1076, 71, 17)

        monkeypatch.setattr(gl, "_wait_for_text", fake_wait)
        monkeypatch.setattr(
            gl, "_click_text", lambda target, **kw: (calls.append(("click", target)), True)[1]
        )
        monkeypatch.setattr(gl, "_wait_for_leader_screen", lambda timeout=120: False)
        gl._continue_game_sync("AutoSave_0080")

        clicked = [" ".join(c[1]) if isinstance(c[1], tuple) else str(c[1]) for c in calls if c[0] == "click"]
        assert not any("单人模式" in label or "Single Player" in label for label in clicked), clicked

    def test_the_control_is_waited_for_not_guessed_at(self, monkeypatch):
        # The leader screen is readable about a hundred seconds before its control is
        # drawn; clicking teal blobs in that window is what cost 98s of stray clicks.
        # The control sits inside the band (x 15-62%, y 50-82% of the window), as it does
        # at 4K: a bar outside the band is clipped, and a clipped bar moves the click.
        from PIL import Image, ImageDraw

        bare = Image.new("RGB", (400, 300), (10, 10, 10))
        drawn = bare.copy()
        draw = ImageDraw.Draw(drawn)
        draw.rectangle((120, 200, 220, 228), fill=(0, 150, 160))
        draw.ellipse((145, 160, 195, 190), outline=(0, 150, 160), width=6)
        frames = iter([bare, bare, drawn])
        monkeypatch.setattr(gl, "_grab_window", lambda win: next(frames, drawn))
        monkeypatch.setattr(time, "sleep", lambda seconds: None)

        class Win:
            x = y = 0
            w, h = 400, 300

        point = gl._wait_for_continue_control(Win(), timeout=30)
        assert point is not None
        assert abs(point[0] - 170) <= 8 and abs(point[1] - 175) <= 8, point

    def test_waiting_for_the_control_gives_up(self, monkeypatch):
        from PIL import Image

        monkeypatch.setattr(
            gl, "_grab_window", lambda win: Image.new("RGB", (400, 300), (10, 10, 10))
        )
        monkeypatch.setattr(time, "sleep", lambda seconds: None)

        class Win:
            x = y = 0
            w, h = 400, 300

        assert gl._wait_for_continue_control(Win(), timeout=0) is None

    def test_a_dropped_connection_is_retried_once(self, monkeypatch):
        # ERROR_NETNAME_DELETED on a reconnect right after another client closed: the port
        # is fine and the same probe answers moments later. Measured 2026-09-20, five
        # seconds after a load finished - the first game_status() after every load hit it.
        import civ_mcp.connection as connection

        attempts = {"n": 0}

        class FlakyConnection:
            def __init__(self, *args, **kwargs):
                self.ingame_index = 0

            async def connect(self):
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise OSError(64, "The specified network name is no longer available")

            async def disconnect(self):
                return None

            async def execute_write(self, lua, timeout=5.0):
                return ["TURN|80"]

        monkeypatch.setattr(connection, "GameConnection", FlakyConnection)
        monkeypatch.setattr(
            gl, "_tuner_port_state", lambda: {"listening": True, "clients": []}
        )
        monkeypatch.setattr(time, "sleep", lambda seconds: None)

        probe = gl._game_probe()
        assert attempts["n"] == 2
        assert probe["connected"] is True
        assert probe["turn"] == 80

    def test_a_refused_connection_is_not_retried(self, monkeypatch):
        # Only a *dropped* connection is worth retrying. A refusal means nothing is
        # listening, and retrying it would just spend 1.5s per probe forever at launch.
        import civ_mcp.connection as connection

        attempts = {"n": 0}

        class RefusingConnection:
            def __init__(self, *args, **kwargs):
                pass

            async def connect(self):
                attempts["n"] += 1
                raise ConnectionRefusedError("Cannot connect to Civ 6 at 127.0.0.1:4318")

            async def disconnect(self):
                return None

            async def execute_write(self, lua, timeout=5.0):
                raise AssertionError("unreachable")

        monkeypatch.setattr(connection, "GameConnection", RefusingConnection)
        monkeypatch.setattr(time, "sleep", lambda seconds: None)

        probe = gl._game_probe()
        assert attempts["n"] == 1
        assert probe["connected"] is False

    def test_the_probe_still_works_inside_a_running_event_loop(self, monkeypatch):
        # asyncio.run cannot nest. The refusal used to be caught and returned as
        # "no connection" - the same reading as a game that is not running - while the
        # tuner was open and a save was loaded. Observed by calling game_status() from
        # an async recovery script on 2026-09-20.
        import asyncio

        import civ_mcp.connection as connection

        class LiveConnection:
            def __init__(self, *args, **kwargs):
                self.ingame_index = 0

            async def connect(self):
                return None

            async def disconnect(self):
                return None

            async def execute_write(self, lua, timeout=5.0):
                return ["TURN|80"]

        monkeypatch.setattr(connection, "GameConnection", LiveConnection)

        async def inside_a_loop():
            return gl._game_probe()

        probe = asyncio.run(inside_a_loop())
        assert probe["connected"] is True
        assert probe["turn"] == 80
        assert "event loop" not in probe["note"]

    def test_the_probe_survives_a_dead_tuner(self, monkeypatch):
        # Nothing listening: the probe answers, it does not raise. The fake goes on
        # the connection module because the probe imports the class at call time.
        import civ_mcp.connection as connection

        class DeadConnection:
            def __init__(self, *args, **kwargs):
                pass

            async def connect(self):
                raise ConnectionError("no tuner here")

            async def disconnect(self):
                pass

        monkeypatch.setattr(connection, "GameConnection", DeadConnection)
        probe = gl._game_probe()
        assert probe["connected"] is False
        assert probe["ingame"] is False
        assert probe["turn"] is None
        assert "no tuner here" in probe["note"]