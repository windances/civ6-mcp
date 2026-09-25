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
   re-executed on the next turn.

These tests are the guard rail on the protocol itself, not on any one task.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TMP = ROOT / "prompts" / "tasks" / "tmp"
AGENTS = ROOT / "AGENTS.md"
HEADER_FIELDS = ("added:", "expires:", "done when:", "overrides:", "scope:")


def task_files() -> list[pathlib.Path]:
    return sorted(p for p in TMP.glob("*.md") if p.name != "README.md")


def in_force_list() -> set[str]:
    """The file names under AGENTS.md's "IN FORCE NOW" line.

    The list is prose, so the shape is fixed instead: the names are backticked `*.md` on the lines
    directly below the header, the parenthetical note that follows them starts a line with `(`, and
    an empty list is the literal `(none)`.
    """
    lines = AGENTS.read_text(encoding="utf-8-sig").splitlines()
    start = next(i for i, line in enumerate(lines) if "IN FORCE NOW" in line)
    names: set[str] = set()
    for line in lines[start + 1 :]:
        if line.strip() == "(none)":
            return set()
        if not line.strip() or line.startswith("("):
            break
        found = set(re.findall(r"`([^`]+\.md)`", line))
        if not found:
            break
        names |= found
    return names


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
    it, and this was found by the suite, not by a reader). Both directions are cheap to check.
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

    def test_done_holds_no_instructions(self):
        # done/ is a record. A task file there must not be readable as an instruction, so nothing
        # in it may carry the header block.
        for path in (TMP / "done").glob("*.md"):
            if path.name == "README.md":
                continue
            text = path.read_text(encoding="utf-8-sig")
            assert "done when:" not in text or "-done-T" in path.name or "-expired-T" in path.name
