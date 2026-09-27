"""Game lifecycle — popup dismissal, save/load, raw Lua execution."""

from __future__ import annotations

import asyncio
import logging

from civ_mcp import lua as lq
from civ_mcp.connection import GameConnection

log = logging.getLogger(__name__)


# Phase 1: the InGame-context batch. These are hidden with SetHide(true), which
# is enough for a control that does not hold the ExclusivePopupManager lock.
#
# This list and spectator.PopupWatcher._NONCRITICAL_POPUPS are two halves of one
# mechanism: the watcher *detects* a visible popup and calls dismiss_popup() to
# clear it. A name in the watcher's list but not in either list here is detected
# for ever and never dismissed - which is what happened to GreatWorkShowcase
# before it was added. tests/test_popup_lists.py pins the two together.
POPUP_NAMES = [
    "InGamePopup",
    "GenericPopup",
    "PopupDialog",
    "BoostUnlockedPopup",
    "GreatWorkShowcase",
    "WorldCongressPopup",
    "WorldCongressIntro",
]

# ExclusivePopupManager popups: these need Close() in their own Lua state, so
# Phase 1 must not SetHide them (that breaks Phase 2's IsHidden check without
# releasing the lock). Phase 2 discovers the states by name keyword, so every
# name below has to contain one of EXCLUSIVE_POPUP_KEYWORDS or the state scan
# cannot reach it - tests/test_popup_lists.py checks that.
EXCLUSIVE_POPUP_KEYWORDS = ("Popup", "Wonder", "Moment", "Era", "Disaster")
EXCLUSIVE_POPUP_NAMES = [
    "TechCivicCompletedPopup",
    "NaturalWonderPopup",
    "NaturalDisasterPopup",
    "WonderBuiltPopup",
    "EraCompletePopup",
    "HistoricMoments",
    "MomentPopup",
    "ProjectBuiltPopup",
    "RockBandPopup",
    "RockBandMoviePopup",
]


