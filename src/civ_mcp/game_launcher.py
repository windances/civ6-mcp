"""Game lifecycle management — kill, launch, and load saves via OCR.

Safety guardrails for automated agents:
- Only kills Civ 6 processes (hardcoded process names)
- Only launches Civ 6 via Steam (hardcoded app ID 289070)
- Only loads saves from the known autosave directory
- No config file modifications, no arbitrary system commands
- All process/file interactions are scoped to Civ 6 only

Platform support:
- macOS: fully supported (process mgmt, OCR, window automation)
  Install with: uv pip install 'civ6-mcp[launcher-macos]'
- Windows: fully supported (process mgmt, OCR, window automation)
  Install with: uv pip install 'civ6-mcp[launcher-windows]'
- Linux: fully supported (process mgmt, OCR, window automation)
  Install with: uv pip install 'civ6-mcp[launcher-linux]'
  System deps: sudo apt install xdotool tesseract-ocr
"""

from __future__ import annotations

import asyncio
import glob
import json
import logging
import os
import re
import socket
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

log = logging.getLogger(__name__)

# Enable per-monitor DPI awareness on Windows so we get true pixel
# coordinates and window dimensions (not DPI-virtualized values).
if sys.platform == "win32":
    try:
        import ctypes as _ctypes

        _ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        pass  # Older Windows or already set


class WindowInfo(NamedTuple):
    """Game window metadata (Quartz on macOS, win32gui on Windows, xdotool on Linux)."""

    window_id: int  # CGWindowNumber on macOS, HWND on Windows, XID on Linux
    x: int  # screen points
    y: int  # screen points
    w: int  # screen points
    h: int  # screen points
    pid: int


# ---------------------------------------------------------------------------
# Constants — hardcoded for safety (not configurable by agents)
# ---------------------------------------------------------------------------

STEAM_APP_ID = "289070"
_ALLOWED_PROCESS_PATTERNS = ("Civ6",)  # pkill -f pattern — only matches Civ 6
# CGWindowList/AppKit report app name ("Civilization VI"), not binary name ("Civ6_Exe")
_APP_NAME_PATTERNS = ("Civilization",)


def _windows_documents_dir() -> str | None:
    """Return the real Documents folder on Windows, or None.

    ``~/Documents`` is only a guess: Documents can be relocated anywhere, and
    OneDrive redirection is common — on such a machine the shell reports
    ``.../OneDrive/<localised>`` while ``~/Documents`` may not even exist. Civ 6
    writes saves to whatever the shell reports, so ask the shell rather than
    assume, and let the caller fall back to the guess.
    """
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        # CSIDL_PERSONAL = 0x0005, SHGFP_TYPE_CURRENT = 0
        if ctypes.windll.shell32.SHGetFolderPathW(None, 0x0005, None, 0, buf) == 0:
            candidate = buf.value
            if candidate and os.path.isdir(candidate):
                return candidate
    except Exception:
        pass
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "Personal")
        value = os.path.expandvars(value)
        if value and os.path.isdir(value):
            return value
    except Exception:
        pass
    return None


if sys.platform == "darwin":
    _PROCESS_NAMES = ("Civ6_Exe_Child", "Civ6_Exe", "Civ6")
    _SAVE_BASE = os.path.expanduser(
        "~/Library/Application Support/Sid Meier's Civilization VI/"
        "Sid Meier's Civilization VI/Saves/Single"
    )
    SAVE_DIR = os.path.join(_SAVE_BASE, "auto")  # autosaves
    SINGLE_SAVE_DIR = _SAVE_BASE  # regular saves (including benchmark)
elif sys.platform == "win32":
    _PROCESS_NAMES = (
        "CivilizationVI_DX12.exe",
        "CivilizationVI.exe",
        "Civ6_Exe_Child.exe",
        "Civ6_Exe.exe",
    )
    # Ask the shell where Documents actually is; fall back to the common guess.
    _documents = _windows_documents_dir() or os.path.expanduser("~/Documents")
    _SAVE_BASE = os.path.join(
        _documents, "My Games", "Sid Meier's Civilization VI", "Saves", "Single"
    )
    SAVE_DIR = os.path.join(_SAVE_BASE, "auto")
    SINGLE_SAVE_DIR = _SAVE_BASE
elif sys.platform == "linux":
    _PROCESS_NAMES = ("Civ6", "Civ6Sub")
    _SAVE_BASE = os.path.expanduser(
        "~/.local/share/aspyr-media/Sid Meier's Civilization VI/Saves/Single"
    )
    SAVE_DIR = os.path.join(_SAVE_BASE, "auto")
    SINGLE_SAVE_DIR = _SAVE_BASE
else:
    _PROCESS_NAMES = ()
    SAVE_DIR = ""
    SINGLE_SAVE_DIR = ""

# How long to wait after kill for Steam to deregister the game
_KILL_SETTLE_SECONDS = 10
# How long to wait for game process to appear after launch
_LAUNCH_TIMEOUT_SECONDS = 60
# How long to wait for FireTuner port to open after game process starts
_PORT_POLL_TIMEOUT = 180
# Tuner TCP port
_TUNER_PORT = 4318


def _require_gui_deps() -> None:
    """Validate GUI dependencies are available, raising clear error if missing."""
    if sys.platform == "win32":
        try:
            import win32gui  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "Game launcher requires pywin32. Install with: uv pip install pywin32"
            )
        try:
            from winrt.windows.media.ocr import OcrEngine  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "Game launcher requires Windows OCR support. "
                "Install with: uv pip install 'civ6-mcp[launcher-windows]'"
            )
        return
    if sys.platform == "linux":
        import shutil

        missing = []
        if shutil.which("xdotool") is None:
            missing.append("xdotool (sudo apt install xdotool)")
        try:
            import mss  # noqa: F401
        except ImportError:
            missing.append("python-mss (uv pip install 'civ6-mcp[launcher-linux]')")
        try:
            import pytesseract  # noqa: F401
        except ImportError:
            missing.append("pytesseract (uv pip install 'civ6-mcp[launcher-linux]')")
        if shutil.which("tesseract") is None:
            missing.append("tesseract-ocr (sudo apt install tesseract-ocr)")
        if missing:
            raise RuntimeError("Game launcher GUI requires: " + ", ".join(missing))
        return
    if sys.platform != "darwin":
        raise NotImplementedError(f"GUI automation not supported on {sys.platform}")
    try:
        import Quartz  # noqa: F401
        import Vision  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Game launcher requires pyobjc GUI dependencies. "
            "Install with: uv pip install 'civ6-mcp[launcher-macos]'"
        )


# ---------------------------------------------------------------------------
# Process management (no GUI deps needed)
# ---------------------------------------------------------------------------


def _running_game_pids_win32() -> list[int]:
    """PIDs of the game process on Windows, without spawning anything.

    Uses the toolhelp snapshot rather than `tasklist`: tasklist is a child process read
    through a pipe, and where pipe-spawning is blocked it returns nothing at all, so
    the game reads as stopped while it is running. That happened on 2026-09-20 -
    ``is_game_running()`` answered "Game not running" for a live game (pid 580), and
    the load flow then spent a minute trying to launch a second one.
    """
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    TH32CS_SNAPPROCESS = 0x00000002
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snapshot or snapshot == ctypes.c_void_p(-1).value:
        return []

    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    wanted = {name.lower() for name in _PROCESS_NAMES}
    pids: list[int] = []
    try:
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return []
        while True:
            if entry.szExeFile.lower() in wanted:
                pids.append(int(entry.th32ProcessID))
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(snapshot))
    return pids


