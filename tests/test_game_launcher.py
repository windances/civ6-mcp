"""The re-focus retry must reach `SetForegroundWindow`, and must not fail quietly.

Measured on this match at T352: four `HANG:352:0_MCP_0352` results while
`.civ6-mcp-data/hang_diagnosis.jsonl` recorded `"foreground": false`. `_bring_to_front_win32` asked
`user32.GetCurrentThreadId()`, which that DLL does not export, so the call raised `AttributeError`,
the `except Exception` below swallowed it, and the function returned before
`win32gui.SetForegroundWindow` - for the entire life of the retry. These tests hold both halves of
that: the thread id comes from `kernel32`, and a failure leaves a warning behind instead of nothing.
"""

from __future__ import annotations

import logging
import sys
import types

import pytest

from civ_mcp import game_launcher

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="the Win32 re-focus path")

FOREGROUND_THREAD = 1234
OUR_THREAD = 5678


class _Win32:
    """A `ctypes.windll` + `win32gui` stand-in that records calls and mirrors the real exports.

    `user32.GetCurrentThreadId` raises `AttributeError` exactly the way the real DLL does, so a
    regression to the old spelling fails here rather than in a live session.
    """

    MISSING = {("user32", "GetCurrentThreadId")}
    VALUES = {
        "user32.GetWindowThreadProcessId": FOREGROUND_THREAD,
        "kernel32.GetCurrentThreadId": OUR_THREAD,
        # The real AttachThreadInput answers non-zero on success, and the code uses that answer to
        # decide whether the detach below is owed.
        "user32.AttachThreadInput": 1,
    }

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []
        self.gui: list[tuple[str, tuple]] = []
        self.raises: dict[str, Exception] = {}

    # --- ctypes.windll -------------------------------------------------------------
    def _module(self, module: str):
        recorder = self

        class _DLL:
            def __getattr__(self, name: str):
                if (module, name) in recorder.MISSING:
                    raise AttributeError(f"module '{module}' has no attribute '{name}'")
                recorded = f"{module}.{name}"

                def call(*args):
                    recorder.calls.append((recorded, args))
                    if recorded in recorder.raises:
                        raise recorder.raises[recorded]
                    return recorder.VALUES.get(recorded, 0)

                return call

        return _DLL()

    def windll(self) -> object:
        return types.SimpleNamespace(__getattr__=self._module)


class _Windll:
    def __init__(self, recorder: _Win32) -> None:
        self._recorder = recorder

    def __getattr__(self, module: str):
        return self._recorder._module(module)


class _Ctypes:
    """`ctypes` with only the attribute this function uses."""

    def __init__(self, recorder: _Win32) -> None:
        self.windll = _Windll(recorder)


def _install(monkeypatch) -> _Win32:
    """Patch ctypes, win32gui and the window lookup; return the recorder."""
    recorder = _Win32()
    fake_ctypes = _Ctypes(recorder)

    class _FakeGui:
        @staticmethod
        def IsIconic(hwnd):
            recorder.gui.append(("IsIconic", (hwnd,)))
            return 0

        @staticmethod
        def ShowWindow(hwnd, cmd):
            recorder.gui.append(("ShowWindow", (hwnd, cmd)))

        @staticmethod
        def SetForegroundWindow(hwnd):
            recorder.gui.append(("SetForegroundWindow", (hwnd,)))
            return 1

    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)
    monkeypatch.setitem(sys.modules, "win32gui", _FakeGui)
    monkeypatch.setattr(game_launcher, "_find_game_window_win32", lambda: _FakeWindow())
    return recorder


class _FakeWindow:
    window_id = 4242


class TestTheThreadId:
    def test_it_comes_from_kernel32_and_the_window_is_raised(self, monkeypatch):
        recorder = _install(monkeypatch)

        game_launcher._bring_to_front_win32()

        asked = [name for name, _ in recorder.calls]
        assert "kernel32.GetCurrentThreadId" in asked, asked
        assert not any(name == "user32.GetCurrentThreadId" for name in asked), (
            "user32 does not export GetCurrentThreadId; asking it raises AttributeError, and the "
            "except below then throws the whole retry away"
        )
        assert [name for name, _ in recorder.gui] == ["IsIconic", "SetForegroundWindow"], recorder.gui

    def test_the_thread_attach_is_taken_and_released(self, monkeypatch):
        recorder = _install(monkeypatch)

        game_launcher._bring_to_front_win32()

        attaches = [args[-1] for name, args in recorder.calls if name == "user32.AttachThreadInput"]
        assert attaches == [True, False], (
            "a different foreground thread needs the attach, and leaving it attached would keep the "
            f"input queues joined: {attaches}"
        )


class TestAFailureIsVisible:
    def test_a_refused_re_focus_is_logged_not_swallowed(self, monkeypatch, caplog):
        recorder = _install(monkeypatch)
        recorder.raises["user32.AttachThreadInput"] = RuntimeError("AttachThreadInput refused")

        with caplog.at_level(logging.WARNING, logger=game_launcher.log.name):
            game_launcher._bring_to_front_win32()  # non-fatal, so it must not raise

        assert any("AttachThreadInput refused" in message for message in caplog.messages), (
            "the bare swallow is what hid the user32 bug; the failure has to be readable now"
        )