async def dismiss_popup(conn: GameConnection) -> str:
    """Dismiss any blocking popup or UI overlay in the game.

    Three-phase approach:
    1. Single batched InGame call that checks all known popup/overlay names
       and closes diplomacy screens (fast — one TCP roundtrip).
    2. Only if Phase 1 found nothing: scan individual Lua states for
       ExclusivePopupManager popups (disaster, wonder, era screens) that
       need Close() in their own state to release the engine event lock.
    3. Safety net: always fire ExclusivePopupManager Close LuaEvents to
       ensure BulkHide counters are decremented even if Phase 1 caught
       the popup by name (SetHide) without proper cleanup.
    """
    dismissed = []

    # Phase 1: Single batched InGame call — handles most cases in one roundtrip.
    # Covers: diplomacy screens, generic popups, world congress, boosts, etc.
    # NOTE: ExclusivePopupManager popups (NaturalDisaster, NaturalWonder,
    # WonderBuilt, EraComplete, RockBand, ProjectBuilt) are handled ONLY in
    # Phase 2 via Close() in their own Lua state.  Phase 1's SetHide() breaks
    # Phase 2's IsHidden check without releasing the PopupManager lock.
    popup_names = POPUP_NAMES
    checks = []
    for name in popup_names:
        checks.append(
            f'do local c = ContextPtr:LookUpControl("/InGame/{name}") '
            f"if c and not c:IsHidden() then "
            f"  pcall(function() UIManager:DequeuePopup(c) end) "
            f"  pcall(function() Input.PopContext() end) "
            f"  c:SetHide(true) "
            f'  print("DISMISSED|{name}") '
            f"end end"
        )
    # LeaderScene 3D model: SetHide does NOT clear the C++ 3D viewport.
    # Must fire Events.HideLeaderScreen() to unload the 3D leader model.
    checks.append(
        'do local ls = ContextPtr:LookUpControl("/InGame/LeaderScene") '
        "if ls and not ls:IsHidden() then "
        "  pcall(function() Events.HideLeaderScreen() end) "
        "  ls:SetHide(true) "
        '  print("DISMISSED|LeaderScene") '
        "end end"
    )
    # Diplomacy screens: report only, do NOT close sessions.
    # Force-closing sessions via DiplomacyManager.CloseSession() bypasses
    # the C++ engine's session lifecycle callbacks, leaving the AI diplomacy
    # subsystem in an inconsistent state that causes turn processing hangs
    # (confirmed across Games 1-5).  Use respond_to_diplomacy() instead.
    checks.append(
        'do local dv = ContextPtr:LookUpControl("/InGame/DiplomacyActionView") '
        "if dv and not dv:IsHidden() then "
        '  print("PENDING|DiplomacyActionView") '
        "end end"
    )
    # NOTE: DiplomacyDealView is NOT dismissed here — it represents an
    # incoming trade deal offer that the agent must accept/reject via
    # get_pending_trades + respond_to_trade.  Dismissing it silently kills
    # the offer (e.g. incoming delegations from other civs).
    checks.append(
        'do local ddv = ContextPtr:LookUpControl("/InGame/DiplomacyDealView") '
        "if ddv and not ddv:IsHidden() then "
        '  print("PENDING|DiplomacyDealView") '
        "end end"
    )
    # Camera reset for cinematic mode
    checks.append(
        "local mode = UI.GetInterfaceMode() "
        "if mode == InterfaceModeTypes.CINEMATIC then "
        '  pcall(function() UI.ClearTemporaryPlotVisibility("NaturalDisaster") end) '
        '  pcall(function() UI.ClearTemporaryPlotVisibility("NaturalWonder") end) '
        "  pcall(function() Events.StopAllCameraAnimations() end) "
        "  pcall(function() UILens.RestoreActiveLens() end) "
        "  UI.SetInterfaceMode(InterfaceModeTypes.SELECTION) "
        '  print("DISMISSED|cinematic_camera") '
        "end"
    )
    pending_deal = False
    pending_diplomacy = False
    try:
        lua = " ".join(checks) + f' print("{lq.SENTINEL}")'
        lines = await conn.execute_write(lua)
        for line in lines:
            if line.startswith("DISMISSED|"):
                dismissed.append(line.split("|", 1)[1])
            elif line.startswith("PENDING|"):
                if "DiplomacyDealView" in line:
                    pending_deal = True
                elif "DiplomacyActionView" in line:
                    pending_diplomacy = True
    except Exception as e:
        log.debug("Phase 1 dismiss failed: %s", e)

    # Pre-check: single InGame call to detect visible ExclusivePopupManager
    # popups.  Phase 2 scans ~30 Lua states individually (~450ms each = ~13.5s)
    # to find these.  This pre-check costs one round-trip (~500ms) and skips
    # Phase 2+3 entirely when no ExclusivePopups are active (>99% of calls).
    exclusive_popup_names = EXCLUSIVE_POPUP_NAMES
    any_exclusive_visible = False
    try:
        precheck_lua = (
            " ".join(
                f'do local c = ContextPtr:LookUpControl("/InGame/{n}") '
                f'if c and not c:IsHidden() then print("EXCL_VISIBLE") end end'
                for n in exclusive_popup_names
            )
            + f' print("{lq.SENTINEL}")'
        )
        precheck_lines = await conn.execute_write(precheck_lua)
        any_exclusive_visible = any("EXCL_VISIBLE" in l for l in precheck_lines)
    except Exception as e:
        log.debug("ExclusivePopup pre-check failed (will run Phase 2): %s", e)
        any_exclusive_visible = True  # fail-open: scan if pre-check errors

    if any_exclusive_visible:
        log.info("ExclusivePopup visible — running Phase 2 state scan")

        # Phase 2: Close ExclusivePopupManager popups in their own Lua states.
        # These need Close() in their OWN state to release the engine lock —
        # Phase 1's SetHide() does NOT release this lock.
        popup_keywords = EXCLUSIVE_POPUP_KEYWORDS
        popup_states = {
            idx: n
            for idx, n in conn.lua_states.items()
            if any(kw in n for kw in popup_keywords)
        }
        log.debug("Phase 2 popup states: %s", popup_states)
        for state_idx, name in popup_states.items():
            # Loop to drain the ExclusivePopupManager's engine queue —
            # each Close() pops the next event, so we keep closing until
            # the popup stays hidden (max 20 to avoid infinite loops).
            for _drain in range(20):
                try:
                    lines = await conn.execute_in_state(
                        state_idx,
                        "pcall(function() if m_kQueuedPopups then m_kQueuedPopups = {} end end); "
                        "if not ContextPtr:IsHidden() then "
                        "  local ok = pcall(Close); "
                        "  if not ok then pcall(OnClose) end; "
                        '  print("DISMISSED") '
                        "end; "
                        'print("---END---")',
                    )
                    if any("DISMISSED" in l for l in lines):
                        dismissed.append(name)
                    else:
                        break  # popup stayed hidden, queue drained
                except Exception as e:
                    log.debug(
                        "Popup check failed for %s (state %d): %s",
                        name,
                        state_idx,
                        e,
                    )
                    break

        # Phase 3: Fallback — if InGame still sees visible ExclusivePopups,
        # probe state indexes to find and close them.  Handles cases where
        # lua_states from the handshake is incomplete (truncated LSQ).
        try:
            check_lua = (
                " ".join(
                    f'do local c = ContextPtr:LookUpControl("/InGame/{n}") '
                    f'if c and not c:IsHidden() then print("STILL_VISIBLE|{n}") end end'
                    for n in exclusive_popup_names
                )
                + f' print("{lq.SENTINEL}")'
            )
            still_visible = await conn.execute_write(check_lua)
            remaining = [
                l.split("|", 1)[1]
                for l in still_visible
                if l.startswith("STILL_VISIBLE|")
            ]
            if remaining:
                log.info(
                    "Phase 3: ExclusivePopups still visible after Phase 2: %s "
                    "(probing state indexes...)",
                    remaining,
                )
                for probe_idx in range(50, 200):
                    if probe_idx in popup_states:
                        continue
                    if not remaining:
                        break
                    try:
                        probe_lines = await conn.execute_in_state(
                            probe_idx,
                            'print(ContextPtr:GetID()); print("---END---")',
                            timeout=1.0,
                        )
                        state_name = probe_lines[0] if probe_lines else ""
                        if state_name not in remaining:
                            continue
                        close_lines = await conn.execute_in_state(
                            probe_idx,
                            "pcall(function() if m_kQueuedPopups then m_kQueuedPopups = {} end end); "
                            "local ok = pcall(Close); "
                            "if not ok then pcall(OnClose) end; "
                            "ContextPtr:SetHide(true); "
                            'print("DISMISSED"); '
                            'print("---END---")',
                            timeout=2.0,
                        )
                        if any("DISMISSED" in l for l in close_lines):
                            dismissed.append(f"{state_name} (probed state {probe_idx})")
                            remaining.remove(state_name)
                            conn.lua_states[probe_idx] = state_name
                            log.info(
                                "Phase 3: Dismissed %s at state %d",
                                state_name,
                                probe_idx,
                            )
                    except Exception:
                        pass
        except Exception as e:
            log.debug("Phase 3 probe failed: %s", e)

    # Final phase: dismiss Windows-level crash dialogs (Firaxis Crash
    # Reporter, Unhandled Exception).  These are Win32 dialogs that appear
    # on top of the game after EXCEPTION_ACCESS_VIOLATION crashes — the
    # game keeps running but Lua calls return degraded data until dismissed.
    from . import game_launcher

    crash_dismissed = await game_launcher.dismiss_crash_dialogs()
    dismissed.extend(crash_dismissed)

    if dismissed:
        msg = f"Dismissed: {', '.join(dismissed)}"
        if pending_diplomacy:
            msg += ". Also: diplomacy session active — use respond_to_diplomacy."
        if pending_deal:
            msg += " (incoming trade deal pending — use get_pending_trades)"
        return msg
    if pending_diplomacy:
        return "Diplomacy session active — use respond_to_diplomacy to handle it."
    if pending_deal:
        return "No popups to dismiss (incoming trade deal pending — use get_pending_trades)."
    return "No popups to dismiss."


