"""The rollback script's decision logic.

The script itself is an operator tool, but the part worth pinning is the decision: which
restart a given game state calls for. Getting it wrong is expensive in a specific way - a
bare load against a game in progress waits out its timeouts and then reports a failure for a
healthy game (the launcher refuses it for that reason), while a game already at the main menu
needs no restart at all.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "rollback_to_turn", ROOT / "scripts" / "rollback-to-turn.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["rollback_to_turn"] = module
    spec.loader.exec_module(module)
    return module


rb = load_module()


def state(**over) -> dict:
    base = {
        "running": True,
        "pids": [1234],
        "other_session": None,
        "turn": 80,
        "tuner": True,
        "newest_save": "0_MCP_0080",
    }
    base.update(over)
    return base


def save(name: str, turn: int | None, directory: str = "mcp", mtime: float = 1.0) -> dict:
    return {
        "path": pathlib.Path(f"/tmp/{name}.Civ6Save"),
        "name": name,
        "dir": directory,
        "turn": turn,
        "bytes": 1,
        "mtime": mtime,
    }


ENTRY = save("0_MCP_0059", 59)


class TestTheDecision:
    def test_another_session_means_refuse(self):
        action, reason = rb.decide(state(other_session="pid 4242 holds the tuner"), 59, ENTRY)
        assert action == "refuse"
        assert "4242" in reason

    def test_a_missing_save_means_refuse(self):
        action, reason = rb.decide(state(), 59, None)
        assert action == "refuse" and "no save" in reason

    def test_a_stopped_game_is_launched_first(self):
        action, _ = rb.decide(state(running=False, turn=None), 59, ENTRY)
        assert action == "launch-then-load"

    def test_a_game_at_the_menu_needs_no_restart(self):
        # Running with no match loaded means the main menu is on screen: the cheap path.
        action, _ = rb.decide(state(turn=None), 59, ENTRY)
        assert action == "load-from-menu"

    def test_a_game_in_progress_needs_a_restart(self):
        action, reason = rb.decide(state(turn=80), 59, ENTRY)
        assert action == "restart-and-load"
        assert "main menu is not on screen" in reason

    def test_being_at_the_target_is_done(self):
        action, _ = rb.decide(state(turn=59), 59, ENTRY)
        assert action == "already-there"

    def test_a_later_target_is_not_a_rollback(self):
        action, reason = rb.decide(state(turn=40), 59, ENTRY)
        assert action == "refuse"
        assert "not a rollback" in reason

    def test_refusal_beats_everything_else(self):
        # Even with no save and no game, another session stops the script: it is the only
        # condition that can destroy someone else's work.
        action, _ = rb.decide(
            state(other_session="pid 1 wrote a playing heartbeat", running=False, turn=None),
            59,
            None,
        )
        assert action == "refuse"


class TestTargetSelection:
    def test_the_save_for_the_turn_is_chosen(self):
        saves = [save("AutoSave_0059", 59, "game"), save("0_MCP_0059", 59, "mcp")]
        assert rb.pick_target(saves, 59)["name"] == "0_MCP_0059", "ours is preferred"

    def test_an_explicit_name_wins(self):
        saves = [save("0_MCP_0059", 59), save("0A_GROUND_CONTROL", None)]
        picked = rb.pick_target(saves, 59, "0A_GROUND_CONTROL")
        assert picked["name"] == "0A_GROUND_CONTROL"

    def test_an_explicit_name_may_carry_the_extension(self):
        saves = [save("0A_GROUND_CONTROL", None)]
        assert rb.pick_target(saves, 59, "0A_GROUND_CONTROL.Civ6Save") is not None

    def test_the_game_own_autosave_is_the_fallback(self):
        saves = [save("AutoSave_0077", 77, "game")]
        assert rb.pick_target(saves, 77)["name"] == "AutoSave_0077"

    def test_nothing_for_that_turn_is_none(self):
        assert rb.pick_target([save("0_MCP_0060", 60)], 59) is None


class TestCandidateListing:
    def test_numbered_saves_come_first_nearest_to_the_target(self):
        saves = [
            save("0_MCP_0100", 100),
            save("0_MCP_0061", 61),
            save("0A_GROUND_CONTROL", None),
        ]
        names = [s["name"] for s in rb.candidates(saves, 60, limit=3)]
        assert names[0] == "0_MCP_0061"
        assert names[-1] == "0A_GROUND_CONTROL", "a named save has no turn to rank by"

    def test_the_limit_is_respected(self):
        saves = [save(f"0_MCP_{n:04d}", n) for n in range(50, 70)]
        assert len(rb.candidates(saves, 60, limit=5)) == 5
