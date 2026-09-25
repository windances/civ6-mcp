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

import pytest

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


@pytest.fixture()
def scratch():
    """A scratch tree under `.tools/`: pytest's temp factory is not writable here."""
    import shutil
    import uuid

    root = ROOT / ".tools" / f"_rollback_test_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    yield root
    shutil.rmtree(root, ignore_errors=True)


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


class TestArchiveReuse:
    """An archive may be reused only when it holds the same saves, not merely the same turns.

    Reuse keys on the target turn and the span archived, and two different branches can share
    both. Measured 2026-09-25: a second rollback to T99 re-used the previous folder, and because
    those turns had been replayed in between, the earlier branch's T100-T117 autosaves existed
    only inside that archive — the live directory had already been rewritten by the new branch.
    Reusing the folder replaced them.
    """

    def archived(self, root: pathlib.Path, name: str, size: int, mtime: float) -> pathlib.Path:
        import os

        saves = root / "rollback-to-T99-from-T100-T117-20260925-111836" / "saves"
        saves.mkdir(parents=True, exist_ok=True)
        copied = saves / f"{name}.Civ6Save"
        copied.write_bytes(b"x" * size)
        os.utime(copied, (mtime, mtime))
        return saves.parent

    def test_the_same_saves_may_be_reused(self, scratch):
        archive = self.archived(scratch, "AutoSave_0100", 1, 100.0)
        assert rb._archive_can_absorb(archive, [save("AutoSave_0100", 100, mtime=100.0)]) is True

    def test_a_save_of_the_same_name_but_other_content_is_not_absorbed(self, scratch):
        archive = self.archived(scratch, "AutoSave_0100", 8, 100.0)
        future = [dict(save("AutoSave_0100", 100, mtime=100.0), bytes=9)]
        assert rb._archive_can_absorb(archive, future) is False

    def test_the_same_size_written_at_another_time_is_not_absorbed(self, scratch):
        # A replay produces files that can match in size; the write time is what separates a
        # replayed turn from the archived copy of the original one.
        archive = self.archived(scratch, "AutoSave_0100", 1, 100.0)
        assert rb._archive_can_absorb(archive, [save("AutoSave_0100", 100, mtime=555.0)]) is False

    def test_a_save_the_archive_does_not_have_yet_is_absorbed(self, scratch):
        archive = self.archived(scratch, "AutoSave_0100", 1, 100.0)
        assert rb._archive_can_absorb(archive, [save("AutoSave_0101", 101, mtime=1.0)]) is True

    def test_an_empty_future_absorbs(self, scratch):
        assert rb._archive_can_absorb(scratch, []) is True