# ------------------------------------------------------------------
# Save / Load
# ------------------------------------------------------------------


async def save_game(conn: GameConnection, name: str) -> str:
    """Create a named save. Used for MCP per-turn autosaves."""
    lines = await conn.execute_write(
        f"local gf = {{}}; "
        f'gf.Name = "{name}"; '
        f"gf.Location = SaveLocations.LOCAL_STORAGE; "
        f"gf.Type = SaveTypes.SINGLE_PLAYER; "
        f"gf.IsAutosave = false; "
        f"gf.IsQuicksave = false; "
        f"Network.SaveGame(gf); "
        f'print("OK|{name}"); '
        f'print("{lq.SENTINEL}")'
    )
    if any("OK|" in l for l in lines):
        return f"Saved: {name}"
    return f"Save may have failed: {' '.join(lines)}"


def cleanup_old_autosaves(keep: int = 5) -> None:
    """Delete MCP autosaves older than the most recent `keep` saves."""
    import glob
    import os

    from .game_launcher import SINGLE_SAVE_DIR

    pattern = os.path.join(SINGLE_SAVE_DIR, "0_MCP_*.Civ6Save")
    saves = glob.glob(pattern)
    if len(saves) <= keep:
        return
    saves.sort(key=os.path.getmtime, reverse=True)
    for old in saves[keep:]:
        try:
            os.remove(old)
            log.debug("Deleted old MCP autosave: %s", old)
        except OSError as e:
            log.debug("Failed to delete %s: %s", old, e)


