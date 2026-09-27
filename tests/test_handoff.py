"""The handoff verdict: who has to do what, before anyone touches the game.

The failure this exists for is not a crash, it is a wrong assumption: a session that starts
against a game nobody loaded, a launch that dies on a missing credential after it has already
started the MCP, or a save chosen by filename when the filename lies (measured 2026-09-26:
``AutoSave_0142`` holds T141 while ``0_MCP_0142`` holds T142, so "the number in the name is
the turn" is only true of the MCP's own files). Every case here is decided from facts, so it
is tested without a game.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import handoff as h  # noqa: E402


def save(name: str, turn: int, family: str, mtime: float = 1_000.0) -> dict:
    return {
        "name": name,
        "path": f"C:/saves/{name}.Civ6Save",
        "family": family,
        "mtime": mtime,
        "mtime_text": "2026-09-26 04:37:50",
        "turn_from_name": int(name.rsplit("_", 1)[-1]),
        "turn": turn,
        "leader": None,
        "turn_source": "file",
    }


def inventory(*saves: dict, warning: str | None = None, notes: list[str] | None = None) -> dict:
    ordered = list(saves)
    return {
        "count": len(ordered),
        "saves": ordered,
        "newest": ordered[0] if ordered else None,
        "newest_autosave": next((s for s in ordered if s["family"] == "autosave"), None),
        "newest_mcp": next((s for s in ordered if s["family"] == "mcp"), None),
        "furthest": max(ordered, key=lambda s: s["turn"]) if ordered else None,
        "newest_is_furthest": True,
        "name_lag": {},
        "notes": notes or [],
        "warning": warning,
    }


def facts(
    *,
    running: bool = True,
    probe: dict | None = None,
    listening: bool = True,
    foreign_clients: list[int] | None = None,
    other_session: str | None = None,
    saves: dict | None = None,
    credential: bool = True,
    last_turn: int | None = 142,
    heartbeat: dict | None = None,
) -> dict:
    default_saves = inventory(
        save("0_MCP_0142", 142, "mcp"), save("AutoSave_0142", 141, "autosave")
    )
    return {
        "checked_at": "2026-09-26 13:00:00",
        "civ": "china",
        "seed": -1894041591,
        "run_id": "twilight-indigo-pinnacle-52",
        "last_turn": last_turn,
        "heartbeat": heartbeat
        if heartbeat is not None
        else {"phase": "playing", "turn": last_turn, "pid": 49364, "age_seconds": 27_000.0, "pid_alive": False},
        "game": {"running": running, "pids": [50144] if running else []},
        "window": {"pid": 50144, "title": "Sid Meier's Civilization VI (DX12)"} if running else None,
        "tuner": {
            "listening": listening,
            "clients": [],
            "foreign_clients": foreign_clients or [],
            "note": "",
        },
        "other_session": other_session,
        "probe": probe,
        "saves": saves if saves is not None else default_saves,
        "credential": {
            "present": credential,
            "variable": "DEEPSEEK_API_KEY",
            "project_home_has_store": False,
            "global_store_exists": True,
            "note": "" if credential else "DEEPSEEK_API_KEY is not set ... MISSING_CREDENTIAL",
        },
    }


class TestVerdict:
    def test_in_game_is_ready_and_reports_the_turn(self):
        result = h.verdict(facts(probe={"connected": True, "ingame": True, "turn": 142}))
        assert result["state"] == h.IN_GAME
        assert result["ready"] is True
        assert result["turn"] == 142
        assert result["needs"] == []

    def test_not_running_names_the_save_to_load_after_launching(self):
        result = h.verdict(facts(running=False, probe=None, listening=False))
        assert result["state"] == h.NOT_RUNNING
        assert result["ready"] is False
        assert any("launch" in need for need in result["needs"])
        assert any("0_MCP_0142" in need for need in result["needs"])

    def test_a_running_game_with_no_match_asks_for_a_load(self):
        result = h.verdict(facts(probe={"connected": True, "ingame": False, "turn": None}))
        assert result["state"] == h.NO_MATCH
        assert result["ready"] is False
        assert any("load a save" in need for need in result["needs"])

    def test_an_unprobed_game_is_not_reported_as_ready(self):
        # "Not probed" is not "no match": the verdict must not promise a handoff it cannot
        # confirm, and it must not tell the human to load over a game that may be loaded.
        result = h.verdict(facts(probe=None))
        assert result["state"] == h.NO_MATCH
        assert result["ready"] is False

    def test_a_foreign_tuner_client_stops_the_handoff(self):
        result = h.verdict(
            facts(
                probe={"connected": True, "ingame": True, "turn": 142},
                foreign_clients=[23276],
                other_session="pid 23276 holds the FireTuner connection",
            )
        )
        assert result["state"] == h.TUNER_BUSY
        assert result["ready"] is False
        assert any("civ6-clean" in need for need in result["needs"])

    def test_a_game_without_the_tuner_is_its_own_state(self):
        # Started outside the MCP: EnableTuner is off. Restarting is the fix, and it is not
        # the same advice as "load a save".
        result = h.verdict(facts(listening=False, probe=None))
        assert result["state"] == h.TUNER_SILENT
        assert result["ready"] is False

    def test_a_missing_credential_is_a_blocker_not_a_state(self):
        # The game is ready; the launch is not. Keeping these apart is what stops the
        # session from starting the MCP and dying seconds later.
        result = h.verdict(facts(probe={"connected": True, "ingame": True, "turn": 142}, credential=False))
        assert result["state"] == h.IN_GAME
        assert result["ready"] is True
        assert result["blockers"] and "MISSING_CREDENTIAL" in result["blockers"][0]

    def test_a_turn_that_disagrees_with_the_diary_is_flagged(self):
        result = h.verdict(
            facts(probe={"connected": True, "ingame": True, "turn": 150}, last_turn=142)
        )
        assert result["ready"] is True
        assert any("T142" in note and "T150" in note for note in result["warnings"])

    def test_a_heartbeat_turn_that_is_not_a_number_is_unknown_not_a_crash(self):
        # The measured failure of 2026-09-28: server.py wrote the log line's "?" placeholder into
        # the heartbeat, this verdict did int("?") on it, and scripts/resume-game.ps1 died with a
        # traceback before printing the report it exists to print.
        result = h.verdict(
            facts(probe={"connected": True, "ingame": True, "turn": 142}, last_turn="?")
        )
        assert result["ready"] is True
        assert result["turn"] == 142
        assert result["warnings"] == [], "a heartbeat that names no turn cannot disagree with one"

    def test_the_newest_save_is_the_one_continue_game_would_load(self):
        saves = inventory(
            save("AutoSave_0150", 149, "autosave", mtime=2_000.0),
            save("0_MCP_0142", 142, "mcp", mtime=1_000.0),
        )
        result = h.verdict(facts(running=False, probe=None, listening=False, saves=saves))
        assert result["save"] == "AutoSave_0150"

    def test_a_save_warning_reaches_the_verdict(self):
        saves = inventory(save("0_MCP_0142", 142, "mcp"), warning="the newest save is not the furthest")
        result = h.verdict(facts(probe=None, saves=saves))
        assert result["warnings"] == ["the newest save is not the furthest"]


class TestProbeSafety:
    def test_the_probe_is_skipped_when_a_session_holds_the_tuner(self):
        assert h._probe_allowed(facts(other_session="pid 23276 holds the FireTuner connection")) is False

    def test_the_probe_is_skipped_when_a_foreign_client_is_connected(self):
        assert h._probe_allowed(facts(foreign_clients=[23276])) is False

    def test_the_probe_is_skipped_when_nothing_is_listening(self):
        assert h._probe_allowed(facts(listening=False)) is False

    def test_the_probe_runs_on_a_free_tuner(self):
        assert h._probe_allowed(facts()) is True


class TestTaskText:
    def test_it_carries_the_facts_and_the_cap(self):
        f = facts(probe={"connected": True, "ingame": True, "turn": 142})
        text = h.task_text(f, h.verdict(f), turns=30)
        assert "turn 142" in text
        assert "at most 30" in text
        assert "Never launch the game and never load a save" in text
        assert "scripts\\orient.py" in text
        assert "prompts/tasks/tmp/" in text

    def test_the_position_warning_only_appears_when_there_is_a_previous_turn(self):
        with_history = h.task_text(facts(), h.verdict(facts(probe={"connected": True, "ingame": True, "turn": 142})))
        without = h.task_text(
            facts(last_turn=None), h.verdict(facts(last_turn=None, probe={"connected": True, "ingame": True, "turn": 142}))
        )
        assert "The previous session stopped at T142" in with_history
        assert "previous session stopped at" not in without

    def test_the_reorientation_is_one_command_not_a_list_of_tools(self):
        f = facts(probe={"connected": True, "ingame": True, "turn": 142})
        text = h.task_text(f, h.verdict(f))
        assert "not eleven" in text
        assert "get_tech_civics" not in text, "the hand-rolled read list is exactly what drifted"
        assert "get_world_congress" in text, "the three channels orient.py cannot print stay"


class TestReport:
    def test_the_report_names_the_state_and_the_next_step(self):
        f = facts(probe={"connected": True, "ingame": True, "turn": 142})
        text = h.render(f, h.verdict(f))
        assert "VERDICT    IN_GAME, T142" in text
        assert "resume-game.ps1" in text
        assert "SAVE       0_MCP_0142" in text

    def test_the_report_says_what_is_blocking_a_ready_game(self):
        f = facts(probe={"connected": True, "ingame": True, "turn": 142}, credential=False)
        text = h.render(f, h.verdict(f))
        assert "BLOCKED" in text
        assert "fix the blocker above" in text

    def test_a_heartbeat_without_a_turn_is_reported_as_unknown(self):
        # The file can hold the log line's "?" (written before 2026-09-28): the report says so in
        # words, and never prints a placeholder as if it were a turn.
        f = facts(probe={"connected": True, "ingame": True, "turn": 142}, last_turn="?")
        text = h.render(f, h.verdict(f))
        assert "turn unknown" in text
        assert "T?" not in text
        assert "VERDICT    IN_GAME, T142" in text
