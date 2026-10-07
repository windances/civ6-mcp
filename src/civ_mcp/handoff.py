"""The handoff: can a fresh session take this match over, and from which save?

A handoff used to be a hand-written prompt file that restated the tools, the save names and
the current turn. It drifted every time a tool changed (measured 2026-09-26: the file
enumerated eleven reads by hand while ``scripts/orient.py`` already did them in one
connection, and it told the reader to run a path that did not exist). The facts it carried
were the problem, not the wording, so this module computes them instead:

    facts    - what is true right now, read passively (``game_launcher.passive_status``):
               the process, the tuner's owner, the heartbeat's last turn, the saves on
               disk with their real turns, and whether a credential is available.
    verdict  - one of six states and what it needs, from those facts alone. Pure, so it is
               tested without a game.
    report   - the same thing for a human to read.
    task     - the prompt for the session that will play, generated from the facts, so it
               cannot name a turn or a save that no longer exists.

Nothing here launches or loads anything: that stays the human's call, which is why the
verdict's job is to say *who* has to do *what*, not to do it.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sys
import time

from . import game_launcher as gl

ROOT = pathlib.Path(__file__).resolve().parents[2]

# The states a handoff can be in. Named after what the human or the session must do next,
# because "the game is not showing its main menu" covers four different situations.
NOT_RUNNING = "not_running"
TUNER_BUSY = "tuner_busy"

#: How many turns the run's played-to record may lag the loaded game before the handoff calls it a
#: different position. A turn or two is bookkeeping: the record names the last turn a *session acted
#: in*, and the human can end a turn from the game's own UI afterwards, so a fresh handoff routinely
#: sees a one-turn gap. The case this warning was measured on was 56 turns wide - the manifest read
#: T288 against a loaded T344 on 2026-10-04, because no session had ever written the field - and the
#: cost of treating a one-turn lag as a different position is that a fresh session is told to
#: discount its own diary.
POSITION_LAG = 2
TUNER_SILENT = "tuner_silent"
NO_MATCH = "no_match"
IN_GAME = "in_game"

_PARSE_SAVE = None


def _parse_save_module():
    """``scripts/parse_save.py``, loaded on demand. None when it cannot be imported.

    The module has to be registered in ``sys.modules`` *before* it is executed: it defines
    dataclasses, and ``dataclasses`` resolves the defining module through ``sys.modules``,
    so executing it unregistered dies with "'NoneType' object has no attribute '__dict__'"
    inside the decorator. ``scripts/turn-of-save.py`` does the same for the same reason.
    """
    global _PARSE_SAVE
    if _PARSE_SAVE is None:
        try:
            spec = importlib.util.spec_from_file_location(
                "parse_save", ROOT / "scripts" / "parse_save.py"
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules["parse_save"] = module
            spec.loader.exec_module(module)
            _PARSE_SAVE = module
        except Exception:  # noqa: BLE001 - a missing parser degrades to the name's turn
            _PARSE_SAVE = False
    return _PARSE_SAVE or None


def save_turn(path: pathlib.Path) -> int | None:
    """The turn the save's **file** holds, or None when it cannot be read.

    The one place a caller should ask this question. The name is not the answer: it is the
    invariant we aim for, and it has been wrong in the field - measured 2026-09-27, four of the
    nine newest MCP saves were named one turn low because `end_turn` built the name from the same
    post-advance read that printed `Turn 203 -> 203` (`0_MCP_0215` holds T216, `0_MCP_0212` holds
    T213). The game's own `AutoSave_NNNN` is different again: its name runs one ahead of the turn
    it holds, by design.
    """
    return _save_meta(path, parse=True).get("turn")


def _save_meta(path: pathlib.Path, parse: bool = True) -> dict:
    """One save: name, family, mtime, the turn in its name, and the turn in the file.

    The name is an invariant for ``0_MCP_NNNN`` and carries no turn at all for a manual
    save, and the game's own autosave names **run one ahead of the turn they hold**
    (measured 2026-09-26 on three pairs: ``0_MCP_0142`` holds T142, ``AutoSave_0142`` holds
    T141). So the file is asked rather than trusted; ``turn_from_name`` stays in the record
    to show how far the name is from the truth.
    """
    stat = path.stat()
    name = path.name.replace(".Civ6Save", "")
    info = {
        "name": name,
        "path": str(path),
        "family": "autosave" if name.startswith("AutoSave_") else "mcp" if name.startswith("0_MCP_") else "manual",
        "mtime": stat.st_mtime,
        "mtime_text": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
        "turn_from_name": gl._save_turn(name),
        "turn": None,
        "leader": None,
        "turn_source": "name",
    }
    module = _parse_save_module() if parse else None
    if module is not None:
        try:
            # parse_save narrates its decompression on stderr; this is a library call.
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                meta, _ = module.parse_save(path)
            turn = getattr(meta, "game_turn", None)
            if turn:
                info["turn"] = int(turn)
                info["turn_source"] = "file"
            info["leader"] = getattr(meta, "leader", None) or getattr(meta, "civ", None)
        except Exception:  # noqa: BLE001
            pass
    if info["turn"] is None:
        info["turn"] = info["turn_from_name"]
    return info


def save_inventory(limit: int = 6, parse_top: int = 4) -> dict:
    """The newest saves from both families, newest first, with the turn each one holds.

    Both families matter and neither is authoritative: the MCP writes ``0_MCP_<turn>`` when
    a turn begins and the game writes ``AutoSave_<turn>`` beside it, so "Continue Game"
    resumes whichever is newest, and after a rollback the MCP name can belong to the
    abandoned branch (two files named for the same turn, different boards).

    The check that is worth making is not "do the names agree" - the two families are
    numbered differently by design - but **is the newest file also the furthest position**.
    When it is not, a rollback happened and the file the game would resume is not the
    furthest game.
    """
    paths: list[pathlib.Path] = []
    for directory in (gl.SAVE_DIR, gl.SINGLE_SAVE_DIR):
        if directory and pathlib.Path(directory).is_dir():
            paths.extend(pathlib.Path(directory).glob("*.Civ6Save"))
    paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    saves = [
        _save_meta(path, parse=index < parse_top) for index, path in enumerate(paths[:limit])
    ]
    newest = saves[0] if saves else None
    newest_autosave = next((s for s in saves if s["family"] == "autosave"), None)
    newest_mcp = next((s for s in saves if s["family"] == "mcp"), None)

    parsed = [s for s in saves if s["turn"] is not None]
    furthest = max(parsed, key=lambda s: s["turn"]) if parsed else None
    newest_is_furthest = bool(furthest and newest and furthest["name"] == newest["name"])

    notes: list[str] = []
    lag = {
        family: entry["turn"] - entry["turn_from_name"]
        for family, entry in (("mcp", newest_mcp), ("autosave", newest_autosave))
        if entry and entry["turn"] is not None and entry["turn_from_name"] is not None
    }
    if lag.get("autosave") == -1:
        notes.append(
            "the game's autosave names run one ahead of the turn they hold "
            f"({newest_autosave['name']} holds T{newest_autosave['turn']}), while "
            "0_MCP_NNNN holds turn NNNN"
        )

    warning = None
    if not newest_is_furthest and furthest and newest:
        warning = (
            f"the newest save by time is {newest['name']} (T{newest['turn']}) but the "
            f"furthest position on disk is {furthest['name']} (T{furthest['turn']}) - a "
            f"rollback leaves the abandoned branch's files behind, so decide deliberately "
            f"which one to load (scripts\\turn-of-save.py prints either turn)"
        )

    return {
        "count": len(paths),
        "saves": saves,
        "newest": newest,
        "newest_autosave": newest_autosave,
        "newest_mcp": newest_mcp,
        "furthest": furthest,
        "newest_is_furthest": newest_is_furthest,
        "name_lag": lag,
        "notes": notes,
        "warning": warning,
    }


def credential_status() -> dict:
    """Is a model credential available to a headless launch?

    The launcher points ``DSH_HOME`` at the project's ``.dsh-home``, which carries no
    credential store, so the global ``~/.dsh/.credentials.yaml`` does not apply and the
    environment variable is the only route (SETUP-WINDOWS.md). A launch without it starts
    the MCP, runs for a few seconds, then dies with MISSING_CREDENTIAL.
    """
    present = bool(os.environ.get("DEEPSEEK_API_KEY"))
    global_store = pathlib.Path.home() / ".dsh" / ".credentials.yaml"
    return {
        "present": present,
        "variable": "DEEPSEEK_API_KEY",
        "project_home_has_store": any(
            (ROOT / ".dsh-home").glob("**/credentials*")
        )
        if (ROOT / ".dsh-home").is_dir()
        else False,
        "global_store_exists": global_store.is_file(),
        "note": (
            ""
            if present
            else "DEEPSEEK_API_KEY is not set in this environment, and the launcher's "
            "DSH_HOME has no credential store, so a headless launch will die with "
            "MISSING_CREDENTIAL (SETUP-WINDOWS.md:28)."
        ),
    }


def collect_facts(passive: dict | None = None, inventory: dict | None = None,
                  credential: dict | None = None, probe: dict | None = None) -> dict:
    """Everything a verdict is made of. Inject nothing to read the real state.

    ``probe`` is the one intrusive reading (a tuner connect), and the caller is expected to
    pass it only when ``passive['tuner']['foreign_clients']`` is empty and no fresh
    heartbeat names another pid. Passing ``None`` means "not probed", which the verdict
    reads as "cannot yet say a match is loaded" rather than as "no match".
    """
    passive = gl.passive_status() if passive is None else passive
    inventory = save_inventory() if inventory is None else inventory
    credential = credential_status() if credential is None else credential
    heartbeat = passive.get("heartbeat") or {}

    # Which playthrough is loaded. The heartbeat was the only source and it is written by another
    # process that may have died hours ago - measured 2026-10-03, a handoff check opened with
    # `MATCH china/911679432, heartbeat 101.7h old (phase playing, T1, pid 26640 gone)` while the
    # loaded game was `china_-1894041591` at T289, and the note three lines down admitted the
    # disagreement. The run manifest is the authority now: it is read from the directory a session
    # will actually write to, and it is checked against the game at session start. The heartbeat is
    # still reported for the age/phase/pid it alone knows - it is just no longer asked *which* game
    # this is when a manifest can answer.
    manifest = None
    try:
        from civ_mcp import run_manifest

        manifest = run_manifest.load(run_manifest.resolve_data_dir())
    except Exception:  # noqa: BLE001 - a handoff check must not fail on this
        manifest = None
    if manifest and manifest.get("civ"):
        source = "run manifest"
        civ = manifest.get("civ")
        seed = manifest.get("seed")
        last_turn = manifest.get("last_turn") or heartbeat.get("turn")
    else:
        source = "heartbeat"
        civ = heartbeat.get("civ")
        seed = heartbeat.get("seed")
        last_turn = heartbeat.get("turn")

    return {
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "civ": civ,
        "seed": seed,
        "run_id": manifest.get("run_id") if manifest else heartbeat.get("run_id"),
        "run_label": manifest.get("label") if manifest else None,
        "identity_source": source,
        "last_turn": last_turn,
        "heartbeat": heartbeat,
        "game": {"running": bool(passive.get("pids")), "pids": list(passive.get("pids") or [])},
        "window": passive.get("window"),
        "tuner": passive.get("tuner") or {},
        "other_session": passive.get("other_session"),
        "probe": probe,
        "saves": inventory,
        "credential": credential,
    }


def _probe_allowed(facts: dict) -> bool:
    """True when connecting cannot disturb anyone: no foreign client, no live session."""
    if facts.get("other_session"):
        return False
    tuner = facts.get("tuner") or {}
    if tuner.get("foreign_clients"):
        return False
    if not tuner.get("listening"):
        return False
    return True


def probe_facts(facts: dict) -> dict:
    """Add one tuner probe to the facts when (and only when) it is safe. Returns facts."""
    if not _probe_allowed(facts):
        return facts
    try:
        facts["probe"] = gl._game_probe()
    except Exception as exc:  # noqa: BLE001 - a failed probe is not a failed handoff
        facts["probe"] = {"connected": False, "ingame": False, "turn": None, "note": str(exc)}
    return facts


def recommend_save(facts: dict) -> dict | None:
    """The save to load: the newest of either family, which is what Continue Game resumes."""
    return (facts.get("saves") or {}).get("newest")


def _heartbeat_turn(value: object) -> int | None:
    """A turn read out of a passive file, or None when it does not name one.

    The heartbeat is written by another process, so this reader has to expect anything in it. A
    value that is not a number is "unknown", not a reason to fail the check: a heartbeat holding
    ``"turn": "?"`` (the log line's placeholder, which ``server.py`` used to pass to
    ``heartbeat.write``) made this module raise ValueError and ``scripts/resume-game.ps1`` die
    before it printed a single line - measured 2026-09-28.
    """
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def verdict(facts: dict) -> dict:
    """One state, who has to act, and the command that acts. Pure."""
    saves = facts.get("saves") or {}
    save = recommend_save(facts)
    save_name = save["name"] if save else None
    probe = facts.get("probe") or {}
    blockers = [facts["credential"]["note"]] if not facts["credential"]["present"] else []
    warning = saves.get("warning")

    out = {
        "state": NOT_RUNNING,
        "ready": False,
        "turn": None,
        "save": save_name,
        "needs": [],
        "blockers": blockers,
        "warnings": [warning] if warning else [],
        "next_command": "",
    }

    if facts.get("other_session"):
        out["state"] = TUNER_BUSY
        out["needs"] = [
            f"another session is playing ({facts['other_session']})",
            "either keep playing in that session, or stop it with scripts\\civ6-clean.ps1",
        ]
        return out

    if not facts["game"]["running"]:
        out["state"] = NOT_RUNNING
        out["needs"] = [
            "launch the game (Steam), then load "
            + (save_name or "the newest save - none was found")
        ]
        return out

    if probe.get("ingame") and probe.get("turn") is not None:
        out["state"] = IN_GAME
        out["ready"] = True
        out["turn"] = int(probe["turn"])
        out["next_command"] = "scripts\\resume-game.ps1"
        played = _heartbeat_turn(facts.get("last_turn"))
        if played is not None and abs(played - out["turn"]) > POSITION_LAG:
            out["warnings"].append(
                f"the run's played-to turn is T{played}, the loaded game says T{out['turn']} - "
                f"{abs(played - out['turn'])} turns apart, so the notes in the diary belong to "
                "another position"
            )
        return out

    if not (facts.get("tuner") or {}).get("listening"):
        out["state"] = TUNER_SILENT
        out["needs"] = [
            "FireTuner is not listening while the game runs: it was started without "
            "EnableTuner=1, or it is still starting",
            "restart the game with the tuner, or wait and check again",
        ]
        return out

    # The game is up, the tuner is ours to ask, and no match is loaded: menu, leader
    # screen, or a load still in progress - which OCR could tell apart and this must not,
    # so the need is phrased to cover both.
    out["state"] = NO_MATCH
    out["needs"] = [
        "load a save: "
        + (save_name or "none found - start a match or copy a save into Saves\\Single")
        + " (if a load is already running, wait for it to finish)"
    ]
    return out


def render(facts: dict, result: dict) -> str:
    """The report a human reads: facts first, then the verdict."""
    saves = facts.get("saves") or {}
    heartbeat = facts.get("heartbeat") or {}
    tuner = facts.get("tuner") or {}
    lines = [f"HANDOFF CHECK  {facts['checked_at']}"]

    match = f"{facts.get('civ') or '?'}/{facts.get('seed') or '?'}"
    # Say where the identity came from: the two sources disagree exactly when the heartbeat is
    # stale, which is when a reader most needs to know which one answered.
    source = facts.get("identity_source")
    if source == "run manifest":
        match += f", from the run manifest"
        if facts.get("run_label"):
            match += f' ("{facts["run_label"]}")'
    elif facts.get("run_id"):
        match += f", last run {facts['run_id']}"
    if heartbeat and source != "run manifest":
        # The turn in the heartbeat is a number or nothing: a file written before 2026-09-28 can hold
        # the log line's "?" (see `_heartbeat_turn`), and a report should say "unknown", not "T?".
        beat_turn = _heartbeat_turn(heartbeat.get("turn"))
        match += (
            f", heartbeat {heartbeat.get('age_seconds', 0) / 3600:.1f}h old "
            f"(phase {heartbeat.get('phase')}, "
            f"{f'T{beat_turn}' if beat_turn is not None else 'turn unknown'}, "
            f"pid {heartbeat.get('pid')} {'alive' if heartbeat.get('pid_alive') else 'gone'})"
        )
    elif heartbeat:
        match += (
            f", heartbeat {heartbeat.get('age_seconds', 0) / 3600:.1f}h old "
            f"(pid {heartbeat.get('pid')} {'alive' if heartbeat.get('pid_alive') else 'gone'})"
        )
    lines.append(f"  MATCH      {match}")

    game = facts["game"]
    window = (facts.get("window") or {}).get("pid")
    lines.append(
        f"  GAME       {'running, pids ' + ', '.join(str(p) for p in game['pids']) if game['running'] else 'not running'}"
        + (f", window pid {window}" if window else "")
    )
    lines.append(
        f"  TUNER      {'listening' if tuner.get('listening') else 'not listening'}"
        + (f", held by pid {', '.join(str(p) for p in tuner.get('foreign_clients') or [])}"
           if tuner.get("foreign_clients") else ", no client")
        + (f" ({tuner['note']})" if tuner.get("note") else "")
    )

    if saves.get("saves"):
        for entry in saves["saves"][:4]:
            lines.append(
                f"  SAVE       {entry['name']:<16} T{str(entry['turn']):<4} {entry['mtime_text']} "
                f"[{entry['family']}, turn from {entry['turn_source']}]"
            )
    else:
        lines.append("  SAVE       none found")
    for note in saves.get("notes") or []:
        lines.append(f"  NOTE       {note}")
    if saves.get("warning"):
        lines.append(f"  WARN       {saves['warning']}")

    probe = facts.get("probe")
    lines.append(
        "  PROBE      "
        + (
            f"connected={probe.get('connected')} ingame={probe.get('ingame')} "
            f"turn={probe.get('turn')}"
            if probe
            else "not probed (the tuner is not ours to ask, or nothing is listening)"
        )
    )

    credential = facts["credential"]
    lines.append(
        "  CREDENTIAL "
        + (f"{credential['variable']} present" if credential["present"] else credential["note"])
    )

    lines.append(f"  VERDICT    {result['state'].upper()}" + (f", T{result['turn']}" if result["turn"] else ""))
    for need in result["needs"]:
        lines.append(f"  NEEDS      {need}")
    for blocker in result["blockers"]:
        lines.append(f"  BLOCKED    {blocker}")
    for item in result["warnings"]:
        lines.append(f"  NOTE       {item}")
    lines.append(
        "  NEXT       "
        + (
            result["next_command"] + "   (generate the task and launch the session)"
            if result["ready"] and not result["blockers"]
            else "fix the blocker above, then scripts\\resume-game.ps1"
            if result["ready"]
            else "nothing to launch yet"
        )
    )
    return "\n".join(lines)


def _victory_text(facts: dict) -> str | None:
    """The game's own `GAME OVER` line, when the match is already finished.

    The preflight used to read the turn off the save and never read that line: measured T385, where
    a "play up to 100 turns" task was handed to a session in a match that had already reported
    `GAME OVER - VICTORY (Culture)`, and the task published for the conquest that followed was
    retired as unexecutable minutes later. The line comes from the probe (`get_game_overview`);
    anything that fills `facts["victory"]` or `facts["probe"]["victory"]` is honoured.
    """
    for source in (facts, facts.get("probe") or {}):
        text = source.get("victory")
        if text:
            return str(text).strip()
    return None


def task_text(facts: dict, result: dict, turns: int = 100, rollback: bool = False,
              after_victory: bool = False) -> str:
    """The prompt for the session that takes over, written from the facts.

    Deliberately not a copy of the policy: the policy is AGENTS.md and the skill, which the
    session is given anyway. This carries only what is specific to *this* handoff - the turn
    to expect, the run it continues, the cap - so no instruction here can go stale between
    sessions. The dynamic sentences are their own paragraphs, so an interpolated turn or
    timestamp cannot break the wrapping of the text around it.

    ``rollback=True`` is the one scenario that has to be stated rather than computed: the
    human deliberately loaded an earlier save, and everything that says "get to the furthest
    position" is wrong for the rest of that session.

    ``after_victory=True`` is the other one, and it is the human's option (2026-10-07: a victory
    must not be a stop condition). A finished match without it is *refused* in the task text,
    because a session launched into one has nothing to play.
    """
    if not after_victory:
        after_victory = bool(result.get("after_victory"))
    expected = result["turn"]
    if expected is None:
        # The probe cannot answer while another session holds the tuner, but the saves can: the
        # report has already read them. Measured 2026-10-08 at T387 - a tuner-busy preflight wrote
        # "found turn None" into the task a session was launched with, while the same report showed
        # `AutoSave_0387 holds T386`.
        newest = (facts.get("saves") or {}).get("newest") or {}
        expected = newest.get("turn") or "unknown"
    victory = _victory_text(facts)
    if victory and after_victory:
        victory_paragraph = (
            f"**This match is already won - {victory} - and you are continuing it deliberately.**\n"
            "The human asked for a won match to stay playable, so the goal is the same as any other\n"
            "turn: the tasks in `prompts/tasks/tmp/`, the checks, the diary. Two things are specific\n"
            "to this state. First, the engine may refuse to advance a turn until the victory screen\n"
            "is cleared: try `dismiss_popup`, read the screen with `.tools/whats-on-screen.py`, and\n"
            "if the turn still will not advance ask the human to press the victory screen's\n"
            "\"one more turn\" button - nothing in Lua can see that dialog. Second, `get_game_overview`\n"
            "keeps printing the `GAME OVER` line, so do not read it as a new stop condition."
        )
    elif victory:
        victory_paragraph = (
            f"**This match is already won: {victory}.** There is nothing to play here - read the\n"
            "`GAME OVER` line in `get_game_overview` for yourself, then stop and report. If the human\n"
            "wants the match continued anyway, the launcher has to pass `-AfterVictory` (handoff's\n"
            "`--after-victory`): a task published after a victory cannot be executed in that position,\n"
            "which is what cost a session at T385."
        )
    else:
        victory_paragraph = None
    parts = ([victory_paragraph] if victory_paragraph else []) + [
        "Take over the live Civilization VI match that the previous session left paused."
        if not rollback
        else "Take over the live Civilization VI match at the position the human deliberately "
        "rolled back to.",
        "Read `AGENTS.md` (the orchestrator skill loads it) and follow it. Then, in this order:",
        f"0. `get_game_status` - it must answer `in_game`, or stop and report. The handoff\n"
        f"   preflight checked this at {facts['checked_at']} and found turn {expected}; the state\n"
        f"   can change between that check and this call, because the game can be closed or\n"
        f"   another session can take the tuner.\n"
        f"   **`starting` is not a stop condition when your own reads work.** FireTuner serves one\n"
        f"   connection and stops accepting new ones once one is established, so the port probe inside\n"
        f"   that status reports \"not listening\" for the session that holds it, and its OCR fallback\n"
        f"   reads a stale frame when the game window is behind another application (measured\n"
        f"   2026-09-29: a session reading turn 1 through four tool calls was told `starting`). A\n"
        f"   successful `get_game_overview` is the authority - if it returns a turn, play.\n"
        f"   **Never launch the game and never load a save: both are the human's calls.**",
    ]
    if rollback:
        parts.append(
            f"   This is a **rollback, and it is deliberate**: the human loaded an earlier save\n"
            f"   (T{expected}). Do not roll forward. Do not load a later save, and do not treat a\n"
            f"   turn-regression warning or a newer autosave as a position to recover - the line\n"
            f"   that was played before this point has been abandoned on purpose."
        )
    elif (last_turn := _heartbeat_turn(facts.get("last_turn"))) is not None:
        gap = abs(last_turn - expected) if isinstance(expected, int) else None
        if gap is None:
            parts.append(
                f"   The previous session stopped at T{last_turn}. Take the position from the game,\n"
                f"   and read the diary as this run's own history."
            )
        elif gap > POSITION_LAG:
            parts.append(
                f"   The previous session stopped at T{last_turn}, and the game reports T{expected} -\n"
                f"   {gap} turns apart, so this is not the position the diary was written at. If the\n"
                f"   **lower** turn is the one loaded, a rollback happened: take the position from the\n"
                f"   game and treat the diary's plan as belonging to another branch. If the higher one\n"
                f"   is loaded, the game was played on past the session - read the diary as history,\n"
                f"   not as the plan."
            )
        else:
            parts.append(
                f"   The previous session stopped at T{last_turn}, and the game stands at T{expected}:\n"
                f"   the same position. The diary is this run's own history - read it as yours, and\n"
                f"   note that a turn or two of difference here is only the record lagging the game."
            )
    parts += [
        "0b. `get_diary` - the history you left yourself: the intent, the plans, the\n"
        "   judgements. Take the position from the game, never from the notes.",
        "1. One re-orientation read, not eleven:\n"
        "\n"
        "   ```\n"
        "   .venv\\Scripts\\python.exe scripts\\orient.py --radius 2\n"
        "   ```\n"
        "\n"
        "   **If that answers `could not connect to FireTuner`, that is expected and it is not the\n"
        "   game: your own MCP server holds the only connection, and `orient.py` opens its own.** Do\n"
        "   the same orientation through the MCP tools, which read the game over the connection that\n"
        "   already exists, and do not conclude from the script's failure that the game is\n"
        "   unreachable.\n"
        "\n"
        "   (`--maps` when the map around the cities and units is what you plan with,\n"
        "   `--only a,b` to narrow.) Three channels it does not print, and all three block the\n"
        "   turn: `get_pending_diplomacy`, `get_pending_trades`, `get_world_congress` - votes\n"
        "   must be queued with `queue_wc_votes` before `end_turn`, which fires the congress\n"
        "   synchronously.",
        "2. Read every `*.md` in `prompts/tasks/tmp/` (not `README.md`, not `current_tasks.md`,\n"
        "   not `done/`). Those files are instructions in force, each with its own `done when:`,\n"
        "   `overrides:` and `expires:`. `current_tasks.md` is the register of what is in force;\n"
        "   `docs/task-history.md` is what the retired ones measured and is not an instruction.",
        f"3. Play the turn loop - `get_game_overview`, clear whatever `end_turn` reports as a\n"
        f"   blocker, order every unit, set city production, `end_turn` - for at most {turns}\n"
        f"   turns, then stop and report. Verify state after a mutation that reports failure: a\n"
        f"   refused order can still have taken effect.",
        "Report when you stop: the turn you started at and the final turn, city count,\n"
        "population, science/culture/gold, military strength, what you built, which wars you\n"
        "fought, and every obstacle you hit with its turn number.",
    ]
    return "\n\n".join(parts) + "\n"


def write_task(
    path: str | pathlib.Path, facts: dict, result: dict, turns: int = 100, rollback: bool = False
) -> pathlib.Path:
    """Write the generated task as pure ASCII (no BOM: the agent's own reader takes UTF-8)."""
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = task_text(facts, result, turns=turns, rollback=rollback)
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


def check(probe: bool = True) -> tuple[dict, dict]:
    """Facts and verdict in one call, probing only when that is safe."""
    facts = collect_facts()
    if probe:
        facts = probe_facts(facts)
    facts["verdict"] = verdict(facts)
    return facts, facts["verdict"]


def main(argv: list[str] | None = None) -> int:
    """CLI: the report, the same as JSON, and optional task generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Can a session take this match over?")
    parser.add_argument("--json", action="store_true", help="facts and verdict as JSON")
    parser.add_argument("--task", help="write the resume task to this path")
    parser.add_argument("--turns", type=int, default=100, help="turn cap for the session")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="the human deliberately loaded an earlier save: forbid rolling forward",
    )
    parser.add_argument("--no-probe", action="store_true", help="passive only; never connect")
    parser.add_argument(
        "--after-victory",
        action="store_true",
        help="the match is won; keep playing it anyway (the human's option, 2026-10-07)",
    )
    parser.add_argument("--save", help="override the recommended save name in the report")
    args = parser.parse_args(argv)

    facts, result = check(probe=not args.no_probe)
    if args.save:
        result["save"] = args.save
    result["rollback"] = bool(args.rollback)
    result["after_victory"] = bool(args.after_victory)
    if args.task:
        path = write_task(args.task, facts, result, turns=args.turns, rollback=args.rollback)
        result["task"] = str(path)

    if args.json:
        print(json.dumps({"facts": facts, "verdict": result, "text": render(facts, result)}, ensure_ascii=False, indent=1))
    else:
        print(render(facts, result))
        if args.task:
            print(f"  TASK       {result['task']}")
    # Exit 0 means "the NEXT line can be run as it is". A loaded match with a missing
    # credential is still a handoff that cannot happen, and that is what a caller's `&&`
    # or `if ($LASTEXITCODE)` is asking about.
    return 0 if result["ready"] and not result["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