async def list_saves(conn: GameConnection) -> str:
    """List available saves (normal + autosave).

    Uses filesystem scan (reliable — finds all save types including
    autosaves and quicksaves). Falls back to Lua query if filesystem
    scan finds nothing.
    """
    result = _list_saves_filesystem()
    if "No saves found" not in result:
        return result

    # Fallback: Lua-based query (may miss autosaves/quicksaves)
    lua_result = await _list_saves_lua(conn)
    if lua_result is not None:
        return lua_result
    return result


async def _list_saves_lua(conn: GameConnection) -> str | None:
    """Try Lua-based save enumeration. Returns None on failure."""
    try:
        await conn.execute_write(
            f"if not ExposedMembers then ExposedMembers = {{}} end; "
            f"ExposedMembers.MCPSaveList = nil; "
            f"ExposedMembers.MCPSaveQueryDone = false; "
            f"local function OnResults(fileList, qid) "
            f"  ExposedMembers.MCPSaveList = fileList; "
            f"  ExposedMembers.MCPSaveQueryDone = true; "
            f"  UI.CloseFileListQuery(qid); "
            f"  LuaEvents.FileListQueryResults.Remove(OnResults); "
            f"end; "
            f"LuaEvents.FileListQueryResults.Add(OnResults); "
            f"local opts = SaveLocationOptions.NORMAL + SaveLocationOptions.AUTOSAVE + SaveLocationOptions.QUICKSAVE + SaveLocationOptions.LOAD_METADATA; "
            f"UI.QuerySaveGameList(SaveLocations.LOCAL_STORAGE, SaveTypes.SINGLE_PLAYER, opts); "
            f'print("QUERY_SENT"); '
            f'print("{lq.SENTINEL}")'
        )

        import asyncio

        for _ in range(20):
            await asyncio.sleep(0.25)
            check_lines = await conn.execute_write(
                f"if ExposedMembers.MCPSaveQueryDone then "
                f"  local fl = ExposedMembers.MCPSaveList; "
                f"  if fl and #fl > 0 then "
                f'    print("COUNT|" .. #fl); '
                f"    for i, s in ipairs(fl) do "
                f'      if i <= 20 then print("SAVE|" .. i .. "|" .. tostring(s.Name)) end '
                f"    end "
                f'  else print("EMPTY") end '
                f'else print("PENDING") end; '
                f'print("{lq.SENTINEL}")'
            )
            if any(l.startswith("COUNT|") or l == "EMPTY" for l in check_lines):
                results = [l for l in check_lines if l.startswith("SAVE|")]
                if not results:
                    return None  # empty — fall through to filesystem
                lines_out = ["Available saves (use load_save with the index number):"]
                for r in results:
                    parts = r.split("|", 2)
                    idx = parts[1]
                    name = parts[2] if len(parts) > 2 else "?"
                    lines_out.append(f"  {idx}. {name}")
                return "\n".join(lines_out)
    except Exception:
        pass
    return None  # timed out or error — fall through to filesystem