def _running_game_pids() -> list[int]:
    """PIDs of any running Civ 6 process."""
    if sys.platform == "win32":
        return _running_game_pids_win32()
    result = subprocess.run(  # noqa: S603 - fixed pgrep pattern, hardcoded
        ["pgrep", "-f", _ALLOWED_PROCESS_PATTERNS[0]],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [int(line) for line in result.stdout.split() if line.strip().isdigit()]


def is_game_running() -> bool:
    """Check if Civ 6 is running."""
    return bool(_running_game_pids())


def _dismiss_crash_dialog() -> bool:
    """Dismiss macOS crash report dialog if present.

    Returns True if a dialog was dismissed, False if none found.
    """
    if sys.platform != "darwin":
        return False
    try:
        # The crash dialog is owned by UserNotificationCenter with an empty
        # window name.  Buttons are "Reopen", "Report...", "Ignore".
        # Click "Ignore" to dismiss without relaunching the crashed app.
        script = (
            'tell application "System Events"\n'
            "    set found to false\n"
            '    tell process "UserNotificationCenter"\n'
            "        repeat with win in every window\n"
            "            try\n"
            '                click button "Ignore" of win\n'
            "                set found to true\n"
            "            end try\n"
            "        end repeat\n"
            "    end tell\n"
            "    return found\n"
            "end tell"
        )
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        dismissed = r.stdout.strip() == "true"
        if dismissed:
            log.info("Dismissed macOS crash report dialog")
        return dismissed
    except Exception as e:
        log.debug("Crash dialog check failed: %s", e)
        return False


# A heartbeat younger than this means a session was playing moments ago.
_ACTIVE_HEARTBEAT_SECONDS = 120


def _heartbeat_candidates() -> list[Path]:
    """Where a running MCP server may have written its heartbeat.

    The data directory is configurable (``CIV_MCP_DATA_DIR``) and the launcher is often
    run out of a project that keeps it beside the code, so more than one path has to be
    considered - a heartbeat that is not looked for is a session that gets killed.
    """
    candidates = [Path.home() / ".civ6-mcp" / "heartbeat.json"]
    data_dir = os.environ.get("CIV_MCP_DATA_DIR")
    if data_dir:
        candidates.insert(0, Path(data_dir) / "heartbeat.json")
    candidates.append(Path.cwd() / ".civ6-mcp-data" / "heartbeat.json")
    return candidates


def _other_active_session() -> str | None:
    """Describe another session that is playing this game right now, if there is one.

    Killing the game is not a neutral diagnostic: on 2026-09-20 a test run called
    ``kill_game`` while a live session was mid-turn-82 (that session's log shows a
    ``get_units`` eight seconds before the kill), and it threw the position away. Two
    independent signals say someone else is playing, and neither needs the other: the
    FireTuner connection (only one client can hold it) and the heartbeat file the MCP
    server writes while it plays.
    """
    own = os.getpid()
    clients = [pid for pid in _tuner_port_state().get("clients", []) if pid != own]
    if clients:
        return f"pid {', '.join(str(pid) for pid in clients)} holds the FireTuner connection"

    for path in _heartbeat_candidates():
        try:
            beat = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - a missing or unreadable file is not a session
            continue
        pid = int(beat.get("pid") or 0)
        age = time.time() - float(beat.get("ts") or 0)
        if pid != own and beat.get("phase") == "playing" and age < _ACTIVE_HEARTBEAT_SECONDS:
            return (
                f"pid {pid} wrote a 'playing' heartbeat {age:.0f}s ago "
                f"(turn {beat.get('turn')}, run {beat.get('run_id')})"
            )
    return None


def _kill_game_sync() -> str:
    """Kill Civ 6 and wait for Steam to deregister. Blocking."""
    if not is_game_running():
        return "Game is not running."

    if sys.platform in ("darwin", "linux"):
        # Kill only the game binary — NOT Steam or other processes.
        # Using -x (exact match) instead of -f (pattern) to avoid
        # killing Steam when its command line contains "Civ6".
        for proc_name in _PROCESS_NAMES:
            subprocess.run(["pkill", "-9", "-x", proc_name], capture_output=True)
    elif sys.platform == "win32":
        for name in _PROCESS_NAMES:
            subprocess.run(["taskkill", "/IM", name, "/F"], capture_output=True)
    else:
        raise NotImplementedError(f"kill not supported on {sys.platform}")
    log.info("Killed Civ 6, waiting %ds for Steam to deregister", _KILL_SETTLE_SECONDS)

    # Wait for process to actually die
    for _ in range(10):
        if not is_game_running():
            break
        time.sleep(1)

    # Extra wait for Steam to deregister
    time.sleep(_KILL_SETTLE_SECONDS)

    if is_game_running():
        return "WARNING: Game process may still be running after kill attempt."
    return "Game killed. Steam deregistration wait complete."


def _click_aspyr_launcher_sync() -> str | None:
    """Click PLAY on the Aspyr launcher if it appears (macOS only).

    On macOS, `steam://run/289070` opens the Aspyr LaunchPad — a splash
    screen with a PLAY button — before the actual game binary starts.
    This function detects that screen via OCR and clicks through it.

    Uses fullscreen OCR directly because the Aspyr launcher window
    cannot be captured via CGWindowListCreateImage (different process).

    Returns None on success, error string on failure.
    """
    if sys.platform != "darwin":
        return None  # no Aspyr launcher on other platforms

    try:
        _require_gui_deps()
    except (RuntimeError, NotImplementedError):
        log.warning("GUI deps not available — cannot auto-click Aspyr launcher")
        return "GUI deps not available. Click PLAY on the Aspyr launcher manually."

    log.info("Waiting for Aspyr launcher PLAY button...")
    start = time.time()
    while time.time() - start < 30:
        # Bring game window to front if it exists
        win = _find_game_window()
        if win:
            _bring_to_front(pid=win.pid)
            time.sleep(0.3)
        # Use fullscreen OCR — Aspyr launcher can't be window-captured
        results = _ocr_fullscreen()
        match = _find_text(results, "PLAY", exact=True)
        if match:
            text, x, y, w, h = match
            log.info("OCR: found '%s' at (%d,%d) — clicking", text, x, y)
            # The Aspyr launcher is a separate process from the game.
            # CGEventPost clicks require the target to be frontmost.
            # Click the mouse position directly — the launcher should
            # already be visible since we just OCR'd it on screen.
            _bring_to_front()
            time.sleep(0.3)
            _click(x, y)
            # Double-click in case the first was absorbed by the focus change
            time.sleep(0.5)
            _click(x, y)
            time.sleep(3)
            log.info("Clicked PLAY on Aspyr launcher")
            return None
        time.sleep(3)

    # Launcher may not appear if game was already past it
    log.info("Aspyr launcher PLAY button not found — may have been skipped")
    return None


def _wait_for_game_process(timeout: int = _LAUNCH_TIMEOUT_SECONDS) -> int | None:
    """Wait for the actual game process to appear. Returns seconds waited, or None."""
    for i in range(timeout):
        if is_game_running():
            log.info("Game process detected after %ds", i)
            return i
        time.sleep(1)
    return None


def _is_tuner_port_open() -> bool:
    """Check if the FireTuner port accepts TCP connections.

    "Accepts" is not the same as "is listening": FireTuner serves a single connection
    for the life of the game process, so once one MCP server is attached every later
    connect() is refused. Use ``_tuner_port_state`` to tell those two apart.
    """
    try:
        s = socket.create_connection(("127.0.0.1", _TUNER_PORT), timeout=2)
        s.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False


def _tuner_port_state() -> dict:
    """Who owns the FireTuner socket: the game's listener and its one client.

    A refused connect is ambiguous, and the two readings call for opposite actions:
    "the tuner has not started yet, wait" versus "the tuner is up and another process
    holds its only connection, waiting is useless". Measured 2026-09-20: an agent was
    playing a turn-80 game (its MCP server, pid 23276, held the connection) while a
    second process saw "not listening" and would have advised a 30-60s wait.

    Returns ``{"listening": bool, "clients": [pid, ...]}``. Off Windows, or if the
    table cannot be read, both come back empty and callers degrade to the socket probe.
    """
    state: dict = {"listening": False, "clients": []}
    if sys.platform != "win32":
        return state

    import ctypes
    from ctypes import wintypes

    class MIB_TCPROW_OWNER_PID(ctypes.Structure):
        _fields_ = [
            ("dwState", wintypes.DWORD),
            ("dwLocalAddr", wintypes.DWORD),
            ("dwLocalPort", wintypes.DWORD),
            ("dwRemoteAddr", wintypes.DWORD),
            ("dwRemotePort", wintypes.DWORD),
            ("dwOwningPid", wintypes.DWORD),
        ]

    TCP_TABLE_OWNER_PID_ALL = 5
    AF_INET = 2
    MIB_TCP_STATE_LISTEN = 2
    MIB_TCP_STATE_ESTAB = 5

    iphlpapi = ctypes.windll.iphlpapi
    size = wintypes.DWORD(0)
    # First call sizes the table and is expected to fail with ERROR_INSUFFICIENT_BUFFER.
    iphlpapi.GetExtendedTcpTable(None, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
    if not size.value:
        return state

    buffer = ctypes.create_string_buffer(size.value)
    ret = iphlpapi.GetExtendedTcpTable(
        buffer, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0
    )
    if ret != 0:
        return state

    count = ctypes.cast(buffer, ctypes.POINTER(wintypes.DWORD)).contents.value
    row_size = ctypes.sizeof(MIB_TCPROW_OWNER_PID)
    rows = ctypes.cast(
        ctypes.byref(buffer, ctypes.sizeof(wintypes.DWORD)),
        ctypes.POINTER(MIB_TCPROW_OWNER_PID * count),
    ).contents

    # Ports arrive in network byte order inside a DWORD, so take the low half and swap.
    for row in rows:
        local = socket.ntohs(row.dwLocalPort & 0xFFFF)
        remote = socket.ntohs(row.dwRemotePort & 0xFFFF)
        if local == _TUNER_PORT and row.dwState == MIB_TCP_STATE_LISTEN:
            state["listening"] = True
        elif local == _TUNER_PORT and row.dwState == MIB_TCP_STATE_ESTAB:
            # The game's side of an accepted connection also proves the listener is up.
            state["listening"] = True
        elif remote == _TUNER_PORT and row.dwState == MIB_TCP_STATE_ESTAB:
            pid = int(row.dwOwningPid)
            if pid not in state["clients"]:
                state["clients"].append(pid)
    return state


# --- the continue control: found by colour, verified by game state --------------
#
# The leader screen's continue control is a teal globe above a teal ribbon, and OCR
# does not read it: at 3840x2160 the whole leader screen yields two text boxes and
# neither is the button. Its position is not where the percentage grid below looks
# either - measured on 2026-09-20 the globe is at (1694,1374) = (44%, 64%) of the
# window, while the grid covers y 75-88%. That mismatch is why a load could sit on
# the leader screen for the whole poll and then be reported as successful.
#
# Clicking "the most teal thing in the band" is a second-order version of the same
# mistake: the control is a *shape* - a wide bar with the globe sitting on its centre -
# and only the globe takes the click. _continue_control_point reads that shape, and the
# area ranking is what is left when it cannot.

_TEAL_MIN_SATURATION = 8
_CONTINUE_BAND = (0.15, 0.50, 0.62, 0.82)  # x0, y0, x1, y1 as window fractions

# The leader screen's panel heading is "特征与能力"; Windows OCR reads the first
# character as 每 ("每征与能力"). Matching the whole string therefore fails on the one
# screen the load is supposed to end on, so match the tail that survives OCR.
_LEADER_SCREEN_SIGNATURE = "与能力"


def _leader_screen_detected(results: list[tuple[str, int, int, int, int]] | None) -> bool:
    """Is the game parked on the leader intro screen?

    Distinguishing this from the main menu is what lets the flow stop waiting and
    click, instead of timing out and then clicking positions that mean nothing.
    """
    for text, *_ in results or ():
        if _LEADER_SCREEN_SIGNATURE in text.replace(" ", ""):
            return True
    return False


def _wait_for_turn_number(max_seconds: float) -> int | None:
    """Poll until the game reports a turn, or give up.

    A readable turn is the only honest signal that a load finished; the FireTuner
    port answers at the main menu as well.
    """
    deadline = time.time() + max_seconds
    while time.time() < deadline:
        turn = _game_turn_number()
        if turn is not None:
            return turn
        time.sleep(3)
    return None


def _wait_for_game(max_seconds: float) -> bool:
    """Poll until the game reports a turn (i.e. a game is actually in progress)."""
    return _wait_for_turn_number(max_seconds) is not None


def _grab_window(win: "WindowInfo"):
    """The whole game window as an RGB image, straight off the screen."""
    from PIL import ImageGrab

    return ImageGrab.grab(
        bbox=(win.x, win.y, win.x + win.w, win.y + win.h), all_screens=True
    ).convert("RGB")


def _band_box(image, band: tuple[float, float, float, float] | None) -> tuple[int, int, int, int]:
    """``band`` (window fractions) as a pixel box inside ``image``."""
    if not band:
        return (0, 0, image.width, image.height)
    return (
        int(image.width * band[0]),
        int(image.height * band[1]),
        int(image.width * band[2]),
        int(image.height * band[3]),
    )


def _teal_mask(image):
    """The teal-pixel mask: green and blue both clearly above red, and neither dark.

    PIL mask arithmetic, not a per-pixel Python loop - the loop version touched 518k
    pixels per scan and is why a recovery that should take a minute ran for three.
    """
    from PIL import ImageChops

    red, green, blue = image.split()
    saturated = ImageChops.darker(
        ImageChops.subtract(green, red).point(
            lambda v: 255 if v > _TEAL_MIN_SATURATION else 0
        ),
        ImageChops.subtract(blue, red).point(
            lambda v: 255 if v > _TEAL_MIN_SATURATION else 0
        ),
    )
    lit = ImageChops.darker(
        green.point(lambda v: 255 if v > 60 else 0),
        blue.point(lambda v: 255 if v > 60 else 0),
    )
    return ImageChops.darker(saturated, lit)


def _continue_control_point(mask) -> tuple[int, int] | None:
    """The globe of the continue control, found by shape rather than by area.

    Measured on a recorded leader screen (1920x1080, 2026-09-20): the control is a solid
    teal bar 280px wide, and the ring-shaped globe ~70px across sits directly above the
    bar's centre - the globe x 1664-1736, y 260-330, the bar y 340-370. Only the globe
    responds to a click (observed live by the player: the label alone does nothing), so
    clicking "the middle of the teal blob" is not enough even when the blob is right.

    What this replaces is a ranking by teal area. Before the search was narrowed to the
    lower-left band, that ranking was dominated by the screen's background art and the
    flow clicked four wrong places; within the band it is unverified, because no
    recorded leader screen has been kept that shows the whole screen. What is verified
    is that this finder lands on the globe of the control it is aimed at, so it goes
    first and the ranking stays as the fallback.

    Returns a click point in ``mask`` coordinates, or None when no bar is on screen.
    """
    width, height = mask.size
    min_run = max(24, int(width * 0.05))  # a bar, not a texture

    bars: list[tuple[int, int, int]] = []
    for y in range(height):
        row = mask.crop((0, y, width, y + 1)).tobytes()
        longest = max((m.end() - m.start() for m in re.finditer(b"\xff+", row)), default=0)
        if longest >= min_run:
            runs = [(m.start(), m.end() - m.start()) for m in re.finditer(b"\xff+", row)]
            start, length = max(runs, key=lambda r: r[1])
            bars.append((y, start, length))
    if not bars:
        return None

    # Consecutive rows form one bar; the widest bar wins, and the tallest breaks ties.
    groups: list[list[tuple[int, int, int]]] = []
    for row in bars:
        if groups and row[0] == groups[-1][-1][0] + 1:
            groups[-1].append(row)
        else:
            groups.append([row])
    group = max(groups, key=lambda g: (max(r[2] for r in g), len(g)))

    top = group[0][0]
    bar_height = len(group)
    _, left, bar_width = max(group, key=lambda r: r[2])
    centre_x = left + bar_width // 2

    # The globe: whatever teal sits above the bar, in the column around the bar's centre.
    # The column matters - the bar's own soft top edge and neighbouring panels reach into
    # the band from the sides, and a bounding box over those reads as a globe 176px wide
    # against a 280px bar on the recorded frame. That misreading is also how a live run
    # clicked (1758,1446) on the ribbon instead of the globe at (1694,1374); the column
    # keeps the click over the bar's centre, where the globe actually sits.
    reach = max(6, bar_height * 3)
    above_top = max(0, top - reach)
    half = max(24, bar_width // 4)
    col_left, col_right = max(0, centre_x - half), min(width, centre_x + half)
    box = mask.crop((col_left, above_top, col_right, top)).getbbox()
    if box is not None:
        log.info(
            "Continue: %dpx bar, globe %dpx wide above its centre (click %d,%d)",
            bar_width,
            box[2] - box[0],
            col_left + (box[0] + box[2]) // 2,
            above_top + (box[1] + box[3]) // 2,
        )
        return (col_left + (box[0] + box[2]) // 2, above_top + (box[1] + box[3]) // 2)

    # No globe drawn (or it fell outside the crop): aim just above the bar's centre.
    return (centre_x, max(0, top - max(3, bar_height // 2)))


def _teal_candidates(
    win: "WindowInfo",
    band: tuple[float, float, float, float] | None,
    *,
    tiles: tuple[int, int] = (12, 8),
) -> list[tuple[int, int, int]]:
    """Teal blobs as (x, y, weight), biggest first.

    ``band`` keeps the search to the part of the window the control lives in. Without
    it the ranking is dominated by teal elsewhere on screen (background art), which is
    how a first attempt clicked four wrong places.

    This is the fallback for a control the shape finder cannot see; it answers "where is
    the most teal", which on the leader screen is not the continue control.
    """
    shot = _grab_window(win)
    x0, y0, x1, y1 = _band_box(shot, band)
    region = shot.crop((x0, y0, x1, y1))
    mask = _teal_mask(region)

    cols, rows = tiles
    found: list[tuple[int, int, int]] = []
    for ty in range(rows):
        for tx in range(cols):
            bx0, bx1 = region.width * tx // cols, region.width * (tx + 1) // cols
            by0, by1 = region.height * ty // rows, region.height * (ty + 1) // rows
            tile = mask.crop((bx0, by0, bx1, by1))
            box = tile.getbbox()
            if box is None:
                continue
            weight = tile.histogram()[255]
            found.append(
                (
                    win.x + x0 + bx0 + (box[0] + box[2]) // 2,
                    win.y + y0 + by0 + (box[1] + box[3]) // 2,
                    weight,
                )
            )
    found.sort(key=lambda item: item[2], reverse=True)
    return found


def _wait_for_continue_to_take(win: "WindowInfo", max_seconds: float = 30) -> bool:
    """Did the continue click take? The leader screen going away is the signal.

    Clicking continue starts a real load, and the screen leaves the leader screen long
    before the turn can be read. Measured 2026-09-20: the click landed, the screen
    changed within seconds, and the turn was readable only minutes later - so a check
    that waited 15s for the *turn* declared a good click a miss, then clicked seven more
    times over three minutes, each one a stray click on a loading game.
    """
    deadline = time.time() + max_seconds
    while time.time() < deadline:
        try:
            kind = _screen_kind(_ocr_game_window(win))
        except Exception as exc:  # noqa: BLE001 - a failed read is not a failed click
            log.debug("Continue: screen unreadable while checking the click (%s)", exc)
            kind = ""
        if kind and kind != "leader intro screen":
            log.info("Continue: the leader screen is gone (%s) - the click took", kind)
            return True
        time.sleep(2)
    return False


def _wait_for_continue_control(
    win: "WindowInfo", timeout: float = 120
) -> tuple[int, int] | None:
    """Wait for the continue control to be drawn, then return its click point.

    The leader screen becomes *readable* well before its control exists. Measured
    2026-09-20 during a relaunch and load: at the moment the leader screen was detected
    the entire screen carried 715 teal samples and no bar at all, and once the bar and
    globe were there it was 7639 - about a hundred seconds later. The flow spent that
    time clicking teal blobs anywhere but the control, so waiting for it is both
    shorter and safer than guessing at it.
    """
    deadline = time.time() + timeout
    while True:
        shot = _grab_window(win)
        bx0, by0, _, _ = _band_box(shot, _CONTINUE_BAND)
        point = _continue_control_point(
            _teal_mask(shot.crop(_band_box(shot, _CONTINUE_BAND)))
        )
        if point is not None:
            return (bx0 + point[0], by0 + point[1])
        if time.time() >= deadline:
            return None
        time.sleep(2)


def _click_continue_by_colour(max_candidates: int = 4) -> bool:
    """Click the continue control, stopping once a game is readable.

    The shape finder goes first because it aims at the one part of the control that
    responds - the globe above the bar. Only if it finds nothing does the flow fall
    back to clicking teal blobs by area, one at a time: clicking nine assumed positions
    in a row is how a stray click ends up inside a game that was already running, so a
    wrong guess costs one click, not eight.
    """
    win = _find_game_window()
    if win is None:
        log.warning("Continue by colour: no game window found")
        return False

    # Nothing to click if a game is already running. This is reachable from the
    # OCR-timeout fallbacks below, which assume the leader screen without having
    # confirmed it - and a click on the map is a move order when a unit is selected.
    try:
        if _screen_kind(_ocr_game_window(win)) == "in-game":
            log.info("Continue: a game is already in progress; not clicking")
            return True
    except Exception as exc:  # noqa: BLE001 - a failed screen read must not block the click
        log.debug("Continue: could not read the screen before clicking (%s)", exc)

    tried: set[tuple[int, int]] = set()

    point = _wait_for_continue_control(win)
    if point is not None:
        tried.add(point)
        log.info("Continue: globe above the ribbon at (%d,%d)", *point)
        _click(*point)
        if _wait_for_continue_to_take(win):
            return True
    else:
        log.info("Continue: no control drawn on the leader screen; ranking teal blobs")

    for band in (_CONTINUE_BAND, None):
        for x, y, count in _teal_candidates(win, band)[:max_candidates]:
            if (x, y) in tried:
                continue
            tried.add((x, y))
            log.info(
                "Continue: teal candidate (%d,%d) samples=%d band=%s", x, y, count, band
            )
            _click(x, y)
            if _wait_for_continue_to_take(win):
                return True
    return False


def _click_continue_positional() -> None:
    """Click the continue control on the leader screen.

    Found by colour first; the percentage grid below is only reached when no teal
    blob is on screen at all.
    """
    if _click_continue_by_colour():
        return

    _click_continue_grid()


def _click_continue_grid() -> None:
    """Click a grid of assumed continue-button positions.

    Kept as a last resort for a window where the control's colour has changed. It
    covers y 75-88% of the window, which is not where the control is at 4K (measured
    at (44%, 64%)), so it is not the first thing tried any more.

    On macOS, kCGWindowBounds includes the title bar + shadow, so we detect
    the content area offset the same way _ocr_game_window does (capture →
    measure → compare) to avoid clicking ~30px too high.
    """
    win = _find_game_window()
    if win is None:
        log.warning("Positional click: no game window found")
        return

    # Detect the content area offset to avoid clicking on decorations.
    # macOS: kCGWindowBounds includes title bar + shadow → measure via capture.
    # Linux: xdotool geometry may include decorations → use mss capture region.
    content_x = win.x
    content_y = win.y
    content_w = win.w
    content_h = win.h
    if sys.platform == "linux":
        try:
            _, capture_geo = _capture_window_linux(win.window_id)
            content_x = capture_geo["left"]
            content_y = capture_geo["top"]
            content_w = capture_geo["width"]
            content_h = capture_geo["height"]
        except Exception:
            log.debug("Positional click: could not get capture geometry")
    elif sys.platform == "darwin":
        try:
            import Quartz

            cg_image = _capture_window(win.window_id)
            img_px_w = Quartz.CGImageGetWidth(cg_image)
            img_px_h = Quartz.CGImageGetHeight(cg_image)
            if win.w and img_px_w and img_px_h:
                scale = img_px_w / win.w
                img_pt_h = img_px_h / scale
                gap = win.h - img_pt_h
                if gap > 5:
                    content_y = win.y + gap
                    content_h = int(img_pt_h)
        except Exception:
            log.debug("Positional click: could not detect title bar offset")

    # Try multiple positions — the button's relative position varies across
    # resolutions and window modes:
    #   4K fullscreen:    ~38%, 75%
    #   1080p fullscreen: ~35%, 82%
    #   1280x962 window:  ~32%, 77% (Linux windowed, empirically verified)
    #   1600x900 window:  ~15%, 88% (button shifts left on smaller windows)
    #   1280x973 window:  ~15-20%, 85-88%
    positions = [
        (0.32, 0.77),  # 1280x962 Linux windowed (verified on MAEVE)
        (0.15, 0.88),  # small windowed (left-aligned panel)
        (0.20, 0.86),  # small windowed (slight offset)
        (0.15, 0.85),  # small windowed (slightly higher)
        (0.25, 0.84),  # medium windowed
        (0.35, 0.82),  # 1080p fullscreen
        (0.38, 0.80),  # between 1080p and 4K
        (0.35, 0.78),  # 1080p variant
        (0.38, 0.75),  # 4K fullscreen
    ]

    # Log all positions upfront for debugging
    coords = [
        (content_x + int(content_w * px), content_y + int(content_h * py), px, py)
        for px, py in positions
    ]
    log.info(
        "Positional click grid [%d positions]: %s "
        "[window %dx%d at (%d,%d), content_y=%d content_h=%d]",
        len(coords),
        ", ".join(f"({x},{y})[{px:.0%},{py:.0%}]" for x, y, px, py in coords),
        win.w,
        win.h,
        win.x,
        win.y,
        content_y,
        content_h,
    )

    _bring_to_front()
    time.sleep(0.3)
    for i, (abs_x, abs_y, pct_x, pct_y) in enumerate(coords, 1):
        log.info(
            "Grid click [%d/%d] at (%d,%d) [%.0f%%,%.0f%%]",
            i,
            len(coords),
            abs_x,
            abs_y,
            pct_x * 100,
            pct_y * 100,
        )
        _click(abs_x, abs_y)
        time.sleep(0.5)


def _wait_for_tuner_port(timeout: int = _PORT_POLL_TIMEOUT) -> bool:
    """Poll TCP 4318 until it accepts connections.

    Returns True if port became reachable within timeout.
    """
    interval = 3

    for i in range(int(timeout / interval)):
        if _is_tuner_port_open():
            log.info("FireTuner port reachable after %ds", i * interval)
            return True

        if i % 10 == 0 and i > 0:
            log.info("Waiting for FireTuner port... %ds elapsed", i * interval)
        time.sleep(interval)

    return False


def _find_game_exe_win32() -> str | None:
    """Find the Civ 6 DX12 EXE via Steam library folders."""
    import re

    steam_dir = os.path.join(
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Steam"
    )
    vdf_path = os.path.join(steam_dir, "steamapps", "libraryfolders.vdf")

    if not os.path.exists(vdf_path):
        return None

    # Parse VDF to find library paths containing app 289070
    try:
        with open(vdf_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return None

    # Split into library blocks and find ones containing our app ID
    blocks = re.split(r'"\d+"\s*\{', content)
    for block in blocks:
        if f'"{STEAM_APP_ID}"' not in block:
            continue
        # Extract path from this block
        m = re.search(r'"path"\s+"([^"]+)"', block)
        if not m:
            continue
        lib_path = m.group(1).replace("\\\\", "\\")
        exe = os.path.join(
            lib_path,
            "steamapps",
            "common",
            "Sid Meier's Civilization VI",
            "Base",
            "Binaries",
            "Win64Steam",
            "CivilizationVI_DX12.exe",
        )
        if os.path.exists(exe):
            return exe

    # Fallback: check default location directly
    exe = os.path.join(
        steam_dir,
        "steamapps",
        "common",
        "Sid Meier's Civilization VI",
        "Base",
        "Binaries",
        "Win64Steam",
        "CivilizationVI_DX12.exe",
    )
    return exe if os.path.exists(exe) else None


def _launch_game_sync() -> str:
    """Launch Civ 6 and wait for the FireTuner port to open. Blocking.

    On macOS, Steam opens the Aspyr LaunchPad first (a splash screen
    with a PLAY button). This function auto-clicks through it if GUI
    deps are available.

    On Windows, falls back to direct EXE launch if steam://run fails.
    """
    # Dismiss any crash reporter dialogs blocking relaunch
    _dismiss_crash_dialogs_sync()

    if is_game_running():
        if _is_tuner_port_open():
            return "Game is already running and FireTuner port is open."
        # Process exists but port not open — wait for it
        log.info("Game process running but port not open yet, waiting...")
        if _wait_for_tuner_port():
            return "Game was starting up. FireTuner port is now open."
        # Stale process — kill it and launch fresh
        log.warning(
            "Game process running but tuner never opened — killing stale process"
        )
        _kill_game_sync()
        time.sleep(5)

    # Launch via Steam
    if sys.platform == "darwin":
        subprocess.run(["open", f"steam://run/{STEAM_APP_ID}"])
    elif sys.platform == "linux":
        # Use -applaunch (not steam:// URI) — the URI scheme is unreliable
        # when Steam is already running (silently ignored by some builds).
        subprocess.Popen(
            ["steam", "-applaunch", str(STEAM_APP_ID)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif sys.platform == "win32":
        os.startfile(f"steam://run/{STEAM_APP_ID}")  # noqa: S606 — hardcoded Steam URL
    else:
        raise NotImplementedError(f"launch not supported on {sys.platform}")
    log.info("Launched Civ 6 via Steam, waiting for process...")

    # macOS: click through the Aspyr launcher if it appears
    launcher_err = _click_aspyr_launcher_sync()
    if launcher_err:
        return f"WARNING: {launcher_err}"

    # Wait for actual game process (Linux/Proton can be slow to start)
    waited = _wait_for_game_process(timeout=60)
    if waited is None and sys.platform == "win32":
        # steam://run may have silently failed — try direct EXE launch
        exe_path = _find_game_exe_win32()
        if exe_path:
            log.info(
                "steam://run did not start game — launching EXE directly: %s", exe_path
            )
            subprocess.Popen([exe_path])  # noqa: S603 — hardcoded game path
            waited = _wait_for_game_process()

    if waited is None:
        return "WARNING: Game process not detected after launch. Check Steam."

    # Wait for FireTuner port to open (replaces blind sleep)
    log.info("Game process started after %ds, waiting for FireTuner port...", waited)
    if _wait_for_tuner_port():
        return (
            f"Game launched. Process started after {waited}s, FireTuner port is open."
        )

    return f"WARNING: Game launched (process after {waited}s) but FireTuner port did not open within {_PORT_POLL_TIMEOUT}s."


# ---------------------------------------------------------------------------
# OCR + GUI helpers (require pyobjc on macOS, winrt on Windows, xdotool on Linux)
# ---------------------------------------------------------------------------


def _find_game_window() -> WindowInfo | None:
    """Find the Civ 6 game window.

    Uses Quartz CGWindowList on macOS, win32gui on Windows, xdotool on Linux.
    Returns WindowInfo with window ID, bounds (screen points), and PID.
    Returns None if no matching window is found on screen.
    """
    if sys.platform == "win32":
        return _find_game_window_win32()
    if sys.platform == "linux":
        return _find_game_window_linux()
    _require_gui_deps()
    import Quartz

    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly
        | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    if not window_list:
        return None

    for w in window_list:
        owner = w.get("kCGWindowOwnerName", "")
        layer = w.get("kCGWindowLayer", -1)
        if layer != 0:
            continue
        if not (
            any(p in owner for p in _PROCESS_NAMES)
            or any(p in owner for p in _APP_NAME_PATTERNS)
        ):
            continue
        bounds = w.get("kCGWindowBounds", {})
        info = WindowInfo(
            window_id=w.get("kCGWindowNumber", 0),
            x=int(bounds.get("X", 0)),
            y=int(bounds.get("Y", 0)),
            w=int(bounds.get("Width", 0)),
            h=int(bounds.get("Height", 0)),
            pid=w.get("kCGWindowOwnerPID", 0),
        )
        log.info(
            "Window found: wid=%s pos=(%d,%d) size=%dx%d pid=%d",
            info.window_id,
            info.x,
            info.y,
            info.w,
            info.h,
            info.pid,
        )
        return info
    log.info("No game window found")
    return None


def _find_game_window_win32() -> WindowInfo | None:
    """Find the Civ 6 window via win32gui.EnumWindows.

    Returns the CLIENT area rect in physical pixel coordinates (matching
    _capture_window_win32 which captures the DX framebuffer at native
    resolution). Uses DPI-aware context for ClientToScreen so that the
    window origin is also in physical space.
    """
    import ctypes

    import win32gui
    import win32process

    # Switch to DPI-aware so ClientToScreen returns physical coordinates,
    # matching GetClientRect which returns physical pixels for DX windows.
    user32 = ctypes.windll.user32
    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_ssize_t(-4)
    old_ctx = None
    try:
        old_ctx = user32.SetThreadDpiAwarenessContext(
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        )
    except Exception:
        pass

    results: list[WindowInfo] = []

    def callback(hwnd: int, _: None) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if any(p in title for p in _APP_NAME_PATTERNS):
            # Use client rect (not window rect) to match PW_CLIENTONLY capture
            cl, ct, cr, cb = win32gui.GetClientRect(hwnd)
            # ClientToScreen maps client (0,0) to screen coordinates
            screen_x, screen_y = win32gui.ClientToScreen(hwnd, (cl, ct))
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            results.append(
                WindowInfo(
                    window_id=hwnd,
                    x=screen_x,
                    y=screen_y,
                    w=cr - cl,
                    h=cb - ct,
                    pid=pid,
                )
            )
        return True

    win32gui.EnumWindows(callback, None)

    if old_ctx:
        user32.SetThreadDpiAwarenessContext(ctypes.c_ssize_t(old_ctx))

    if results:
        w = results[0]
        log.info(
            "Window found: hwnd=%s pos=(%d,%d) size=%dx%d pid=%d",
            w.window_id,
            w.x,
            w.y,
            w.w,
            w.h,
            w.pid,
        )
    else:
        log.info("No game window found")

    return results[0] if results else None


def _get_frame_extents(wid: int) -> tuple[int, int, int, int]:
    """Return (left, right, top, bottom) X11 frame extents for a window.

    Queries ``_NET_FRAME_EXTENTS`` via xprop. Returns (0,0,0,0) if
    unavailable (undecorated window, Wayland without XWayland, etc.).
    """
    try:
        r = subprocess.run(
            ["xprop", "-id", str(wid), "_NET_FRAME_EXTENTS"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Output: _NET_FRAME_EXTENTS(CARDINAL) = left, right, top, bottom
        if "=" in r.stdout:
            vals = r.stdout.split("=")[1].strip().split(",")
            if len(vals) >= 4:
                extents = tuple(int(v.strip()) for v in vals[:4])
                if extents[2] > 0:  # top > 0 means decorated
                    log.info(
                        "Frame extents: left=%d right=%d top=%d bottom=%d (wid=%d)",
                        *extents,
                        wid,
                    )
                return extents
    except Exception:
        pass
    return (0, 0, 0, 0)


def _find_game_window_linux() -> WindowInfo | None:
    """Find the Civ 6 window via xdotool on Linux.

    Searches for windows whose title exactly matches "Civilization VI"
    to avoid false positives (e.g. a browser tab showing civ6-mcp docs).
    When multiple windows match, prefers the one owned by a Civ6 process.
    """
    try:
        r = subprocess.run(
            ["xdotool", "search", "--name", "Civilization VI"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None

        candidates = r.stdout.strip().split("\n")

        # Score candidates: prefer windows owned by the game process
        best: WindowInfo | None = None
        for wid_str in candidates:
            wid = int(wid_str)

            name_r = subprocess.run(
                ["xdotool", "getwindowname", str(wid)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            name = name_r.stdout.strip() if name_r.returncode == 0 else ""
            if name != "Civilization VI":
                continue

            r2 = subprocess.run(
                ["xdotool", "getwindowgeometry", "--shell", str(wid)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            geo: dict[str, int] = {}
            for line in r2.stdout.strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    if v.isdigit():
                        geo[k] = int(v)

            r3 = subprocess.run(
                ["xdotool", "getwindowpid", str(wid)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            pid = int(r3.stdout.strip()) if r3.returncode == 0 else 0

            # NOTE: On GNOME/X11, xdotool getwindowgeometry already
            # returns the content area (excluding title bar). The
            # _NET_FRAME_EXTENTS property describes additional decoration
            # but xdotool accounts for it. No compensation needed.
            info = WindowInfo(
                window_id=wid,
                x=geo.get("X", 0),
                y=geo.get("Y", 0),
                w=geo.get("WIDTH", 0),
                h=geo.get("HEIGHT", 0),
                pid=pid,
            )

            # Prefer the window whose dimensions match a standard game
            # resolution (the inner client window, not the decorated one)
            if best is None:
                best = info
            elif info.w <= best.w and info.h <= best.h and info.w > 0:
                # Smaller "Civilization VI" window is the client area
                best = info

        if best:
            log.info(
                "Window found: wid=%s pos=(%d,%d) size=%dx%d pid=%d",
                best.window_id,
                best.x,
                best.y,
                best.w,
                best.h,
                best.pid,
            )
        else:
            log.info("No game window found")
        return best
    except Exception as e:
        log.debug("xdotool window search failed: %s", e)
        return None


def _capture_window(window_id: int) -> object:
    """Capture a single window as an in-memory image.

    Returns a CGImageRef on macOS, PIL Image on Windows/Linux.
    Falls back to screencapture subprocess on macOS 15+ where
    CGWindowListCreateImage is obsoleted.
    """
    if sys.platform == "win32":
        return _capture_window_win32(window_id)
    if sys.platform == "linux":
        return _capture_window_linux(window_id)
    import Quartz

    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectNull,
        Quartz.kCGWindowListOptionIncludingWindow,
        window_id,
        Quartz.kCGWindowImageBoundsIgnoreFraming,
    )
    if image is not None:
        return image

    # macOS 15: CGWindowListCreateImage obsoleted — screencapture fallback
    log.debug("CGWindowListCreateImage returned nil, trying screencapture -l")
    return _capture_window_screencapture(window_id)


def _capture_window_screencapture(window_id: int) -> object:
    """Capture a window via screencapture subprocess (macOS 15 fallback).

    Uses ScreenCaptureKit internally. Returns a CGImageRef compatible
    with _ocr_vision().
    """
    import tempfile

    import Quartz
    from Foundation import NSData

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        subprocess.run(
            ["screencapture", "-x", "-l", str(window_id), path],
            check=True,
            timeout=5,
            capture_output=True,
        )
        data = NSData.dataWithContentsOfFile_(path)
        if data is None:
            raise RuntimeError(
                f"screencapture produced no output for window {window_id}"
            )
        provider = Quartz.CGDataProviderCreateWithCFData(data)
        cg_image = Quartz.CGImageCreateWithPNGDataProvider(
            provider, None, True, Quartz.kCGRenderingIntentDefault
        )
        if cg_image is None:
            raise RuntimeError(
                f"Failed to create CGImage from screencapture for window {window_id}"
            )
        return cg_image
    finally:
        os.unlink(path)


def _capture_fullscreen_screencapture() -> object | None:
    """Capture the full screen via screencapture (macOS 15 fallback).

    Returns a CGImageRef compatible with _ocr_vision(), or None on failure.
    Unlike the per-window variant, this captures the entire display.
    """
    import tempfile

    import Quartz
    from Foundation import NSData

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        subprocess.run(
            ["screencapture", "-x", path],
            check=True,
            timeout=5,
            capture_output=True,
        )
        data = NSData.dataWithContentsOfFile_(path)
        if data is None:
            log.warning("screencapture fullscreen produced no output")
            return None
        provider = Quartz.CGDataProviderCreateWithCFData(data)
        cg_image = Quartz.CGImageCreateWithPNGDataProvider(
            provider, None, True, Quartz.kCGRenderingIntentDefault
        )
        if cg_image is None:
            log.warning("Failed to create CGImage from fullscreen screencapture")
            return None
        return cg_image
    except Exception as e:
        log.warning("screencapture fullscreen failed: %s", e)
        return None
    finally:
        os.unlink(path)


def _capture_window_win32(hwnd: int) -> "PIL.Image.Image":
    """Capture the game window on Windows by reading the screen.

    A screen grab is the default, not PrintWindow, and that is a safety choice.
    PrintWindow asks the DX12 renderer to redraw itself into a device context, and
    the load flow's own comment records the consequence: "PrintWindow +
    SetForegroundWindow during the DX12 loading phase can crash the renderer".
    Polling for the leader screen's continue button runs inside exactly that phase.
    On 2026-09-20 a capture of the window during a load was followed by the game
    disappearing; the flow then sat on a leader screen with nothing to click.

    A grab reads pixels that are already on screen and sends the game no window
    messages at all. The tradeoff is that it captures whatever is on top, so it is
    wrong for an occluded or minimised window - set CIV_MCP_PRINTWINDOW_CAPTURE=1 to
    use PrintWindow instead for that case, accepting the renderer risk.
    """
    if os.environ.get("CIV_MCP_PRINTWINDOW_CAPTURE", "").strip() == "1":
        return _capture_window_printwindow(hwnd)

    import win32gui
    from PIL import ImageGrab

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    if right <= left or bottom <= top:
        raise RuntimeError(f"Window {hwnd} has no extent ({left},{top})-({right},{bottom})")
    return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)


def _capture_window_printwindow(hwnd: int) -> "PIL.Image.Image":
    """Capture a window via PrintWindow + BitBlt into a PIL Image.

    Only reached when CIV_MCP_PRINTWINDOW_CAPTURE=1 is set: see
    ``_capture_window_win32`` for why this is not the default on Windows.
    """
    import ctypes

    import win32gui
    import win32ui
    from PIL import Image

    # Get the client area dimensions
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w = right - left
    h = bottom - top
    if w <= 0 or h <= 0:
        raise RuntimeError(f"Window {hwnd} has no client area ({w}x{h})")

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    save_dc.SelectObject(bitmap)

    # PrintWindow with PW_CLIENTONLY|PW_RENDERFULLCONTENT for DX windows
    PW_CLIENTONLY = 0x1
    PW_RENDERFULLCONTENT = 0x2
    ctypes.windll.user32.PrintWindow(
        hwnd, save_dc.GetSafeHdc(), PW_CLIENTONLY | PW_RENDERFULLCONTENT
    )

    bmp_info = bitmap.GetInfo()
    bmp_bits = bitmap.GetBitmapBits(True)
    img = Image.frombuffer(
        "RGB",
        (bmp_info["bmWidth"], bmp_info["bmHeight"]),
        bmp_bits,
        "raw",
        "BGRX",
        0,
        1,
    )

    # Cleanup GDI resources
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)
    win32gui.DeleteObject(bitmap.GetHandle())

    return img


def _capture_window_linux(
    window_id: int,
) -> tuple["PIL.Image.Image", dict[str, int]]:
    """Capture a window region on Linux using python-mss.

    mss captures screen regions (not window content by ID), so we use
    xdotool to get the window geometry and grab that screen region.
    The window should be in the foreground for accurate capture.
    Clamps the region to display bounds to avoid XGetImage failures.

    Returns (pil_image, capture_region) where capture_region is the exact
    screen region captured (left, top, width, height). The caller should
    use this — not the WindowInfo geometry — as the OCR origin/extent,
    because xdotool geometry may include window decorations that mss
    doesn't capture (or vice versa depending on WM).
    """
    import mss
    from PIL import Image

    r = subprocess.run(
        ["xdotool", "getwindowgeometry", "--shell", str(window_id)],
        capture_output=True,
        text=True,
        timeout=5,
    )
    geo: dict[str, int] = {}
    for line in r.stdout.strip().split("\n"):
        if "=" in line:
            k, v = line.split("=", 1)
            if v.isdigit():
                geo[k] = int(v)

    x, y = geo.get("X", 0), geo.get("Y", 0)
    w, h = geo.get("WIDTH", 0), geo.get("HEIGHT", 0)
    if w <= 0 or h <= 0:
        raise RuntimeError(f"Window {window_id} has no geometry ({w}x{h})")

    # Clamp to display bounds — mss fails if the region exceeds the screen
    with mss.mss() as sct:
        disp = sct.monitors[0]  # virtual display (union of all monitors)
        disp_r = disp["left"] + disp["width"]
        disp_b = disp["top"] + disp["height"]
        x = max(x, disp["left"])
        y = max(y, disp["top"])
        w = min(w, disp_r - x)
        h = min(h, disp_b - y)
        if w <= 0 or h <= 0:
            raise RuntimeError(f"Window {window_id} is off-screen")

        monitor = {"left": x, "top": y, "width": w, "height": h}
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        return img, monitor


def _ocr_vision(
    cg_image: object,
    origin_x: int,
    origin_y: int,
    extent_w: int,
    extent_h: int,
) -> list[tuple[str, int, int, int, int]]:
    """Run Vision OCR on a CGImage, mapping results to screen points (macOS).

    Coordinates are mapped using the capture region's known bounds in
    screen points (not retina pixels), making this retina-independent:
        screen_x = origin_x + normalized_center_x * extent_w
        screen_y = origin_y + (1 - norm_y - norm_h/2) * extent_h
    """
    import Vision

    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cg_image, None
    )
    success, error = handler.performRequests_error_([request], None)
    if not success:
        log.warning("Vision OCR failed: %s", error)
        return []

    results = []
    _last_rejected_ocr.clear()
    for obs in request.results() or []:
        candidate = obs.topCandidates_(1)[0]
        text = candidate.string()
        conf = candidate.confidence()  # 0.0–1.0
        bbox = obs.boundingBox()
        # Vision: normalized [0,1], origin bottom-left → screen points
        norm_cx = bbox.origin.x + bbox.size.width / 2
        norm_cy = 1 - bbox.origin.y - bbox.size.height / 2  # flip Y
        sx = origin_x + norm_cx * extent_w
        sy = origin_y + norm_cy * extent_h
        sw = bbox.size.width * extent_w
        sh = bbox.size.height * extent_h
        entry = (text, int(sx), int(sy), int(sw), int(sh))
        if conf < 0.5:
            log.debug("Vision OCR: rejected '%s' (conf=%.2f < 0.5)", text, conf)
            _last_rejected_ocr.append(entry)
            continue
        results.append(entry)
    log.info(
        "Vision OCR: %d lines found (%d rejected)",
        len(results),
        len(_last_rejected_ocr),
    )
    if results:
        log.debug("Vision OCR sample: %s", [r[0] for r in results[:5]])
    return results


def _ocr_winrt(
    pil_image: "PIL.Image.Image",
    origin_x: int,
    origin_y: int,
    extent_w: int,
    extent_h: int,
) -> list[tuple[str, int, int, int, int]]:
    """Run Windows Runtime OCR on a PIL Image, mapping results to screen points.

    Uses Windows.Media.Ocr (built-in to Windows 10+, no external binaries).
    """
    import asyncio
    import io

    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import (
        DataWriter,
        InMemoryRandomAccessStream,
    )

    # Convert PIL Image → PNG bytes → WinRT SoftwareBitmap
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    async def _run_ocr():
        stream = InMemoryRandomAccessStream()
        writer = DataWriter(stream)
        writer.write_bytes(png_bytes)
        await writer.store_async()
        await writer.flush_async()
        stream.seek(0)

        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()

        engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            log.warning("WinRT OCR: no engine available")
            return []

        ocr_result = await engine.recognize_async(bitmap)
        return ocr_result

    # Run the async OCR — handle nested event loops
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Already in an async context — run in a new thread
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            ocr_result = pool.submit(lambda: asyncio.run(_run_ocr())).result(timeout=10)
    else:
        ocr_result = asyncio.run(_run_ocr())

    if ocr_result is None:
        return []

    img_w, img_h = pil_image.size
    results = []
    for line in ocr_result.lines:
        text = line.text
        # WinRT OCR: bounding box in pixel coordinates
        words = list(line.words)
        if not words:
            continue
        # Use first word's x and union of all words for the line bounds
        x0 = min(w.bounding_rect.x for w in words)
        y0 = min(w.bounding_rect.y for w in words)
        x1 = max(w.bounding_rect.x + w.bounding_rect.width for w in words)
        y1 = max(w.bounding_rect.y + w.bounding_rect.height for w in words)
        # Map pixel coords to screen coords
        cx = (x0 + x1) / 2 / img_w
        cy = (y0 + y1) / 2 / img_h
        bw = (x1 - x0) / img_w
        bh = (y1 - y0) / img_h
        sx = origin_x + cx * extent_w
        sy = origin_y + cy * extent_h
        sw = bw * extent_w
        sh = bh * extent_h
        results.append((text, int(sx), int(sy), int(sw), int(sh)))
    log.info("WinRT OCR: %d lines found", len(results))
    if results:
        log.debug("WinRT OCR sample: %s", [r[0] for r in results[:5]])
    return results


# Low-confidence OCR results from the most recent OCR call (any engine).
# Used by _find_text as a fuzzy fallback when confident results don't match.
_last_rejected_ocr: list[tuple[str, int, int, int, int]] = []


def _ocr_tesseract(
    pil_image: "PIL.Image.Image",
    origin_x: int,
    origin_y: int,
    extent_w: int,
    extent_h: int,
) -> list[tuple[str, int, int, int, int]]:
    """Run Tesseract OCR on a PIL Image, mapping results to screen points (Linux).

    Groups words into text regions using tesseract's block/par/line hierarchy,
    then splits regions where a large horizontal gap exists between words
    (common in two-column game menus where tesseract merges both columns
    into one line).
    """
    import pytesseract

    img_w, img_h = pil_image.size
    # --psm 11 (sparse text) handles scattered game UI text better than
    # the default page segmentation, especially for faded/low-contrast buttons.
    #
    # Two-pass OCR: normal image first, then a thresholded version to catch
    # faded/low-contrast UI elements (e.g. greyed-out buttons). Results are
    # merged with the normal pass taking priority (higher confidence).
    data = pytesseract.image_to_data(
        pil_image,
        config="--psm 11",
        output_type=pytesseract.Output.DICT,
    )
    # Threshold pass: grayscale → binary at brightness 80
    gray = pil_image.convert("L")
    thresh = gray.point(lambda x: 255 if x > 80 else 0)
    data_thresh = pytesseract.image_to_data(
        thresh,
        config="--psm 11",
        output_type=pytesseract.Output.DICT,
    )
    # Append threshold results with a tag so we can de-duplicate
    n_orig = len(data["text"])
    for key in data:
        data[key].extend(data_thresh[key])

    # Group words by block + par + line (not just block + line)
    lines: dict[tuple[int, int, int], list[int]] = {}
    n = len(data["text"])
    _last_rejected_ocr.clear()
    for i in range(n):
        conf = int(data["conf"][i])
        text_val = data["text"][i].strip()
        if conf < 50:
            if text_val:
                log.debug("OCR: rejected '%s' (conf=%d < 50)", text_val, conf)
                # Store with screen coords for fuzzy fallback matching
                cx = (data["left"][i] + data["width"][i] / 2) / img_w
                cy = (data["top"][i] + data["height"][i] / 2) / img_h
                _last_rejected_ocr.append(
                    (
                        text_val,
                        int(origin_x + cx * extent_w),
                        int(origin_y + cy * extent_h),
                        int(data["width"][i] / img_w * extent_w),
                        int(data["height"][i] / img_h * extent_h),
                    )
                )
            continue
        if not text_val:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(i)

    # Split lines at large horizontal gaps (e.g. two-column menus).
    # A gap > 3x the median word width suggests separate text regions.
    def _split_line(indices: list[int]) -> list[list[int]]:
        if len(indices) <= 1:
            return [indices]
        sorted_idx = sorted(indices, key=lambda i: data["left"][i])
        groups: list[list[int]] = [[sorted_idx[0]]]
        for prev, cur in zip(sorted_idx, sorted_idx[1:]):
            gap = data["left"][cur] - (data["left"][prev] + data["width"][prev])
            avg_h = (data["height"][prev] + data["height"][cur]) / 2
            # Gap larger than 3x the average character height = column break
            if gap > avg_h * 3:
                groups.append([cur])
            else:
                groups[-1].append(cur)
        return groups

    results = []
    for indices in lines.values():
        for group in _split_line(indices):
            text = " ".join(data["text"][i] for i in group)
            x0 = min(data["left"][i] for i in group)
            y0 = min(data["top"][i] for i in group)
            x1 = max(data["left"][i] + data["width"][i] for i in group)
            y1 = max(data["top"][i] + data["height"][i] for i in group)
            cx = (x0 + x1) / 2 / img_w
            cy = (y0 + y1) / 2 / img_h
            bw = (x1 - x0) / img_w
            bh = (y1 - y0) / img_h
            sx = origin_x + cx * extent_w
            sy = origin_y + cy * extent_h
            sw = bw * extent_w
            sh = bh * extent_h
            results.append((text, int(sx), int(sy), int(sw), int(sh)))

    # De-duplicate: threshold pass may re-find text the normal pass got.
    # Keep only one region per unique (normalized_text, approximate_position).
    seen: set[tuple[str, int, int]] = set()
    deduped = []
    for text, sx, sy, sw, sh in results:
        # Bucket position to ~20px grid to catch near-duplicates
        key = (_normalize(text), sx // 20, sy // 20)
        if key not in seen:
            seen.add(key)
            deduped.append((text, sx, sy, sw, sh))
    log.info(
        "Tesseract OCR: %d lines found (%d before dedup)", len(deduped), len(results)
    )
    if deduped:
        log.debug("Tesseract OCR sample: %s", [r[0] for r in deduped[:5]])
    return deduped


def _ocr_game_window(win: WindowInfo) -> list[tuple[str, int, int, int, int]]:
    """Capture the game window and OCR it. All coords in screen points."""
    if sys.platform == "win32":
        # The capture is a screen grab, so it reads whatever is on top, and the game
        # has to be raised before every read - not just before a click. After a cold
        # launch the game comes up behind the terminal or the browser, and without
        # this the flow OCRs that window instead: on 2026-09-20 it read the desktop
        # clock, then a white browser page, and reported "the game is not showing its
        # main menu" while the game sat at its menu underneath.
        _bring_to_front()
        pil_image = _capture_window_win32(win.window_id)
        return _ocr_winrt(pil_image, win.x, win.y, win.w, win.h)
    if sys.platform == "linux":
        pil_image, capture_geo = _capture_window_linux(win.window_id)
        # Use the actual capture region as OCR origin/extent — not the
        # WindowInfo geometry, which may differ due to title bar / WM
        # decoration offsets on some compositors.
        return _ocr_tesseract(
            pil_image,
            capture_geo["left"],
            capture_geo["top"],
            capture_geo["width"],
            capture_geo["height"],
        )
    cg_image = _capture_window(win.window_id)
    # On macOS 15+, CGWindowListCreateImage returns nil and we fall back
    # to `screencapture -l` which captures the FULL window (title bar +
    # content + shadow).  The window bounds from Quartz (win.*) also
    # include title bar and shadow, so the mapping is 1:1.
    #
    # On older macOS, kCGWindowImageBoundsIgnoreFraming captures content
    # only — but the bounds still include framing. Detect this by
    # comparing the capture's aspect ratio to the window bounds.
    import Quartz

    img_px_w = Quartz.CGImageGetWidth(cg_image)
    img_px_h = Quartz.CGImageGetHeight(cg_image)
    if win.w and win.h and img_px_w and img_px_h:
        scale = img_px_w / win.w
        img_pt_h = img_px_h / scale
        # If capture is significantly shorter than window bounds, the
        # title bar / shadow was excluded — offset accordingly.
        gap = win.h - img_pt_h
        if gap > 5:
            return _ocr_vision(cg_image, win.x, win.y + gap, win.w, int(img_pt_h))
    return _ocr_vision(cg_image, win.x, win.y, win.w, win.h)


def _ocr_fullscreen() -> list[tuple[str, int, int, int, int]]:
    """Full-screen OCR fallback for when no game window exists.

    Used during the Aspyr launcher phase before the game process starts.
    Maps via display dimensions in points (retina-independent).
    """
    if sys.platform == "win32":
        return _ocr_fullscreen_win32()
    if sys.platform == "linux":
        return _ocr_fullscreen_linux()

    import Quartz

    main_display = Quartz.CGMainDisplayID()
    display_bounds = Quartz.CGDisplayBounds(main_display)
    disp_w = int(display_bounds.size.width)
    disp_h = int(display_bounds.size.height)
    log.info("Fullscreen OCR: capturing %dx%d (macOS)", disp_w, disp_h)

    image = Quartz.CGWindowListCreateImage(
        display_bounds,
        Quartz.kCGWindowListOptionAll,
        Quartz.kCGNullWindowID,
        Quartz.kCGWindowImageDefault,
    )
    if image is None:
        # macOS 15: CGWindowListCreateImage obsoleted — screencapture fallback
        log.info(
            "Fullscreen OCR: CGWindowListCreateImage returned nil, trying screencapture"
        )
        image = _capture_fullscreen_screencapture()
        if image is None:
            return []

    results = _ocr_vision(image, 0, 0, disp_w, disp_h)
    log.info("Fullscreen OCR: %d text regions found", len(results))
    return results


def _ocr_fullscreen_win32() -> list[tuple[str, int, int, int, int]]:
    """Full-screen capture + OCR on Windows.

    Captures in physical pixel coordinates (DPI-aware) so that results
    are in the same coordinate space as game window OCR (which captures
    DX framebuffers at native resolution).
    """
    import ctypes

    import win32gui
    import win32ui
    from PIL import Image

    user32 = ctypes.windll.user32

    # Switch to DPI-aware to get physical primary monitor dimensions.
    # This ensures the capture and coordinates match physical screen space,
    # consistent with DX fullscreen window captures.
    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_ssize_t(-4)
    old_ctx = None
    try:
        old_ctx = user32.SetThreadDpiAwarenessContext(
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        )
    except Exception:
        pass

    w = user32.GetSystemMetrics(0)  # SM_CXSCREEN (physical when DPI-aware)
    h = user32.GetSystemMetrics(1)  # SM_CYSCREEN (physical when DPI-aware)
    log.info(
        "Fullscreen OCR: capturing %dx%d (DPI-aware=%s)", w, h, old_ctx is not None
    )

    desktop_hwnd = win32gui.GetDesktopWindow()
    desktop_dc = win32gui.GetWindowDC(desktop_hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(desktop_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    save_dc.SelectObject(bitmap)
    save_dc.BitBlt((0, 0), (w, h), mfc_dc, (0, 0), 0x00CC0020)  # SRCCOPY

    bmp_info = bitmap.GetInfo()
    bmp_bits = bitmap.GetBitmapBits(True)
    img = Image.frombuffer(
        "RGB",
        (bmp_info["bmWidth"], bmp_info["bmHeight"]),
        bmp_bits,
        "raw",
        "BGRX",
        0,
        1,
    )

    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(desktop_hwnd, desktop_dc)
    win32gui.DeleteObject(bitmap.GetHandle())

    if old_ctx:
        user32.SetThreadDpiAwarenessContext(ctypes.c_ssize_t(old_ctx))

    results = _ocr_winrt(img, 0, 0, w, h)
    log.info("Fullscreen OCR: %d text regions found", len(results))
    return results


def _ocr_fullscreen_linux() -> list[tuple[str, int, int, int, int]]:
    """Full-screen capture + OCR on Linux using mss + pytesseract."""
    import mss
    from PIL import Image

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        log.info(
            "Fullscreen OCR: capturing %dx%d (Linux)",
            monitor["width"],
            monitor["height"],
        )
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        results = _ocr_tesseract(
            img,
            monitor["left"],
            monitor["top"],
            monitor["width"],
            monitor["height"],
        )
        log.info("Fullscreen OCR: %d text regions found", len(results))
        return results


def _normalize(s: str) -> str:
    """Normalize text for OCR comparison.

    Handles common OCR confusions:
    - Underscores ↔ spaces (game UI shows underscores, OCR reads spaces)
    - 0 ↔ O (OCR confuses zero and capital O, especially in save names like 0A_...)
    - Leading/trailing punctuation noise from tesseract (e.g. ": Load Game =:")

    Trimming is Unicode-aware. An earlier version used ``[^a-z0-9]``, which
    deletes every non-ASCII character — so on a localized install both the
    label and the OCR line normalized to "" and compared equal.
    """
    import re

    s = s.lower().strip().replace("_", " ").replace("0", "o")
    # Strip leading/trailing non-word characters (OCR artifacts). \w is
    # Unicode-aware, so CJK survives while punctuation and spaces do not.
    s = re.sub(r"^[^\w]+", "", s)
    s = re.sub(r"[^\w]+$", "", s)
    return s


def _fuzzy_suffix_match(
    target: str,
    rejected: list[tuple[str, int, int, int, int]],
) -> tuple[str, int, int, int, int] | None:
    """Match by numeric suffix against low-confidence OCR results.

    Tesseract often misreads the prefix of save names (e.g. '0_MCP_0135'
    becomes 'VICP_0135') but the trailing digits are reliable. This matches
    on a suffix of 3+ digits extracted from the target.
    """
    import re

    suffix = re.search(r"(\d{3,})$", target.replace(" ", "").replace("_", ""))
    if not suffix:
        return None
    suffix_str = suffix.group(1)
    for text, x, y, w, h in rejected:
        clean = text.replace(" ", "").replace("_", "")
        if clean.endswith(suffix_str):
            return (text, x, y, w, h)
    return None


def _label_list(target: str | Sequence[str]) -> list[str]:
    """Normalise a label or a label set into a list of candidates."""
    if isinstance(target, str):
        return [target]
    return [t for t in target if t]


def _label_display(target: str | Sequence[str]) -> str:
    """Human-readable form of a label set, for log messages.

    A bare string may be a logical key (``"single_player"``), so it is expanded
    before display — logs should never show the internal key instead of the
    label that was actually searched for.
    """
    if isinstance(target, str):
        return _label_display(_menu_labels(target))
    return " | ".join(t for t in target if t)


def _label_matches(text_norm: str, target_norm: str, exact: bool) -> bool:
    """Does one normalized OCR line match one normalized label?

    The Windows OCR engine inserts a space between CJK glyphs, so the game's
    ``单人模式`` comes back as ``单 人 模 式``. A straight comparison never
    matches, so when the direct test fails we compare again with every space
    removed. English labels are unaffected: the first test already decides them.
    """
    if not target_norm:
        # A label that normalized away to nothing must not match everything.
        return False
    if exact:
        if text_norm == target_norm:
            return True
    elif target_norm in text_norm:
        return True
    squeezed_target = target_norm.replace(" ", "")
    if not squeezed_target:
        return False
    squeezed_text = text_norm.replace(" ", "")
    return squeezed_text == squeezed_target if exact else squeezed_target in squeezed_text


def _find_text(
    ocr_results: list[tuple[str, int, int, int, int]],
    target: str | Sequence[str],
    exact: bool = False,
    prefer_bottom: bool = False,
    min_y_fraction: float = 0.0,
) -> tuple[str, int, int, int, int] | None:
    """Find OCR result matching target text.

    Normalizes underscores to spaces for comparison, since the game UI
    may display underscores but OCR can read them as spaces (or vice versa).

    Args:
        target: One label, or several acceptable labels for the same control
            (e.g. the English and localized spellings of a menu item). The
            first match in screen order wins, as before.
        prefer_bottom: When True and multiple matches exist, return the one
            with the largest y coordinate (lowest on screen). Useful when a
            label and a button have the same text (e.g. "Load Game" title
            at top vs "Load Game" button at bottom).
        min_y_fraction: Reject matches in the top portion of the screen.
            0.7 means only accept matches in the bottom 30%. Requires a
            game window to determine screen bounds; ignored if no window.
    """
    targets_norm = [_normalize(t) for t in _label_list(target)]
    matches = []
    for text, x, y, w, h in ocr_results:
        text_norm = _normalize(text)
        if any(_label_matches(text_norm, t, exact) for t in targets_norm):
            matches.append((text, x, y, w, h))
    if min_y_fraction > 0 and matches:
        # Filter by screen position — use the max y from all results as proxy
        # for screen bottom (avoids needing window info here)
        max_y = max(r[2] for r in ocr_results)
        min_y = max_y * min_y_fraction
        matches = [(t, x, y, w, h) for t, x, y, w, h in matches if y >= min_y]
    if not matches:
        # Second-chance: fuzzy suffix match on rejected low-confidence results
        fuzzy = None
        for candidate in _label_list(target):
            fuzzy = _fuzzy_suffix_match(
                candidate, _last_rejected_ocr
            ) or _fuzzy_suffix_match(candidate, ocr_results)
            if fuzzy:
                break
        if fuzzy:
            log.info(
                "_find_text: '%s' not in confident results, "
                "fuzzy suffix matched rejected '%s'",
                _label_display(target),
                fuzzy[0],
            )
            return fuzzy
        log.debug(
            "_find_text: '%s' not found in %d OCR results",
            _label_display(target),
            len(ocr_results),
        )
        return None
    log.debug("_find_text: '%s' -> %d matches", _label_display(target), len(matches))
    if prefer_bottom:
        return max(matches, key=lambda m: m[2])
    return matches[0]


def _click(x: int, y: int) -> None:
    """Click at screen coordinates (points)."""
    if sys.platform == "win32":
        return _click_win32(x, y)
    if sys.platform == "linux":
        return _click_linux(x, y)
    _require_gui_deps()
    import Quartz

    log.info("Click: screen=(%d,%d) via Quartz", x, y)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.3)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
    time.sleep(0.1)
    e = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def _click_win32(x: int, y: int) -> None:
    """Click at screen coordinates using SendInput (Windows)."""
    import ctypes
    import ctypes.wintypes

    # MOUSEEVENTF_ABSOLUTE + MOUSEEVENTF_VIRTUALDESK maps 0-65535 to the
    # physical virtual screen. All OCR coordinates are in physical pixel
    # space (game window captures DX framebuffers at native resolution,
    # fullscreen captures use DPI-aware mode).
    user32 = ctypes.windll.user32
    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_ssize_t(-4)
    old_ctx = None
    try:
        old_ctx = user32.SetThreadDpiAwarenessContext(
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        )
    except Exception:
        pass

    vx0 = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
    vy0 = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
    vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
    vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN

    if old_ctx:
        user32.SetThreadDpiAwarenessContext(ctypes.c_ssize_t(old_ctx))

    abs_x = int((x - vx0) * 65536 / vw)
    abs_y = int((y - vy0) * 65536 / vh)
    log.info(
        "Click: screen=(%d,%d) abs=(%d,%d) vscreen=(%d,%d)+%dx%d",
        x,
        y,
        abs_x,
        abs_y,
        vx0,
        vy0,
        vw,
        vh,
    )

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.c_ulong),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_VIRTUALDESK = 0x4000
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    ABS_VIRT = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK

    # Move
    move = INPUT(
        type=0,
        mi=MOUSEINPUT(
            dx=abs_x,
            dy=abs_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_MOVE | ABS_VIRT,
            time=0,
            dwExtraInfo=None,
        ),
    )
    user32.SendInput(1, ctypes.byref(move), ctypes.sizeof(INPUT))
    time.sleep(0.15)

    # Click down
    down = INPUT(
        type=0,
        mi=MOUSEINPUT(
            dx=abs_x,
            dy=abs_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTDOWN | ABS_VIRT,
            time=0,
            dwExtraInfo=None,
        ),
    )
    user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT))
    time.sleep(0.05)

    # Click up
    up = INPUT(
        type=0,
        mi=MOUSEINPUT(
            dx=abs_x,
            dy=abs_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTUP | ABS_VIRT,
            time=0,
            dwExtraInfo=None,
        ),
    )
    user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT))


def _click_linux(x: int, y: int) -> None:
    """Click at screen coordinates using xdotool (Linux)."""
    log.info("Click: screen=(%d,%d) via xdotool", x, y)
    subprocess.run(
        ["xdotool", "mousemove", str(x), str(y)],
        capture_output=True,
        timeout=5,
    )
    time.sleep(0.15)
    subprocess.run(
        ["xdotool", "click", "1"],
        capture_output=True,
        timeout=5,
    )


def _is_window_focused() -> bool:
    """Check if a Civ 6 window is the frontmost application."""
    if sys.platform == "win32":
        try:
            import win32gui

            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            return any(p in title for p in _APP_NAME_PATTERNS)
        except Exception:
            return False
    if sys.platform == "linux":
        try:
            r = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode != 0:
                return False
            title = r.stdout.strip()
            return any(p in title for p in _APP_NAME_PATTERNS)
        except Exception:
            return False
    if sys.platform != "darwin":
        return False
    try:
        from AppKit import NSWorkspace

        active = NSWorkspace.sharedWorkspace().frontmostApplication()
        if active is None:
            return False
        name = active.localizedName() or ""
        return any(p in name for p in _PROCESS_NAMES) or any(
            p in name for p in _APP_NAME_PATTERNS
        )
    except ImportError:
        return False


def _is_game_foreground() -> bool:
    """Is the game window the foreground window right now?"""
    if sys.platform != "win32":
        return True
    try:
        import ctypes

        win = _find_game_window()
        if win is None:
            return False
        return ctypes.windll.user32.GetForegroundWindow() == win.window_id
    except Exception:  # noqa: BLE001
        return False


def _bring_to_front(pid: int | None = None) -> None:
    """Bring the game window to front, unless it is already there.

    This is needed, and why is worth stating: the capture is a screen grab, and a grab
    reads whatever is on top. After a cold launch the game can come up behind the
    terminal or the browser, and then the flow OCRs the wrong window entirely - on
    2026-09-20 it read the desktop clock instead of the main menu and reported that
    the game was "not showing its main menu" while the game was sitting right there.

    It is also no longer the risk the load flow's comment describes. The danger
    recorded there is the pair "PrintWindow + SetForegroundWindow during the DX12
    loading phase"; the capture no longer uses PrintWindow, so the renderer is never
    asked to redraw itself into a device context.

    Skipped when the game is already foreground, so nothing is disturbed needlessly.
    Set CIV_MCP_NO_FOREGROUND_STEAL=1 to disable even that.

    Args:
        pid: Process ID from WindowInfo. If None, looks up via
            _find_game_window().
    """
    if os.environ.get("CIV_MCP_NO_FOREGROUND_STEAL", "").strip() == "1":
        log.debug("_bring_to_front: disabled by CIV_MCP_NO_FOREGROUND_STEAL")
        return
    if _is_game_foreground():
        return
    if sys.platform == "win32":
        return _bring_to_front_win32()
    if sys.platform == "linux":
        return _bring_to_front_linux()
    if sys.platform != "darwin":
        raise NotImplementedError(f"Window focus not supported on {sys.platform}")
    try:
        from AppKit import (
            NSApplicationActivateIgnoringOtherApps,
            NSRunningApplication,
        )
    except ImportError:
        log.warning("AppKit not available for window focus")
        return

    if pid is None:
        win = _find_game_window()
        if win is None:
            log.debug("Cannot bring to front: no game window found")
            return
        pid = win.pid

    app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
    if app is None:
        log.warning("Cannot bring to front: no app with PID %d", pid)
        return

    for attempt in range(3):
        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        time.sleep(0.3)
        if app.isActive():
            return
        if attempt < 2:
            log.debug("Window focus attempt %d failed, retrying...", attempt + 1)
    log.warning("Could not confirm window focus after 3 attempts")


def _bring_to_front_win32() -> None:
    """Bring the game window to foreground on Windows.

    Uses the thread-attach trick to bypass Windows' foreground lock:
    attach our thread to the foreground window's thread, then call
    SetForegroundWindow, then detach.
    """
    import ctypes
    import win32gui

    win = _find_game_window_win32()
    if win is None:
        log.debug("Cannot bring to front: no game window found")
        return

    hwnd = win.window_id
    user32 = ctypes.windll.user32

    # If already foreground, nothing to do
    if user32.GetForegroundWindow() == hwnd:
        return

    try:
        # Attach our thread to the foreground window's thread
        fg_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        our_thread = user32.GetCurrentThreadId()
        attached = False
        if fg_thread != our_thread:
            attached = user32.AttachThreadInput(our_thread, fg_thread, True)

        # Restore if minimized, then bring to front
        SW_RESTORE = 9
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)

        if attached:
            user32.AttachThreadInput(our_thread, fg_thread, False)
    except Exception:
        log.debug("Could not bring window to front (non-fatal)")


def _bring_to_front_linux() -> None:
    """Bring the game window to foreground using xdotool (Linux)."""
    win = _find_game_window_linux()
    if win is None:
        log.debug("Cannot bring to front: no game window found")
        return
    subprocess.run(
        ["xdotool", "windowactivate", "--sync", str(win.window_id)],
        capture_output=True,
        timeout=5,
    )
    time.sleep(0.3)


def _wait_for_text(
    target: str | Sequence[str],
    timeout: int = 60,
    exact: bool = False,
    interval: float = 1.5,
    prefer_bottom: bool = False,
    min_y_fraction: float = 0.0,
) -> tuple[str, int, int, int, int] | None:
    """Wait until OCR finds target text in game window.

    Captures only the game window (not the full screen). Falls back to
    full-screen capture when no game window exists (e.g. Aspyr launcher).

    ``target`` may be one label or several acceptable labels for the same
    control; see ``_find_text``.
    """
    _require_gui_deps()
    start = time.time()
    focused = False
    last_results: list[tuple[str, int, int, int, int]] = []
    while time.time() - start < timeout:
        win = _find_game_window()
        if win is None:
            log.debug("No game window found, using full-screen OCR")
            results = _ocr_fullscreen()
            focused = False
        else:
            if not focused:
                _bring_to_front(pid=win.pid)
                time.sleep(0.3)
                focused = True
            try:
                results = _ocr_game_window(win)
            except RuntimeError:
                log.debug("Window capture failed, falling back to full-screen OCR")
                results = _ocr_fullscreen()

        last_results = results
        match = _find_text(
            results,
            target,
            exact=exact,
            prefer_bottom=prefer_bottom,
            min_y_fraction=min_y_fraction,
        )
        elapsed = time.time() - start
        if match:
            log.info("_wait_for_text: '%s' found after %.1fs", _label_display(target), elapsed)
            return match
        log.debug(
            "_wait_for_text: '%s' not found (%.1fs/%ds, %d results)",
            _label_display(target),
            elapsed,
            timeout,
            len(results),
        )
        time.sleep(interval)

    # Log what OCR actually saw on failure — critical for diagnosing misses
    elapsed = time.time() - start
    if last_results:
        seen = [f"'{t}'" for t, *_ in last_results[:20]]
        log.warning(
            "_wait_for_text: '%s' not found after %.0fs. Saw %d items: %s",
            _label_display(target),
            elapsed,
            len(last_results),
            ", ".join(seen),
        )
    else:
        log.warning(
            "_wait_for_text: '%s' not found after %.0fs (no OCR results at all)",
            _label_display(target),
            elapsed,
        )
    return None


def _click_text(
    target: str | Sequence[str],
    timeout: int = 30,
    exact: bool = False,
    post_delay: float = 1,
    prefer_bottom: bool = False,
    min_y_fraction: float = 0.0,
    y_offset: int = 0,
) -> bool:
    """Find text via OCR and click it. Returns success.

    Args:
        target: One label or several acceptable labels for the same control;
            see ``_find_text``.
        y_offset: Pixels to shift the click vertically from bbox center.
            Positive = down, negative = up.  Useful when menu items are
            tightly packed and OCR bbox centers can land between items.
    """
    match = _wait_for_text(
        target,
        timeout=timeout,
        exact=exact,
        prefer_bottom=prefer_bottom,
        min_y_fraction=min_y_fraction,
    )
    if not match:
        return False
    text, x, y, w, h = match
    click_y = y + y_offset
    log.info(
        "OCR: found '%s' at (%d,%d) [%dx%d] — clicking (%d,%d)",
        text,
        x,
        y,
        w,
        h,
        x,
        click_y,
    )
    _bring_to_front()
    time.sleep(0.3)
    _click(x, click_y)
    time.sleep(post_delay)
    return True


# ---------------------------------------------------------------------------
# Crash dialog dismissal (Windows only)
# ---------------------------------------------------------------------------


def _dismiss_crash_dialogs_sync() -> list[str]:
    """Find and dismiss Firaxis crash reporter / exception dialogs (Windows).

    These are standard Win32 dialogs that appear on top of the game after
    an EXCEPTION_ACCESS_VIOLATION or similar crash.  The game continues
    running underneath but Lua calls return degraded data until the
    dialogs are dismissed.

    Returns list of dismissed dialog descriptions.
    """
    if sys.platform != "win32":
        return []

    try:
        import win32con
        import win32gui
    except ImportError:
        return []

    dismissed: list[str] = []

    # Dialog signatures: (title_substring, button_text_to_click)
    _CRASH_DIALOGS = [
        ("Unhandled Exception", "OK"),
        ("Firaxis Crash Reporter", "No"),
    ]

    for title_substr, target_button in _CRASH_DIALOGS:
        # Find all top-level windows matching the title
        def _enum_callback(hwnd: int, results: list) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if title_substr in title:
                results.append(hwnd)
            return True

        matches: list[int] = []
        try:
            win32gui.EnumWindows(_enum_callback, matches)
        except Exception:
            continue

        for hwnd in matches:
            # Find the target button among child windows
            def _enum_children(child_hwnd: int, buttons: list) -> bool:
                try:
                    text = win32gui.GetWindowText(child_hwnd)
                    # Strip Win32 accelerator prefix (&Yes -> Yes, &No -> No)
                    clean = text.replace("&", "")
                    if clean == target_button:
                        buttons.append(child_hwnd)
                except Exception:
                    pass
                return True

            buttons: list[int] = []
            try:
                win32gui.EnumChildWindows(hwnd, _enum_children, buttons)
            except Exception:
                continue

            if buttons:
                try:
                    # BM_CLICK message to press the button
                    win32gui.SendMessage(buttons[0], win32con.BM_CLICK, 0, 0)
                    title = win32gui.GetWindowText(hwnd)
                    dismissed.append(f"{title} (clicked '{target_button}')")
                    log.info(
                        "Dismissed crash dialog: '%s' -> clicked '%s'",
                        title,
                        target_button,
                    )
                except Exception as e:
                    log.debug("Failed to click '%s': %s", target_button, e)

    return dismissed


async def dismiss_crash_dialogs() -> list[str]:
    """Async wrapper for crash dialog dismissal."""
    return await asyncio.to_thread(_dismiss_crash_dialogs_sync)


# ---------------------------------------------------------------------------
# Save discovery
# ---------------------------------------------------------------------------


def get_newest_save() -> tuple[str, float] | None:
    """The most recently written save, whatever its prefix, as (name, mtime).

    Not the same as ``get_latest_autosave``, which only looks at the game's own
    AutoSave_* files. Both live on this box and either can be the newer one: the MCP
    writes 0_MCP_<turn> when a turn begins, the game writes its own autosaves
    alongside, and after a plain exit the game's file can be a turn ahead. "Continue
    Game" resumes whichever is most recent, so this is what to compare against.
    """
    paths: list[str] = []
    for directory in (SAVE_DIR, SINGLE_SAVE_DIR):
        paths.extend(glob.glob(os.path.join(directory, "*.Civ6Save")))
    if not paths:
        return None
    newest = max(paths, key=os.path.getmtime)
    return os.path.basename(newest).replace(".Civ6Save", ""), os.path.getmtime(newest)


def _save_turn(name: str) -> int | None:
    """The turn number carried in a save name, or None if it has none.

    ``0_MCP_0079`` is turn 79; that invariant is what the recovery verification rests
    on, so it is parsed in one place.
    """
    match = re.search(r"(\d+)$", name)
    return int(match.group(1)) if match else None


def _game_probe(timeout: float = 5.0) -> dict:
    """One short tuner query: connected, is a game loaded, and which turn.

    ``_game_turn_number`` cannot tell "the tuner is not there" from "the tuner is there
    but no game is loaded", and those two call for completely different actions: wait,
    or click through a menu. This keeps them apart.
    """
    import asyncio

    from civ_mcp.connection import GameConnection
    from civ_mcp.lua._helpers import SENTINEL

    lua = (
        "local ok, turn = pcall(function() return Game.GetCurrentGameTurn() end) "
        'print("TURN|" .. tostring(ok and turn or "none")) '
        f'print("{SENTINEL}")'
    )

    async def probe() -> dict:
        conn = GameConnection()
        try:
            await conn.connect()
        except ConnectionRefusedError as exc:
            # Nothing is listening: definitive, and a retry would only cost time.
            return {
                "connected": False,
                "ingame": False,
                "turn": None,
                "transient": False,
                "note": str(exc),
            }
        except (ConnectionError, OSError) as exc:
            # The port answered and then dropped us - see the retry in _game_probe.
            return {
                "connected": False,
                "ingame": False,
                "turn": None,
                "transient": True,
                "note": str(exc),
            }
        if conn.ingame_index is None:
            await conn.disconnect()
            return {"connected": True, "ingame": False, "turn": None, "note": ""}
        try:
            for line in await conn.execute_write(lua, timeout=timeout):
                if line.startswith("TURN|"):
                    value = line.split("|", 1)[1]
                    return {
                        "connected": True,
                        "ingame": True,
                        "turn": int(value) if value.isdigit() else None,
                        "note": "" if value.isdigit() else f"turn read as {value!r}",
                    }
            return {"connected": True, "ingame": True, "turn": None, "note": "no reply"}
        finally:
            await conn.disconnect()

    def probe_once() -> dict:
        try:
            return asyncio.run(probe())
        except RuntimeError:
            # Already inside a running event loop: asyncio.run refuses to nest, and the
            # refusal used to be caught below and handed back as "no connection" - the
            # same reading as a game that is not there - for a game whose tuner was open.
            # Observed on 2026-09-20 by calling game_status() from an async recovery
            # script.
            return _probe_off_loop(probe)
        except Exception as exc:  # noqa: BLE001 - a probe must never raise into a caller
            return {
                "connected": False,
                "ingame": False,
                "turn": None,
                "transient": isinstance(exc, OSError)
                and not isinstance(exc, ConnectionRefusedError),
                "note": f"{type(exc).__name__}: {exc}",
            }

    result = probe_once()
    if result["connected"]:
        return result

    # A reconnect immediately after another client closed fails with
    # ERROR_NETNAME_DELETED while the port itself is fine: measured on 2026-09-20 right
    # after a load, the probe failed at 17:30:02 and answered turn 80 at 17:30:04. The
    # retry keys on the *error*, not on the port table - at that moment the table had no
    # LISTEN row at all, so a port-based condition silently never fired.
    if result.get("transient"):
        time.sleep(1.5)
        retry = probe_once()
        if retry["connected"]:
            return retry
    return result


def _probe_off_loop(probe) -> dict:
    """Run the probe coroutine on a thread of its own and return what it reported."""
    import threading

    box: dict = {}

    def runner() -> None:
        try:
            box.update(asyncio.run(probe()))
        except Exception as exc:  # noqa: BLE001 - reported, never raised
            box.update(
                {
                    "connected": False,
                    "ingame": False,
                    "turn": None,
                    "transient": isinstance(exc, OSError)
                    and not isinstance(exc, ConnectionRefusedError),
                    "note": f"{type(exc).__name__}: {exc}",
                }
            )

    thread = threading.Thread(target=runner, name="civ6-tuner-probe", daemon=True)
    thread.start()
    thread.join(timeout=30)
    return box or {
        "connected": False,
        "ingame": False,
        "turn": None,
        "note": "probe thread did not finish in 30s",
    }


def _game_turn_number(timeout: float = 5.0) -> int | None:
    """The current turn, or None when no game is in progress."""
    return _game_probe(timeout).get("turn")


def _ocr_text(results: list[tuple[str, int, int, int, int]] | None) -> str:
    """All OCR boxes as one string, with spaces squeezed out.

    Windows OCR puts a space between every CJK glyph ("回 合 80 / 500"), so a literal
    match on the game's own label fails until the spaces are gone.
    """
    return " ".join(text.replace(" ", "") for text, *_ in results or ())


def _ocr_lines(results: list[tuple[str, int, int, int, int]] | None) -> list[str]:
    """OCR boxes rebuilt into visual lines, top to bottom, spaces squeezed out.

    One line of the game's UI often comes back as several boxes, and **the box order is
    not the reading order**. Measured 2026-09-20: a live session reported turn 81 as
    "turn 8" because the HUD's 回合 81 / 500 had been split into 回 合 8 and 1 / 5 0 0
    and the tail arrived first, so joining the whole screen into one string put the
    digits in the wrong order. Grouping by y and sorting by x is what makes the digits
    adjacent again. Any label spanning two boxes benefits the same way.
    """
    lines: list[list[tuple[int, int, str]]] = []  # (y, x, text) per visual line
    for text, x, y, _w, h in results or ():
        for line in lines:
            # Same visual line, not merely "nearby": the top strip of the window stacks
            # three or four rows within about one text height of each other, and merging
            # those produces a single 80-character pseudo-line.
            if abs(line[0][0] - y) <= max(3, h // 3):
                line.append((y, x, text))
                break
        else:
            lines.append([(y, x, text)])
    return [
        "".join(text for _y, _x, text in sorted(line, key=lambda entry: entry[1])).replace(
            " ", ""
        )
        for line in sorted(lines, key=lambda entries: entries[0][0])
    ]


_TURN_ON_SCREEN = re.compile(r"(?:回合|Turn)\s*(\d+)")
# The canonical HUD form, preferred when it is readable: "回合 81 / 500". It is not
# required, because the HUD is genuinely misread - a recorded turn-59 frame OCRs as
# "回 合 59 巧 00", where the "/ 5" of "/ 500" comes back as one glyph, and requiring the
# slash would lose the turn and read an in-game screen as "unrecognised".
_TURN_ON_SCREEN_WITH_TOTAL = re.compile(r"(?:回合|Turn)\s*(\d+)\s*/\s*(\d+)")


def _turn_in_line(line: str) -> int | None:
    match = _TURN_ON_SCREEN_WITH_TOTAL.search(line) or _TURN_ON_SCREEN.search(line)
    return int(match.group(1)) if match else None


def _ocr_turn(results: list[tuple[str, int, int, int, int]] | None) -> int | None:
    """The turn number the HUD shows, for when the tuner cannot answer.

    The tuner is the better source, but it is exactly what is missing when another
    process holds the single FireTuner connection - and "which turn is this save" is
    the fact a recovery needs most. Parsed line by line, top first: the counter sits in
    the top strip of the window, so the first readable line carrying it is the HUD.
    """
    for line in _ocr_lines(results):
        turn = _turn_in_line(line)
        if turn is not None:
            log.info("Screen HUD read %r -> turn %s", line, turn)
            return turn
    return None


def _screen_kind(results: list[tuple[str, int, int, int, int]] | None) -> str:
    """What the game window is showing, from its OCR text alone."""
    lines = _ocr_lines(results)
    joined = " ".join(lines)
    if any(_TURN_ON_SCREEN.search(line) for line in lines):
        return "in-game"
    if _leader_screen_detected(list(results or ())):
        return "leader intro screen"
    if "单人模式" in joined or "SinglePlayer" in joined:
        return "main menu"
    if "加载游戏" in joined or "LoadGame" in joined:
        return "load game screen"
    if not joined:
        return "nothing readable (intro movie, splash, or a blank frame)"
    return f"unrecognised ({len(results or ())} text boxes)"


def _foreign_tuner_clients(clients: list[int], pids: list[int]) -> list[int]:
    """Connection holders that are neither the game nor this process.

    Our own pid can legitimately appear when the MCP server runs in-process; the game's
    own pid appears as the accepting side, which is handled by the caller.
    """
    own = os.getpid()
    return [pid for pid in clients if pid != own and pid not in pids]


def game_status() -> str:
    """Where the game is right now, and what that state calls for.

    An agent otherwise has to infer this from the wording of whatever failed: "the game
    is not showing its main menu" covers a game that is still starting, one parked on
    the leader screen, and one whose window is simply behind the browser. The same
    status is also what tells a recovery whether it needs to launch, click, or play.

    The screen is read whenever there is a window, not only when the tuner answers:
    with another agent holding the single FireTuner connection, OCR is the only way to
    know that a game is loaded and at which turn.
    """
    pids = _running_game_pids()
    window = _find_game_window()
    tuner = _is_tuner_port_open()
    probe = _game_probe() if tuner else {"connected": False, "ingame": False, "turn": None, "note": ""}

    port = {"listening": False, "clients": []} if tuner else _tuner_port_state()
    holders = _foreign_tuner_clients(port.get("clients", []), pids)
    held_by = ", ".join(f"pid {pid}" for pid in holders)

    boxes: list | None = None
    screen = "not read (no window)"
    screen_turn = None
    if window is not None:
        try:
            boxes = _ocr_game_window(window)
            screen = _screen_kind(boxes)
            screen_turn = _ocr_turn(boxes)
        except Exception as exc:  # noqa: BLE001
            screen = f"unreadable ({type(exc).__name__})"

    turn = probe.get("turn")
    on_screen = turn if turn is not None else screen_turn

    if not pids:
        state = "not_running"
        nxt = "Call launch_game, then check again. Nothing else can work yet."
    elif turn is not None or screen == "in-game":
        state = "in_game"
        where = f"turn {on_screen}" if on_screen is not None else "the current turn"
        if turn is not None:
            nxt = (
                f"In game at {where}. Play it: get_game_overview, then the turn loop. "
                "Nothing needs loading."
            )
        elif held_by:
            nxt = (
                f"A game is loaded and on screen at {where}, but this process cannot "
                f"attach: FireTuner serves one connection and {held_by} already holds "
                "it, so no query or command from here will work. Play it from that "
                "session, or stop it (scripts\\civ6-clean.ps1) and check again."
            )
        elif tuner or port.get("listening"):
            # The port answers but the probe did not: the game is loading, or the tuner
            # dropped the connection (WinError 64 does exactly this while a 4K load is in
            # progress). Either way the game is fine - telling the caller to relaunch
            # would throw away a good position, which is what this lane did before it
            # checked whether anything was listening at all.
            nxt = (
                f"A game is on screen at {where} and FireTuner is listening, but the "
                "probe did not answer"
                + (f" ({probe['note']})" if probe.get("note") else "")
                + ". Wait for the load to finish and call this again; do not restart the "
                "game."
            )
        else:
            nxt = (
                f"A game is on screen at {where} but FireTuner is not listening, which "
                "means the game was started outside the MCP. Restart it with "
                "launch_game (or restart_and_load) to get a readable game."
            )
    elif held_by:
        state = "tuner_busy"
        nxt = (
            f"FireTuner is listening but {held_by} holds its only connection, so this "
            "process cannot attach and waiting will not change that. Stop that process "
            "if it is stale (scripts\\civ6-clean.ps1), or keep playing in that session."
        )
    elif not tuner:
        state = "starting"
        nxt = (
            "The process is up but FireTuner is not listening yet. Wait ~30-60s and "
            "check again; do not launch a second instance."
        )
    elif screen == "leader intro screen":
        state = "leader_screen"
        nxt = (
            "A save is loaded but the game is parked on the leader intro screen. Call "
            "load_game_save with the same save again, or click through Continue Game - "
            "the MCP does the clicking for either."
        )
    elif screen == "main menu":
        newest = get_newest_save()
        state = "main_menu"
        if newest:
            nxt = (
                f'Nothing is loaded. Call load_game_save("{newest[0]}") - the newest '
                f"save, turn {_save_turn(newest[0])}. Continue Game resumes that one."
            )
        else:
            nxt = "Nothing is loaded and no save was found. Call list_saves."
    elif screen == "load game screen":
        state = "loading"
        nxt = "The Load Game screen is open. A load is in progress or was started; let it finish."
    else:
        state = "loading_or_unknown"
        nxt = (
            "The tuner answers but no game is loaded, and the screen is not one this "
            "knows. Wait, then check again; if it persists, the save is still opening "
            "or the window is showing something else."
        )

    if tuner:
        tuner_line = "listening (this process can attach)"
    elif port.get("listening") and held_by:
        tuner_line = f"listening, but {held_by} holds the only connection"
    elif port.get("listening"):
        tuner_line = "listening (no client attached, and connecting from here failed)"
    else:
        tuner_line = "not listening"

    if turn is not None:
        loaded_line = f"yes, turn {turn}"
    elif on_screen is not None:
        loaded_line = f"turn {on_screen} (read from the screen; this process is not attached)"
    elif probe.get("connected"):
        loaded_line = "connected, none loaded"
    else:
        loaded_line = "no connection"

    lines = [
        f"GAME STATE: {state}",
        f"  process     : {'running, pid ' + ', '.join(str(p) for p in pids) if pids else 'not running'}",
        f"  window      : {'yes' if window else 'none'}",
        f"  FireTuner   : {tuner_line}",
        f"  game loaded : {loaded_line}",
        f"  screen      : {screen}",
    ]
    if probe.get("note"):
        lines.append(f"  note        : {probe['note']}")
    lines.append(f"NEXT: {nxt}")
    return "\n".join(lines)


def get_latest_autosave() -> str | None:
    """Find the most recent autosave name (without extension)."""
    saves = glob.glob(os.path.join(SAVE_DIR, "AutoSave_*.Civ6Save"))
    if not saves:
        return None
    saves.sort(key=os.path.getmtime, reverse=True)
    return os.path.basename(saves[0]).replace(".Civ6Save", "")


def list_autosaves(limit: int = 10) -> list[str]:
    """List recent autosave names, newest first."""
    saves = glob.glob(os.path.join(SAVE_DIR, "AutoSave_*.Civ6Save"))
    saves.sort(key=os.path.getmtime, reverse=True)
    return [os.path.basename(s).replace(".Civ6Save", "") for s in saves[:limit]]


# ---------------------------------------------------------------------------
# Menu navigation (blocking — run via asyncio.to_thread)
# ---------------------------------------------------------------------------

# The game renders its front end in whatever language the player selected, so
# a single English literal is not enough: on this machine AppOptions.txt has
# DisplayLanguage=zh_Hans_CN and the main menu offers 单人模式, not
# "Single Player", which made every OCR recovery fail. Each logical control
# therefore carries every label it can appear under. The Chinese strings are
# the game's own, joined out of LocalizationDatabase/Vanilla_zh_Hans_CN.xml by
# Tag (see .tools/join-loc-strings.py), not transliterations.
_MENU_LABELS: dict[str, tuple[str, ...]] = {
    # LOC_SINGLE_PLAYER
    "single_player": ("Single Player", "单人模式"),
    # LOC_LOAD_GAME (the main-menu entry and the Load button are the same word)
    "load_game": ("Load Game", "加载游戏"),
    # LOC_CONTINUE. Matched non-exactly, so 继续 also covers LOC_CONTINUE_GAME
    # (继续游戏), which is what the leader intro screen shows after a load.
    "continue": ("CONTINUE", "继续"),
    # LOC_CONTINUE_GAME, the Single Player submenu item that resumes the most recent
    # save. Kept separate from "continue" because it is matched exactly: on that
    # submenu 继续游戏 sits two rows above 创建游戏, and a fuzzy match there is how a
    # click ends up on the wrong item.
    "continue_game": ("Continue Game", "继续游戏"),
    # LOC_AUTOSAVES — the filter checkbox on the Load Game screen
    "autosaves": ("Autosaves", "自动保存"),
}


def _menu_labels(key: str) -> tuple[str, ...]:
    """Accepted OCR labels for a logical menu control, English first.

    Unknown keys pass through unchanged, so a caller may hand this either a
    logical key from ``_MENU_LABELS`` or a literal label.
    """
    return _MENU_LABELS.get(key, (key,))


def _game_text_language() -> str:
    """The game's configured text language, e.g. ``zh_Hans_CN``.

    Returns "" when AppOptions.txt is missing or unreadable — the callers only
    use this to order label candidates, so a failure is not fatal.
    """
    if sys.platform != "win32":
        return ""
    appdata = os.environ.get("LOCALAPPDATA") or ""
    if not appdata:
        return ""
    path = os.path.join(
        appdata, "Firaxis Games", "Sid Meier's Civilization VI", "AppOptions.txt"
    )
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.lower().startswith("displaylanguage"):
                    return stripped.split(None, 1)[1].strip() if " " in stripped else ""
    except OSError:
        return ""
    return ""


def window_state() -> dict[str, object]:
    """Diagnostic snapshot of the game window.

    Used by the hang path in server.py to record *what the screen looked like*
    before the recovery machinery kills and relaunches the game. Deliberately
    free of Lua calls: the game may be mid-AI-turn, and extra InGame queries
    during that window are themselves a known hang trigger.
    """
    state: dict[str, object] = {"found": False}
    try:
        win = _find_game_window()
    except Exception as exc:  # noqa: BLE001 - diagnostics must never raise
        state["error"] = f"{type(exc).__name__}: {exc}"
        return state
    if win is None:
        return state

    state.update(
        {
            "found": True,
            "window_id": win.window_id,
            "pid": win.pid,
            "x": win.x,
            "y": win.y,
            "w": win.w,
            "h": win.h,
        }
    )
    if sys.platform != "win32":
        return state
    try:
        import win32gui

        hwnd = win.window_id
        foreground = win32gui.GetForegroundWindow()
        state.update(
            {
                "title": win32gui.GetWindowText(hwnd),
                "visible": bool(win32gui.IsWindowVisible(hwnd)),
                "minimised": bool(win32gui.IsIconic(hwnd)),
                "foreground": foreground == hwnd,
                "foreground_window": win32gui.GetWindowText(foreground),
            }
        )
    except Exception as exc:  # noqa: BLE001
        state["win32_error"] = f"{type(exc).__name__}: {exc}"
    return state


def _wait_for_leader_screen(timeout: float = 120) -> bool:
    """Wait for the leader intro screen, which is where a load ends up.

    Returns False both on timeout and when the main menu is on screen instead, since
    that means the load did not take and the caller has to fall back.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        win = _find_game_window()
        try:
            results = _ocr_game_window(win) if win else _ocr_fullscreen()
        except Exception:  # noqa: BLE001 - OCR failure must not end the wait early
            results = _ocr_fullscreen()
        if _leader_screen_detected(results):
            return True
        if _find_text(results, _menu_labels("single_player")):
            log.info("Still on the main menu - the load did not take")
            return False
        time.sleep(2.5)
    return False


def _continue_game_sync(expected_name: str) -> str | None:
    """Load the most recent save via Single Player -> Continue Game (继续游戏).

    Two clicks instead of four, and it is the mechanism the game itself uses to
    resume: it picks the most recent save, so it also implements "the newest save by
    date" rather than "the newest 0_MCP_ file". The turn is then checked against the
    number in the save name, so choosing the save implicitly does not cost the
    verification.

    Returns None when the path is unavailable or the load does not verify, so the
    caller can fall back to picking the save from the list. Returning None is the
    contract: this function never reports a load it has not confirmed.
    """
    _require_gui_deps()
    started = time.time()
    steps: list[str] = []

    # The submenu may already be open: from an earlier attempt, or because the pointer is
    # resting on the item. Clicking the parent again *closes* it, and the parent itself
    # moves ~95px left while the submenu is open, so a coordinate read before that shift
    # misses the item completely. Both were observed on 2026-09-20 - look, then click.
    if (
        _wait_for_text(
            _menu_labels("continue_game"), timeout=1.5, interval=0.75, prefer_bottom=True
        )
        is not None
    ):
        steps.append("Single Player submenu was already open")
    else:
        if not _click_text(
            _menu_labels("single_player"), timeout=90, exact=True, post_delay=0.5
        ):
            log.info("Continue Game path: no main menu to click from")
            return None
        steps.append("Clicked Single Player")

    # Matched exactly: 继续游戏 sits two rows above 创建游戏 on this submenu, and a
    # loose match there is how a click lands on Create Game instead.
    if not _click_text(
        _menu_labels("continue_game"), timeout=5, exact=True, post_delay=1.5
    ):
        log.info("Continue Game path: the item is not on this submenu; using the list")
        return None
    steps.append("Clicked Continue Game")

    if not _wait_for_leader_screen(timeout=120):
        steps.append("WARNING: the leader screen never appeared")
        return None

    if _click_continue_by_colour():
        steps.append("Clicked CONTINUE (colour match on the leader screen)")
    else:
        steps.append("WARNING: leader screen, but no continue click landed")

    turn = _wait_for_turn_number(max_seconds=30)
    if turn is None:
        steps.append("WARNING: no game in progress after Continue Game")
        return None

    expected_turn = _save_turn(expected_name)
    if expected_turn is not None and turn != expected_turn:
        # Continue Game resumed something else. Say so and let the caller pick the
        # save explicitly rather than reporting a load that is not the one asked for.
        steps.append(
            f"WARNING: Continue Game reached turn {turn}, but {expected_name} is "
            f"turn {expected_turn}"
        )
        log.warning("Continue Game resumed turn %s, expected %s", turn, expected_turn)
        return None

    steps.append(f"Game in progress at turn {turn}")
    elapsed = time.time() - started
    return (
        f"Save loading ({elapsed:.0f}s). Steps: {', '.join(steps)}. "
        "Wait ~10s then use get_game_overview to verify."
    )


def _navigate_to_save_sync(save_name: str, tab: str | None = "autosaves") -> str:
    """Navigate: Main Menu → Single Player → Load Game → [tab] → select → Load.

    Args:
        save_name: Display name of the save (no extension).
        tab: Filter checkbox to click (e.g. "Autosaves"), or None to use
            the default view (regular saves shown by default).

    Blocking operation — takes 30-90 seconds. Returns status message.
    """
    _require_gui_deps()  # Fail fast if deps missing
    nav_start = time.time()
    steps = []

    # Every step below assumes the front end is on screen. When it is not, each wait runs
    # to its own timeout instead of failing: measured 2026-09-20, a request to load
    # turn-80 AutoSave_0080 against a game already in progress at turn 80 spent 172s
    # trying to click 'Single Player' on a menu that was not there, and then reported a
    # failure for a game that was fine. Ask the game what it is doing first (~2s).
    loaded_turn = _game_turn_number()
    if loaded_turn is not None:
        wanted = _save_turn(save_name)
        if wanted == loaded_turn:
            return (
                f"Already loaded ({time.time() - nav_start:.0f}s). The game is at turn "
                f"{loaded_turn}, which is what '{save_name}' holds. Nothing to load."
            )
        return (
            f"FAILED ({time.time() - nav_start:.0f}s): a game is already in progress at "
            f"turn {loaded_turn}, so there is no main menu to navigate and "
            f"'{save_name}' (turn {wanted}) cannot be loaded from one. Use "
            f"restart_and_load('{save_name}') to relaunch and load it."
        )

    # The front end has to be up before any of its menus can be clicked, and a cold start
    # can take minutes. Wait for it exactly once, here: the fast path used to wait for the
    # main menu itself and then the list path waited for it again, so a game that had not
    # reached its menu yet paid both timeouts (measured 2026-09-20: a load requested one
    # second after launch spent 172s, then reported FAILED, and the caller only learned
    # the game was fine by asking get_game_status 35s later).
    if not _wait_for_text(_menu_labels("single_player"), timeout=180, exact=True):
        try:
            shown = _screen_kind(_ocr_game_window(_find_game_window()))
        except Exception:  # noqa: BLE001 - a diagnostic must not mask the failure
            shown = "unreadable"
        turn = _game_turn_number()
        if turn is not None:
            detail = f"a game is already in progress at turn {turn}"
        elif shown == "main menu":
            detail = (
                "the main menu is on screen but its 'Single Player' row was not matched"
            )
        else:
            detail = f"the game is still starting (its window shows: {shown})"
        return (
            f"FAILED ({time.time() - nav_start:.0f}s): {detail}, so there was nothing to "
            "navigate. Call get_game_status to see where the game actually is before "
            "retrying, and do not launch a second copy."
        )

    # Fast path. When the caller is asking for the newest save - which is what a
    # crash recovery asks for - Continue Game loads exactly that in two clicks, with
    # no save list to read and no row to pick. It is only used when the requested name
    # IS the newest save on disk, so it cannot silently load something else.
    newest = get_newest_save()
    if newest and newest[0] == save_name:
        log.info("Newest save requested (%s) - trying Continue Game first", save_name)
        fast = _continue_game_sync(save_name)
        if fast is not None:
            return fast
        log.info("Continue Game did not verify; falling back to the save list")

    # Launch the game if it's not running
    if not is_game_running():
        log.info("Game not running — launching before OCR navigation")
        launch_result = _launch_game_sync()
        log.info("Launch result: %s", launch_result)
        # After launch, game should be at main menu (Aspyr launcher handled by _launch_game_sync)
    else:
        # Dismiss crash dialog if present — it overlays the menu and blocks OCR
        _dismiss_crash_dialog()
        # Click through Aspyr launcher if present (macOS shows PLAY button before main menu)
        _click_aspyr_launcher_sync()

    log.info("[1/7] Waiting for main menu (Single Player)...")
    if not _click_text(
        _menu_labels("single_player"), timeout=90, exact=True, post_delay=0.5
    ):
        return (
            "FAILED: the game is not showing its main menu, so the "
            f"'Single Player' entry ({_label_display(_menu_labels('single_player'))}) "
            "could not be clicked. It may still be loading a save, or already "
            "be inside a game — check get_game_overview before retrying."
        )
    steps.append("Clicked Single Player")

    log.info("[2/7] Clicking 'Load Game'...")
    # Click the centre of the OCR box it was found in, with no vertical nudge.
    # A +15 px downward nudge used to be applied here to keep clear of "Resume Game"
    # above, but any fixed offset is resolution-dependent and this one is wrong at
    # 4K: the menu rows there are 38 px apart (measured: 继续游戏 at y=1076, 加载游戏
    # at 1114, 创建游戏 at 1152), so the nudge lands in the gap below 加载游戏 or on
    # 创建游戏. On 2026-09-20 that opened the Create Game screen and the load failed
    # with "Save '0_MCP_0079' not found" while the save list was never on screen.
    # The centre of the box cannot drift onto a neighbour.
    if not _click_text(
        _menu_labels("load_game"), timeout=5, exact=True, post_delay=0.5
    ):
        return "FAILED: Could not find 'Load Game' button."
    steps.append("Clicked Load Game")

    if tab is not None:
        log.info("[3/6] Clicking '%s' filter...", _label_display(_menu_labels(tab)))
        if not _click_text(_menu_labels(tab), timeout=10, exact=True, post_delay=1):
            log.info("%s filter not found — may already be active", tab)
            steps.append(f"{tab} filter (may already be active)")
        else:
            steps.append(f"Clicked {tab} filter")
    else:
        log.info("[3/6] Using default save list (no filter needed)")
        steps.append("Default save list (regular saves)")

    log.info("[4/6] Looking for save '%s'...", save_name)
    if not _click_text(save_name, timeout=15, post_delay=1):
        return (
            f"FAILED: Save '{save_name}' not found. Steps completed: {', '.join(steps)}"
        )
    steps.append(f"Selected save {save_name}")

    log.info("[5/6] Clicking 'Load Game' button (bottom, not title)...")
    # prefer_bottom picks the button over the page title. If the only match
    # is the title (y < 50% of screen), skip it — the button wasn't detected.
    if not _click_text(
        _menu_labels("load_game"),
        timeout=10,
        post_delay=1,
        prefer_bottom=True,
        min_y_fraction=0.7,
    ):
        steps.append("Load Game button not found (may have loaded from double-click)")
    else:
        steps.append("Clicked Load Game button")

    # Wait for save to load, then click through the leader intro screen.
    #
    # NOTE (Windows): PrintWindow + SetForegroundWindow during the DX12
    # loading phase can crash the renderer.  macOS (Quartz) and Linux (mss)
    # are safe to poll during loading since they don't inject window messages.

    log.info("[6/6] Waiting 15s for save to load, then looking for CONTINUE GAME...")
    time.sleep(15)

    # Screen-aware CONTINUE detection: poll OCR and check WHAT we see.
    # If we see "Single Player" / "Multiplayer", we're on the main menu
    # (save load failed) — redo the navigation instead of blindly clicking.
    continue_found = False
    main_menu_detected = False
    poll_start = time.time()
    poll_timeout = 105
    last_status_log = 0

    while time.time() - poll_start < poll_timeout:
        elapsed = time.time() - poll_start
        win = _find_game_window()
        try:
            results = _ocr_game_window(win) if win else _ocr_fullscreen()
        except Exception:
            results = _ocr_fullscreen()

        # Check for CONTINUE (leader screen — good).
        # prefer_bottom: the localized button (继续) is also a common word, and
        # on the leader screen the intro paragraph can contain it — the real
        # button is the bottom-most match, which is also where
        # _click_continue_positional() looks when OCR misses it entirely.
        match = _find_text(results, _menu_labels("continue"), prefer_bottom=True)
        if match:
            text, x, y, w, h = match
            log.info(
                "CONTINUE wait: found '%s' at (%d,%d) after %.0fs — clicking",
                text,
                x,
                y,
                elapsed,
            )
            _bring_to_front()
            _click(x, y)
            time.sleep(3)
            continue_found = True
            steps.append("Clicked CONTINUE")
            break

        # The leader screen is where the load is supposed to end. OCR often cannot
        # read its continue button at all, so recognise the screen and click the
        # control by colour now, rather than waiting out the poll and then clicking
        # positions that mean nothing on this screen.
        if elapsed > 10 and _leader_screen_detected(results):
            log.info(
                "CONTINUE wait: leader screen at %.0fs but no readable button - "
                "clicking by colour",
                elapsed,
            )
            if _click_continue_by_colour():
                continue_found = True
                steps.append("Clicked CONTINUE (colour match on the leader screen)")
            else:
                steps.append("WARNING: leader screen, but no continue click landed")
            break

        # Check for main menu (wrong screen — save load failed)
        menu_match = _find_text(results, _menu_labels("single_player"))
        if menu_match and elapsed > 20:  # give 20s grace for loading transition
            log.warning(
                "CONTINUE wait: ABORT — detected main menu ('%s' visible) "
                "after %.0fs. Save load likely failed. Will retry navigation.",
                menu_match[0],
                elapsed,
            )
            main_menu_detected = True
            steps.append("ABORT: main menu detected during CONTINUE wait")
            break

        # Periodic status log (every 15s)
        if int(elapsed) // 15 > last_status_log:
            last_status_log = int(elapsed) // 15
            seen = [t for t, *_ in (results or [])[:8]]
            log.info("CONTINUE wait: %.0fs elapsed, OCR sees: %s", elapsed, seen)

        time.sleep(2.5)

    if main_menu_detected:
        # Save load failed — we're back at main menu. Redo from step 1.
        log.warning("Restarting save navigation from main menu")
        if _click_text(_menu_labels("single_player"), timeout=15, post_delay=2):
            _click_text(
                _menu_labels("load_game"), timeout=10, post_delay=1, prefer_bottom=False
            )
            time.sleep(1)
            if _click_text(save_name, timeout=15, post_delay=0.5):
                _click_text(
                    _menu_labels("load_game"),
                    timeout=10,
                    post_delay=1,
                    prefer_bottom=True,
                    min_y_fraction=0.7,
                )
                time.sleep(15)
                # One more attempt at CONTINUE
                retry_match = _wait_for_text(
                    _menu_labels("continue"),
                    timeout=60,
                    interval=2.5,
                    prefer_bottom=True,
                )
                if retry_match:
                    text, x, y, w, h = retry_match
                    log.info("Retry: found CONTINUE at (%d,%d) — clicking", x, y)
                    _bring_to_front()
                    _click(x, y)
                    time.sleep(3)
                    steps.append("Retry: clicked CONTINUE after re-navigation")
                else:
                    log.warning(
                        "Retry: CONTINUE still not found — using positional click"
                    )
                    _click_continue_positional()
                    time.sleep(3)
                    steps.append("Retry: CONTINUE not found — positional click")
            else:
                steps.append("Retry: could not find save name in list")
        else:
            steps.append("Retry: could not find Single Player menu item")
    elif not continue_found:
        # OCR timeout — neither CONTINUE nor main menu detected.
        # Use positional click grid as last resort.
        log.warning(
            "OCR: CONTINUE not found after %ds — using positional click grid",
            poll_timeout,
        )
        _click_continue_positional()
        time.sleep(3)
        steps.append("CONTINUE not found via OCR — used positional click fallback")

    # Verify the load by reading the game, not by checking that a port answers.
    # The FireTuner port is open at the main menu as well, so "port open" reported a
    # successful load for a run that never left the leader screen (2026-09-20).
    # Reading the turn is the check the recovery prompt asks for anyway: the caller
    # can compare it with the number in the save name.
    turn = None
    verify_deadline = time.time() + 30
    while turn is None and time.time() < verify_deadline:
        turn = _game_turn_number()
        if turn is None:
            time.sleep(3)
    if turn is not None:
        steps.append(f"Game in progress at turn {turn}")
    else:
        steps.append(
            "WARNING: no game in progress after the load - the save did not open "
            "(a listening FireTuner port is not evidence of a loaded game)"
        )

    nav_elapsed = time.time() - nav_start
    return f"Save loading ({nav_elapsed:.0f}s). Steps: {', '.join(steps)}. Wait ~10s then use get_game_overview to verify."


# ---------------------------------------------------------------------------
# Async public API (called by MCP tools)
# ---------------------------------------------------------------------------


async def kill_game(force: bool = False) -> str:
    """Kill Civ 6 and wait for Steam to deregister.

    Refuses while another session is playing (see ``_other_active_session``): killing a
    game someone else is mid-turn in throws their position away, which is exactly what a
    diagnostic run did to a live session on 2026-09-20. ``force=True`` is for when that
    session is known to be dead.
    """
    other = await asyncio.to_thread(_other_active_session)
    if other and not force:
        return (
            f"NOT KILLED: another session is playing this game ({other}). Killing it "
            "would interrupt that session mid-turn. Pass force=True if that session is "
            "dead, or call get_game_status to see what the game is doing."
        )
    return await asyncio.to_thread(_kill_game_sync)



async def launch_game() -> str:
    """Launch Civ 6 via Steam and wait for process."""
    return await asyncio.to_thread(_launch_game_sync)


async def load_save_from_menu(save_name: str | None = None) -> str:
    """Navigate the main menu to load a save via OCR.

    Args:
        save_name: Save name without extension (e.g. "AutoSave_0221" or
            "0A_GROUND_CONTROL"). If None, loads most recent autosave.

    Checks both regular saves and autosaves directories. Uses the
    appropriate tab in the Load Game screen.

    Requires the game to be at the main menu (launched but no game loaded).
    """
    if save_name is None:
        save_name = get_latest_autosave()
        if save_name is None:
            return "No autosaves found in save directory."

    # The Load Game screen shows regular saves by default.
    # "autosaves" is the logical key for the checkbox filter — only relevant
    # for autosaves. _menu_labels() expands it to the localized spellings.
    auto_path = os.path.join(SAVE_DIR, f"{save_name}.Civ6Save")
    single_path = os.path.join(SINGLE_SAVE_DIR, f"{save_name}.Civ6Save")

    if os.path.exists(auto_path):
        tab = "autosaves"  # need to toggle the Autosaves checkbox
    elif os.path.exists(single_path):
        tab = None  # regular saves shown by default, no tab click needed
    else:
        available = list_autosaves(5)
        # Also list regular saves
        regular = glob.glob(os.path.join(SINGLE_SAVE_DIR, "*.Civ6Save"))
        regular = [
            os.path.basename(s).replace(".Civ6Save", "")
            for s in sorted(regular, key=os.path.getmtime, reverse=True)[:5]
        ]
        avail_str = ", ".join(available + regular) if (available or regular) else "none"
        return f"Save '{save_name}' not found. Available: {avail_str}"

    return await asyncio.to_thread(_navigate_to_save_sync, save_name, tab)


async def restart_and_load(save_name: str | None = None, force: bool = False) -> str:
    """Kill game, relaunch, and load a save. Full recovery sequence.

    This is the recommended tool for recovering from game hangs.
    Takes 60-120 seconds total.

    Refuses while another session is playing, for the same reason ``kill_game`` does:
    a recovery is not worth another session's position. ``force=True`` when that session
    is known to be dead.
    """
    other = await asyncio.to_thread(_other_active_session)
    if other and not force:
        return (
            f"NOT RESTARTED: another session is playing this game ({other}). Killing it "
            "would interrupt that session mid-turn. Pass force=True if that session is "
            "dead."
        )

    results = []

    # Dismiss crash dialogs before kill — they block the process from exiting
    pre_dismissed = await dismiss_crash_dialogs()
    if pre_dismissed:
        log.info("Pre-kill: dismissed %s", pre_dismissed)

    # Step 1: Kill. The check above already ran, so this must not run it again.
    kill_result = await kill_game(force=True)
    results.append(f"Kill: {kill_result}")

    # Step 2: Launch
    launch_result = await launch_game()
    results.append(f"Launch: {launch_result}")
    if "not detected" in launch_result:
        return " | ".join(results) + " | ABORTED: Game failed to launch."

    # Dismiss any lingering crash dialog from previous session (both platforms)
    await dismiss_crash_dialogs()

    # Step 3: Load save via OCR
    load_result = await load_save_from_menu(save_name)
    results.append(f"Load: {load_result}")

    return " | ".join(results)
