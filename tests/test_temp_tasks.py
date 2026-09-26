"""The temporary-task protocol: files in `prompts/tasks/tmp/`, read by the turn loop.

A temporary instruction reaches a session that is already playing either as a `once: true` rule (the
engine retires it) or as a file the turn loop reads. The file route exists for everything no metric
can express, and it only works if three things hold, each of which has burned a session before:

1. the standing text that tells the agent to look there is present in `AGENTS.md` — nothing else in
   the loop knows the directory exists — and the names it lists as **in force** are exactly the files
   that are in the directory;
2. every task file carries the four header lines (`added:`, `expires:`, `done when:`, `overrides:`)
   plus `scope:`, because that is what lets an agent start a task, know when it is finished, and
   retire it without asking;
3. the retirement is a **move** out of the directory (`done/`), so a finished task cannot be
   re-executed on the next turn;
4. `AGENTS.md` itself stays the **procedure**: since 2026-09-26 the section says how to find the tasks,
   how to read one, how to tell which are in force and where the detail lives, and names no task's
   content or retirement outside the single `IN FORCE NOW` line — the live status is
   `prompts/tasks/tmp/current_tasks.md` and the history is `docs/task-history.md`. A task's status
   written into `AGENTS.md` is a line that goes stale in the one file that is re-injected whole on
   every change (measured: 6 re-injections of 55-61 KB in one session drove it to stop after 4 turns).

These tests are the guard rail on the protocol itself, not on any one task.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TMP = ROOT / "prompts" / "tasks" / "tmp"
AGENTS = ROOT / "AGENTS.md"
REGISTER = TMP / "current_tasks.md"
DATA = ROOT / ".civ6-mcp-data"
HEADER_FIELDS = ("added:", "expires:", "done when:", "overrides:", "scope:")
# Neither of these is a task: `README.md` documents the directory, `current_tasks.md` is the register.
NON_TASKS = frozenset({"README.md", "current_tasks.md"})


def task_files() -> list[pathlib.Path]:
    return sorted(p for p in TMP.glob("*.md") if p.name not in NON_TASKS)


def expires_turn(path: pathlib.Path) -> int | None:
    """The turn this task's `expires:` names, or None when the line is unreadable."""
    line = next(
        (l for l in path.read_text(encoding="utf-8-sig").splitlines() if l.startswith("expires:")),
        "",
    )
    found = re.search(r"turn (\d+)", line)
    return int(found.group(1)) if found else None