def _list_saves_filesystem() -> str:
    """Scan the save directory on disk (always works)."""
    import glob
    import os

    from .game_launcher import SAVE_DIR

    save_base = os.path.dirname(SAVE_DIR)  # .../Saves/Single
    all_saves: list[tuple[float, str]] = []

    # Autosaves
    for f in glob.glob(os.path.join(SAVE_DIR, "*.Civ6Save")):
        all_saves.append((os.path.getmtime(f), os.path.basename(f)))

    # Normal saves (parent directory)
    for f in glob.glob(os.path.join(save_base, "*.Civ6Save")):
        all_saves.append((os.path.getmtime(f), os.path.basename(f)))

    all_saves.sort(reverse=True)  # newest first
    if not all_saves:
        return "No saves found on filesystem."

    lines = ["Available saves (filesystem scan, sorted by date):"]
    for i, (_mtime, name) in enumerate(all_saves[:25], 1):
        lines.append(f"  {i}. {name.replace('.Civ6Save', '')}")
    return "\n".join(lines)


async def load_save(conn: GameConnection, save_index: int) -> str:
    """Load a save by index from the most recent list_saves() query.

    The game will reload — the FireTuner connection stays alive but
    all Lua state is wiped. Wait a few seconds after calling this.
    """
    lines = await conn.execute_write(
        f"if not ExposedMembers or not ExposedMembers.MCPSaveList then "
        f'  print("ERR:NO_SAVE_LIST"); print("{lq.SENTINEL}"); return '
        f"end; "
        f"local fl = ExposedMembers.MCPSaveList; "
        f"local idx = {save_index}; "
        f"if idx < 1 or idx > #fl then "
        f'  print("ERR:INDEX_OUT_OF_RANGE|" .. #fl); print("{lq.SENTINEL}"); return '
        f"end; "
        f"local save = fl[idx]; "
        f'print("LOADING|" .. tostring(save.Name)); '
        f'print("{lq.SENTINEL}"); '
        f"Network.LeaveGame(); "
        f"Network.LoadGame(save, ServerType.SERVER_TYPE_NONE)"
    )
    for line in lines:
        if line.startswith("ERR:NO_SAVE_LIST"):
            return "Error: No save list cached. Call list_saves() first."
        if line.startswith("ERR:INDEX_OUT_OF_RANGE"):
            count = line.split("|")[1] if "|" in line else "?"
            return f"Error: Index {save_index} out of range (1-{count}). Call list_saves() to see available saves."
        if line.startswith("LOADING|"):
            name = line.split("|", 1)[1]
            return f"Loading save: {name}. Game will reload — wait ~10 seconds then call get_game_overview to verify."
    return "Load command sent. Wait for game to reload."


# The FrontEnd states that answer the save-list query from the main menu, in the order to try.
# LoadGameMenu is the one that owns the flow (LoadGameMenu.lua:459 asks for the list, :440 loads
# the file); MainMenu and FrontEnd register on the same shared event and answer the same call.
_MENU_SAVE_STATES = ("LoadGameMenu", "MainMenu", "FrontEnd")