class TestRestoringRetiredGoals:
    """A rollback has to un-retire the rules the abandoned branch achieved.

    A ``once: true`` goal is removed from `prompts/checks/turn-checks.md` when it is met, with a
    comment naming the archived copy. Behind that turn the rule must come back: it is a
    directive the target position is supposed to be following, and once retired no later turn
    re-checks it.
    """

    BLOCK = (
        "<!-- check\n"
        "id: ram-tower-before-civil-engineering\n"
        "when: not researched(CIVIC_CIVIL_ENGINEERING)\n"
        "require: units(BATTERING_RAM, SIEGE_TOWER) >= 1\n"
        "message: no ram yet\n"
        "once: true\n"
        "-->"
    )

    @pytest.fixture()
    def checks(self, scratch, monkeypatch):
        """A scratch check file with the goal already retired, and its archived original."""
        checks = scratch / "turn-checks.md"
        archive = scratch / "archive" / "turn-checks-20260925-145233.md"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(
            "# Rules\n\n" + self.BLOCK + "\n\n## Next\n\nSomething else.\n", encoding="utf-8"
        )
        checks.write_text(
            "# Rules\n\n"
            "<!-- achieved T100: ram-tower-before-civil-engineering "
            "(original in archive/turn-checks-20260925-145233.md) -->\n\n"
            "## Next\n\nSomething else.\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(rb, "CHECKS_FILE", checks)
        return checks

    def test_a_goal_achieved_after_the_target_comes_back(self, checks):
        restored = rb.restore_achieved_goals(99)
        assert restored and "ram-tower-before-civil-engineering" in restored[0]
        text = checks.read_text(encoding="utf-8")
        assert "id: ram-tower-before-civil-engineering" in text
        assert "require: units(BATTERING_RAM, SIEGE_TOWER) >= 1" in text
        assert "achieved T100" not in text

    def test_nothing_else_in_the_file_moves(self, checks):
        before = checks.read_text(encoding="utf-8").splitlines()
        rb.restore_achieved_goals(99)
        after = checks.read_text(encoding="utf-8").splitlines()
        assert "# Rules" in after and "## Next" in after and "Something else." in after
        assert len(after) == len(before) - 1 + len(self.BLOCK.splitlines())

    def test_a_goal_achieved_before_the_target_stays_retired(self, checks):
        # Rolling back to T100 or later is not rolling back behind the achievement: a rule
        # retired at T100 is legitimately retired at T100.
        assert rb.restore_achieved_goals(100) == []
        assert "achieved T100" in checks.read_text(encoding="utf-8")

    def test_a_dry_run_reports_without_writing(self, checks):
        restored = rb.restore_achieved_goals(99, apply=False)
        assert restored
        assert "achieved T100" in checks.read_text(encoding="utf-8")

    def test_a_missing_archive_leaves_the_file_alone(self, checks):
        (checks.parent / "archive" / "turn-checks-20260925-145233.md").unlink()
        assert rb.restore_achieved_goals(99) == []
        assert "achieved T100" in checks.read_text(encoding="utf-8")

    def test_the_block_is_found_by_id_not_by_position(self, scratch):
        archive = scratch / "old.md"
        archive.write_text(
            "<!-- check\nid: something-else\n-->\n\n" + self.BLOCK + "\n", encoding="utf-8"
        )
        block = rb.check_block(archive, "ram-tower-before-civil-engineering")
        assert block is not None and "id: ram-tower-before-civil-engineering" in block
        assert "something-else" not in block


class TestTheLoadTheRollbackIssues:
    """The rollback's load must go through the adapter, not straight to the OCR half.

    `game_launcher.load_save_from_menu` is the OCR navigation on its own: it needs the game
    window in the foreground and clicks a screen grab of it, which is the path that failed three
    times while rolling back one save on 2026-09-25. `game_lifecycle.load_game_save` reaches the
    main menu's own load screen over Lua and lands the load, and falls back to that OCR
    navigation itself when the game's save list does not carry the name.
    """

    def test_the_menu_load_goes_through_the_adapter(self, monkeypatch):
        import asyncio

        from civ_mcp import connection as connection_module
        from civ_mcp import game_lifecycle as lifecycle

        asked: list[str] = []

        class FakeConnection:
            def __init__(self, *args, **kwargs):
                pass

            async def connect(self):
                return None

            async def disconnect(self):
                asked.append("disconnected")

        async def fake_load(conn, name):
            asked.append(name)
            return f"Loading save: {name} (issued from the LoadGameMenu Lua state)."

        monkeypatch.setattr(connection_module, "GameConnection", FakeConnection)
        monkeypatch.setattr(lifecycle, "load_game_save", fake_load)

        result = asyncio.run(rb.apply_plan("load-from-menu", "AutoSave_0099", 99, False))
        assert asked[0] == "AutoSave_0099"
        assert "disconnected" in asked, "the connection is closed even on success"
        assert "LoadGameMenu" in result

    def test_a_hang_still_restarts_and_loads(self, monkeypatch):
        import asyncio

        called: list[tuple] = []

        async def fake_restart(name, force=False):
            called.append((name, force))
            return "restarted"

        monkeypatch.setattr(rb.gl, "restart_and_load", fake_restart)
        assert asyncio.run(rb.apply_plan("restart-and-load", "AutoSave_0099", 99, True)) == "restarted"
        assert called == [("AutoSave_0099", True)]