def game_turn() -> int | None:
    """The turn the game stands on, read offline - the clock an expiry has to be compared with.

    The **newest save by mtime** leads, because the saves are the only record that keeps moving while a
    human plays with no session attached - which is exactly the window in which an expiry goes
    unnoticed (016 sat in the directory from T191 to T193 with `expires: turn 190`). The two save
    families are named for different turns: `0_MCP_NNNN` holds turn NNNN, and `AutoSave_NNNN` holds
    NNNN - 1 (measured 2026-09-26), so each name is read for the turn it actually holds.

    The heartbeat and the diary are the fallbacks, and they are deliberately not consulted when a save
    is available: both are written *by a session*, so after a rollback they can name a turn the game
    has left behind and would report a live task as expired.
    """
    try:
        from civ_mcp import game_launcher as gl  # noqa: PLC0415

        saves = []
        for directory in (gl.SAVE_DIR, gl.SINGLE_SAVE_DIR):
            for path in pathlib.Path(directory).glob("*.Civ6Save"):
                found = re.match(r"(0_MCP_|AutoSave_)(\d+)", path.name)
                if found:
                    number = int(found.group(2))
                    turn = number if found.group(1) == "0_MCP_" else number - 1
                    saves.append((path.stat().st_mtime, turn))
        if saves:
            return max(saves)[1]
    except Exception:  # a fresh clone has no game install, and that is not a failure
        pass

    heartbeat = DATA / "heartbeat.json"
    if heartbeat.exists():
        try:
            turn = json.loads(heartbeat.read_text(encoding="utf-8-sig")).get("turn")
            if isinstance(turn, int) and turn > 0:
                return turn
        except (OSError, ValueError):
            pass

    # The newest diary by mtime is this checkout's live game; an older seed's diary can name a higher
    # turn than the current match, so the others are not consulted.
    diaries = sorted(DATA.glob("diary_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    for diary in diaries[:1]:
        tail = diary.read_bytes()[-200_000:].decode("utf-8", errors="replace")
        turns = [int(n) for n in re.findall(r'"turn":\s*(\d+)', tail)]
        if turns:
            return max(turns)
    return None


def named_tasks(text: str) -> set[str]:
    """Every backticked `NNN-*.md` name in `text`, which is how a task is written down anywhere."""
    return set(re.findall(r"`(\d{3}-[^`]+\.md)`", text))


def in_force_list() -> set[str]:
    """The file names on AGENTS.md's "IN FORCE NOW" line.

    That line is the one-line channel that tells a running session a task file has arrived, so its
    shape is fixed: the names are backticked `*.md` on the line itself (the list may continue on the
    lines directly below it), and an empty list is written as `none` (however it is emphasised), which
    is the state a fully retired directory is in. `README.md` and `current_tasks.md` are never tasks.
    """
    lines = AGENTS.read_text(encoding="utf-8-sig").splitlines()
    start = next(i for i, line in enumerate(lines) if "IN FORCE NOW" in line)

    def names_on(line: str) -> set[str]:
        if line.strip().strip("*_` ").lower().startswith("none"):
            return set()
        return {n for n in re.findall(r"`([^`]+\.md)`", line) if n not in NON_TASKS}

    names = names_on(lines[start])
    # The list may continue on the lines directly below the header whether or not the header itself
    # carried names - a long list is allowed to wrap, and only the following blank line ends it.
    for line in lines[start + 1:]:
        if not line.strip() or line.startswith("("):
            break
        found = names_on(line)
        if not found:
            break
        names |= found
    return names


def register_list() -> set[str]:
    """The task names in `current_tasks.md`, the live register of what is in force."""
    return named_tasks(REGISTER.read_text(encoding="utf-8-sig"))


class TestTheProtocolIsAdvertised:
    def test_agents_md_points_at_the_directory(self):
        text = AGENTS.read_text(encoding="utf-8-sig")
        assert "prompts/tasks/tmp/" in text
        assert "Temporary tasks are files" in text

    def test_the_turn_loop_step_one_sends_the_agent_there(self):
        text = AGENTS.read_text(encoding="utf-8-sig")
        loop = text.split("## Turn Loop", 1)[1].split("2. `get_units`", 1)[0]
        assert "prompts/tasks/tmp/" in loop

    def test_the_directory_documents_itself(self):
        readme = (TMP / "README.md").read_text(encoding="utf-8-sig")
        assert "done when:" in readme
        assert "expires:" in readme
        assert "overrides:" in readme
        assert (TMP / "done" / "README.md").is_file()


class TestTheListAndTheDirectoryAgree:
    """`AGENTS.md` names what is in force; the directory is what is actually in force.

    The list is the channel, not decoration: a file dropped into `prompts/tasks/tmp/` while a session
    is playing reaches that session only when the list names it (003 and 004 sat unread for five turns
    until it did), and a file retired *without* editing the list is an instruction that never dies
    (measured T95: `002-focus-fire-scouts` was moved to `done/` as expired while the list still named
    it, and this was found by the suite, not by a reader). Both directions are cheap to check, and the
    register in the directory is a third place the same fact is written down.
    """

    def test_the_in_force_list_is_exactly_the_directory(self):
        listed = in_force_list()
        on_disk = {path.name for path in task_files()}
        assert listed == on_disk, (
            "AGENTS.md's IN FORCE NOW list and prompts/tasks/tmp/ disagree: "
            f"listed but not on disk: {sorted(listed - on_disk)}; "
            f"on disk but not listed: {sorted(on_disk - listed)}. "
            "Update the list in the same commit that adds or retires a task."
        )

    def test_the_register_is_exactly_the_directory(self):
        registered = register_list()
        on_disk = {path.name for path in task_files()}
        assert registered == on_disk, (
            "prompts/tasks/tmp/current_tasks.md and the directory disagree: "
            f"registered but not on disk: {sorted(registered - on_disk)}; "
            f"on disk but not registered: {sorted(on_disk - registered)}. "
            "The register is maintained in the same commit that adds or retires a task."
        )

    def test_agents_md_names_no_task_outside_the_in_force_line(self):
        """The section is the procedure; status and history live in the directory.

        A task's content or retirement written into `AGENTS.md` is status in the one file that is
        re-injected whole every time it changes, and it is what the 2026-09-26 split moved out: the
        live register is `current_tasks.md` and the record is `docs/task-history.md`.
        """
        lines = AGENTS.read_text(encoding="utf-8-sig").splitlines()
        start = next(i for i, line in enumerate(lines) if "IN FORCE NOW" in line)
        offenders = [
            (number, line.strip())
            for number, line in enumerate(lines, start=1)
            if number != start + 1 and named_tasks(line)
        ]
        assert not offenders, (
            "AGENTS.md names a temporary task outside its IN FORCE NOW line: "
            + "; ".join(f"line {n}: {text[:80]}" for n, text in offenders)
        )

    def test_the_history_doc_is_a_record_and_not_an_instruction(self):
        """The prose that left `AGENTS.md` is kept, and kept clearly out of force."""
        history = (ROOT / "docs" / "task-history.md").read_text(encoding="utf-8-sig")
        assert "not an instruction" in history
        assert named_tasks(history)          # the retired tasks are still written down somewhere
        assert "current_tasks.md" in history  # and it points at where the live status is


class TestEveryTaskFileIsRetirable:
    def test_each_task_file_has_the_four_header_lines_and_a_scope(self):
        for path in task_files():
            text = path.read_text(encoding="utf-8-sig")
            for field in HEADER_FIELDS:
                assert re.search(rf"^{re.escape(field)}", text, re.MULTILINE), (
                    f"{path.name} is missing the {field!r} line"
                )

    def test_each_done_when_is_observable_rather_than_vague(self):
        # A `done when:` an agent has to argue about is a task that never retires. Require it to
        # name something the game can be queried for: a tile, an improvement, a unit, a turn, or a
        # distance/count that the scans can answer.
        observable = re.compile(
            r"\(|-?\d+,\d+|turn \d+|no longer|>=|count ==|within \d+ tiles?|no hostile"
        )
        for path in task_files():
            text = path.read_text(encoding="utf-8-sig")
            line = next(l for l in text.splitlines() if l.startswith("done when:"))
            assert observable.search(line), (
                f"{path.name}'s done-when is not observable: {line!r}"
            )

    def test_each_expires_names_a_turn(self):
        for path in task_files():
            line = next(
                l for l in path.read_text(encoding="utf-8-sig").splitlines()
                if l.startswith("expires:")
            )
            assert re.search(r"turn \d+", line), f"{path.name}'s expiry has no turn: {line!r}"

    def test_no_task_in_the_directory_is_past_its_expiry(self):
        """An expired task left behind is an instruction that never retires.

        Measured 2026-09-27: 016's `expires:` was `turn 190` and the game reached T193 before anyone
        moved it, and **the other tests in this class were all green** - the list, the register and the
        directory agreed with each other perfectly, because none of them knows what turn it is. This is
        the clock, and it is offline: the newest save names the turn.
        """
        turn = game_turn()
        if turn is None:
            pytest.skip("no save, heartbeat or diary to read a turn from")
        late = [
            (path.name, expiry)
            for path in task_files()
            if (expiry := expires_turn(path)) is not None and expiry < turn
        ]
        assert not late, (
            f"the game is on turn {turn} and these files are past their expiry: "
            + "; ".join(f"{name} (expires turn {n})" for name, n in late)
            + ". Retire each one in the turn it ends: move it to `done/` as `-expired-T<turn>.md`, or as"
            " `-done-T<turn>.md` when its `done when:` holds, update `IN FORCE NOW` and"
            " `current_tasks.md` in the same commit, and record the turn in the diary's `tooling` line."
        )

    def test_done_holds_no_instructions(self):
        # done/ is a record. A task file there must not be readable as an instruction, so nothing
        # in it may carry the header block.
        for path in (TMP / "done").glob("*.md"):
            if path.name == "README.md":
                continue
            text = path.read_text(encoding="utf-8-sig")
            assert "done when:" not in text or "-done-T" in path.name or "-expired-T" in path.name