async def _save_list_states(conn: GameConnection) -> list[tuple[int, str]]:
    """The Lua states to ask for the save list, in order. Empty when none can answer.

    In-game the InGame state owns the UI API. At the main menu there is no InGame state at all
    — the tuner lists only FrontEnd states — and the game's own load screen answers the same
    two calls from there. That is what makes a menu load possible without OCR, without
    clicking, and without the game window in the foreground.
    """
    await conn.ensure_connected()
    if conn.ingame_index is None:
        # A connection opened at the main menu caches FrontEnd state names only, so a game
        # loaded since then would be missed. Re-discovery is one handshake, and it is the same
        # lesson as reading the turn instead of trusting the cached connection state.
        try:
            await conn.reconnect()
        except ConnectionError:
            pass
    if conn.ingame_index is not None:
        return [(conn.ingame_index, "InGame")]
    by_index = sorted(conn.lua_states.items())
    return [
        (index, name)
        for name in _MENU_SAVE_STATES
        for index, state in by_index
        if state == name
    ]


def _save_query_lua(save_name: str) -> str:
    """Lua: ask the game for its save list and load ``save_name`` when it appears in it.

    Two details are load-bearing, both measured live on 2026-09-25:

    * the names the list carries include the extension — ``s.Name`` is
      ``AutoSave_0099.Civ6Save`` — so an equality test against ``AutoSave_0099`` never matched,
      and this whole tier fell through to OCR menu navigation every time;
    * the list arrives on ``LuaEvents.FileListQueryResults`` (``LoadSaveMenu_Shared.lua:1068``),
      which is the event the game's own load screen listens on, so a handler registered here
      from the tuner is called at all.
    """
    return (
        "if not ExposedMembers then ExposedMembers = {} end; "
        "ExposedMembers.MCPLoadResult = nil; "
        "ExposedMembers.MCPLoadDone = false; "
        "local function OnResults(fileList, qid) "
        "  UI.CloseFileListQuery(qid); "
        "  LuaEvents.FileListQueryResults.Remove(OnResults); "
        "  for i, s in ipairs(fileList) do "
        '    local n = tostring(s.Name):gsub("%.Civ6Save$", ""); '
        f'    if n == "{save_name}" then '
        '      ExposedMembers.MCPLoadResult = "FOUND"; '
        "      ExposedMembers.MCPLoadDone = true; "
        "      pcall(function() Network.LeaveGame() end); "
        "      Network.LoadGame(s, ServerType.SERVER_TYPE_NONE); "
        "      return "
        "    end "
        "  end; "
        '  ExposedMembers.MCPLoadResult = "NOT_FOUND"; '
        "  ExposedMembers.MCPLoadDone = true; "
        "end; "
        "LuaEvents.FileListQueryResults.Add(OnResults); "
        "local opts = SaveLocationOptions.NORMAL + SaveLocationOptions.AUTOSAVE "
        "  + SaveLocationOptions.QUICKSAVE + SaveLocationOptions.LOAD_METADATA; "
        "UI.QuerySaveGameList(SaveLocations.LOCAL_STORAGE, SaveTypes.SINGLE_PLAYER, opts); "
        'print("QUERY_SENT"); '
        f'print("{lq.SENTINEL}")'
    )


def _save_poll_lua() -> str:
    """Lua: what became of the query this state was asked to run.

    ``LOST`` is the third answer and it is not a failure: the markers the query set are gone,
    which means this Lua context has been rebuilt - i.e. the game has begun loading. Without it
    a load that starts *and* finishes inside the poll window looks like a state that never
    answered, because the fresh context sits there reporting PENDING. Measured 2026-09-25: the
    tuner came back in about three seconds, all five FrontEnd states read PENDING, the tier
    concluded "never answered", fell through to OCR navigation, and the game was left parked on
    the leader screen with nobody to click CONTINUE.
    """
    return (
        "if ExposedMembers == nil or ExposedMembers.MCPLoadDone == nil then print('LOST') "
        "elseif ExposedMembers.MCPLoadDone then "
        '  print("RESULT|" .. tostring(ExposedMembers.MCPLoadResult)) '
        "else print('PENDING') end; "
        f'print("{lq.SENTINEL}")'
    )


