"""The temporary-task protocol: files in `prompts/tasks/tmp/`, read by the turn loop.

A temporary instruction reaches a session that is already playing either as a `once: true` rule (the
engine retires it) or as a file the turn loop reads. The file route exists for everything no metric
can express, and it only works if three things hold, each of which has burned a session before:

1. the standing text that tells the agent to look there is present in `AGENTS.md` — nothing else in
   the loop knows the directory exists;
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


class TestTheProtocolIsAdvertised:
    def test_agents_md_points_at_the_directory(self):
        text = AGENTS.read_text(encoding="utf-8")
        assert "prompts/tasks/tmp/" in text
        assert "Temporary tasks are files" in text

    def test_the_turn_loop_step_one_sends_the_agent_there(self):
        text = AGENTS.read_text(encoding="utf-8")
        loop = text.split("## Turn Loop", 1)[1].split("2. `get_units`", 1)[0]
        assert "prompts/tasks/tmp/" in loop

    def test_the_directory_documents_itself(self):
        readme = (TMP / "README.md").read_text(encoding="utf-8")
        assert "done when:" in readme
        assert "expires:" in readme
        assert "overrides:" in readme
        assert (TMP / "done" / "README.md").is_file()


class TestEveryTaskFileIsRetirable:
    def test_there_is_at_least_one_task_in_force(self):
        # The camp raid is the reason the mechanism exists; if this fails because the task was
        # legitimately retired, move the assertion, do not delete the test.
        assert task_files(), "no temporary task in force (expected the camp raid)"

    def test_each_task_file_has_the_four_header_lines_and_a_scope(self):
        for path in task_files():
            text = path.read_text(encoding="utf-8")
            for field in HEADER_FIELDS:
                assert re.search(rf"^{re.escape(field)}", text, re.MULTILINE), (
                    f"{path.name} is missing the {field!r} line"
                )

    def test_each_done_when_is_observable_rather_than_vague(self):
        # A `done when:` an agent has to argue about is a task that never retires. Require it to
        # name something the game can be queried for: a tile, an improvement, a unit, a turn.
        for path in task_files():
            text = path.read_text(encoding="utf-8")
            line = next(
                l for l in text.splitlines() if l.startswith("done when:")
            )
            assert re.search(r"\(|-?\d+,\d+|turn \d+|no longer|>=|>= ", line), (
                f"{path.name}'s done-when is not observable: {line!r}"
            )

    def test_each_expires_names_a_turn(self):
        for path in task_files():
            line = next(
                l for l in path.read_text(encoding="utf-8").splitlines()
                if l.startswith("expires:")
            )
            assert re.search(r"turn \d+", line), f"{path.name}'s expiry has no turn: {line!r}"

    def test_done_holds_no_instructions(self):
        # done/ is a record. A task file there must not be readable as an instruction, so nothing
        # in it may carry the header block.
        for path in (TMP / "done").glob("*.md"):
            if path.name == "README.md":
                continue
            text = path.read_text(encoding="utf-8")
            assert "done when:" not in text or "-done-T" in path.name or "-expired-T" in path.name