async def _lua_load_in_state(
    conn: GameConnection, state_index: int, state_name: str, save_name: str
) -> str:
    """Ask one state for the save list. Returns ``FOUND``, ``NOT_FOUND`` or ``SILENT``.

    ``FOUND`` means the load was issued from here. ``NOT_FOUND`` means this state answered and
    the name is not in the game's list - the same list every state returns, so there is nothing
    to gain from asking another. ``SILENT`` means no answer arrived in the window, which is worth
    one more state.

    A context that *vanishes*, and one that answers ``LOST``, are both ``FOUND``: the game blasts
    the FrontEnd context as the load begins (``LoadGameMenu.lua:112``) and the InGame context goes
    with it, so the reply never arrives - and a rebuilt context reporting fresh state is the same
    event seen a moment later.
    """
    await conn.execute_in_state(state_index, _save_query_lua(save_name))
    for _ in range(20):
        await asyncio.sleep(0.25)
        try:
            check = await conn.execute_in_state(state_index, _save_poll_lua())
        except Exception:  # noqa: BLE001 - a dead state is the expected signature here
            log.info("The %s state stopped answering - the load has begun", state_name)
            return "FOUND"
        for line in check:
            if line == "RESULT|FOUND" or line == "LOST":
                return "FOUND"
            if line == "RESULT|NOT_FOUND":
                return "NOT_FOUND"
    log.warning("The %s state never answered the save query for '%s'", state_name, save_name)
    return "SILENT"


async def load_game_save(conn: GameConnection, save_name: str) -> str:
    """Load a save by name — no list_saves() prerequisite.

    Two-tier approach:
    1. Lua: query save list, find by name, load in one async operation, then land the load
       (leader screen, CONTINUE click, turn read back). The query runs in the InGame state
       when a game is loaded and in the game's own FrontEnd load-screen states when the main
       menu is up — the main menu has no InGame state at all, which is why this used to fall
       through to OCR menu navigation there.
    2. Filesystem: verify file exists, use OCR menu navigation (slow but
       reliable — works for autosaves and quicksaves that Lua can't find).
    """
    import asyncio
    import sys

    # Accept the name either way: the game's own list carries the extension, and a caller
    # copying a filename out of Explorer has it.
    save_name = save_name.removesuffix(".Civ6Save")

    from . import game_launcher

    # Sitting on the save that was asked for is not a load. Reading the turn is how the old
    # tier-2 path decided this, but with tier 1 able to find any save in the game's own list it
    # would otherwise issue a reload of the position that is already open.
    wanted_turn = game_launcher._save_turn(save_name)
    current_turn = await asyncio.to_thread(game_launcher._game_turn_number)
    if current_turn is not None and wanted_turn == current_turn:
        return (
            f"Already loaded: the game is at turn {current_turn}, which is what "
            f"'{save_name}' holds. Nothing to load - continue with get_game_overview."
        )

    # On the Aspyr Linux port, Network.LoadGame silently does nothing
    # (same as Network.SaveGame). Skip Lua tier and go straight to OCR
    # menu navigation which actually works.
    if sys.platform != "linux":
        # Tier 1: Lua query-match-load (Windows/macOS only)
        try:
            issued_from: str | None = None
            answered = False
            for attempt in range(3):
                # A round that answers nothing at all is the front end not being ready, not a
                # missing save: measured 2026-09-25, 47s after a launch all five FrontEnd states
                # were silent, the tier fell through to OCR navigation, and the same query
                # answered 207 saves a minute later. Wait and ask again before giving up.
                for state_index, state_name in await _save_list_states(conn):
                    outcome = await _lua_load_in_state(conn, state_index, state_name, save_name)
                    if outcome == "FOUND":
                        issued_from = state_name
                        break
                    if outcome == "NOT_FOUND":
                        # Every state answers with the same list, so one NOT_FOUND is the
                        # answer: asking the rest is how a second load goes out for the same
                        # file.
                        answered = True
                        break
                if issued_from is not None or answered:
                    break
                log.info(
                    "No Lua state answered the save query (attempt %d/3) - waiting for the "
                    "front end",
                    attempt + 1,
                )
                await asyncio.sleep(10)

            if issued_from is None:
                # No state claimed it. Before navigating a main menu, check whether a game is
                # open anyway - an earlier load that started inside the poll window, or a click
                # someone else made, shows up here and just needs landing.
                turn = await asyncio.to_thread(game_launcher._game_turn_number)
                if turn is not None:
                    issued_from = "a load that had already started"

            if issued_from is not None:
                landing = await asyncio.to_thread(
                    game_launcher._finish_load_sync, save_name
                )
                log.info("Loaded '%s' via %s; %s", save_name, issued_from, landing)
                return f"Loading save: {save_name} (via {issued_from}). {landing}"

            log.info("Lua query did not find '%s', trying filesystem", save_name)
        except Exception:
            log.debug("Lua load_game_save failed", exc_info=True)
    else:
        log.info(
            "Linux: skipping Lua load (Aspyr port bug), using OCR nav for '%s'",
            save_name,
        )

    # Tier 2: Filesystem verify + OCR menu load
    import os

    from .game_launcher import SAVE_DIR, SINGLE_SAVE_DIR

    auto_path = os.path.join(SAVE_DIR, f"{save_name}.Civ6Save")
    single_path = os.path.join(SINGLE_SAVE_DIR, f"{save_name}.Civ6Save")

    if not os.path.exists(auto_path) and not os.path.exists(single_path):
        return (
            f"Error: Save '{save_name}' not found in Lua query or on filesystem. "
            f"Check the name and try list_saves() to see available saves."
        )

    # File exists but Lua couldn't find it — use OCR menu navigation.
    # If we're at the main menu (no GameCore), navigate directly without
    # restarting. Only restart_and_load if we're in-game.
    from . import game_launcher

    # The cached connection state is not the same question as "is a game loaded". A
    # connection opened while the game was still starting caches gamecore_index=None,
    # and the menu path then waits out every one of its timeouts clicking through a main
    # menu that is not on screen. Measured 2026-09-20: 172s spent on a turn-80 game that
    # was in progress and perfectly fine, after which the caller read the turn in 3s.
    # Ask the game instead of the cache.
    current_turn = await asyncio.to_thread(game_launcher._game_turn_number)
    if current_turn is not None:
        wanted = game_launcher._save_turn(save_name)
        if wanted == current_turn:
            return (
                f"Already loaded: the game is at turn {current_turn}, which is what "
                f"'{save_name}' holds. Nothing to load - continue with get_game_overview."
            )
        return (
            f"FAILED: a game is already in progress at turn {current_turn}, and "
            f"'{save_name}' is turn {wanted}. The main menu is not on screen, so it "
            f"cannot be loaded from there. Call restart_and_load('{save_name}') to "
            f"relaunch and load it, or keep playing the game that is open."
        )

    if conn.gamecore_index is None:
        log.info("At main menu — loading '%s' via OCR menu nav", save_name)
        return await game_launcher.load_save_from_menu(save_name)
    else:
        log.info("In-game — restart_and_load for '%s'", save_name)
        return await game_launcher.restart_and_load(save_name)


async def execute_lua(
    conn: GameConnection, code: str, context: str = "gamecore"
) -> str:
    """Escape hatch: run arbitrary Lua code."""
    if context == "ingame":
        lines = await conn.execute_write(code)
    elif context.isdigit():
        lines = await conn.execute_in_state(int(context), code)
    else:
        lines = await conn.execute_read(code)
    return "\n".join(lines) if lines else "(no output)"
