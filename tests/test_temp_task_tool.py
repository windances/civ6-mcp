"""`scripts/temp-task.py` and `civ_mcp.temp_tasks` - the protocol's mechanical half.

The **authority** on the protocol is `tests/test_temp_tasks.py`; these tests check that the tool writes
what that suite demands. Two of them are drift guards rather than behaviour tests: the observable
`done when:` pattern is asserted to be character-for-character the suite's, and the `IN FORCE NOW`
parser is asserted to read back exactly the names the writer produced.

The fixture is built under the checkout's `.tmp/` rather than pytest's `tmp_path`, for the reason
`test_temp_tasks.py` records: the sandbox this suite runs in refuses to create or remove `.pytest-tmp`.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import temp_tasks as tt  # noqa: E402


def _load_cli():
    """`scripts/temp-task.py` has a dash in its name, so it is loaded by path, not imported."""
    spec = importlib.util.spec_from_file_location("temp_task_cli", ROOT / "scripts" / "temp-task.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _load_cli()

SCRATCH = ROOT / ".tmp" / "temp-task-fixture"
FIXTURE_TURN = 30

AGENTS_STUB = """# Reference

## Temporary tasks are files

**IN FORCE NOW:** `001-first-task.md` (a first task; expires turn 10).

Prose below the line, which must survive.
"""

REGISTER_STUB = """# The live register

| task file | added | expires | why it exists, in one line | done when (first line) |
|---|---|---|---|---|
| `001-first-task.md` | 2026-01-01 | turn 10 | a first task (expires turn 10) | the tile at (1,2) reads ours |

Notes below the table.
"""

TASK_STUB = """# TEMP TASK 001 - a first task

added:     2026-01-01 (human instruction: do the first thing)
expires:   turn 10 - a hard stop
done when: the tile at (1,2) reads `[CITY_CENTER]` owned by us with a unit on it
overrides: nothing
scope:     the first thing

Body.
"""

SECOND_NAME = "002-second-task-do-the-second-thing.md"
CN_NAME = "002-second-task-do-the-second-thing.cn.md"
CN_DRAFT = """# 临时任务 002 - 做第二件事

这是第二件事的中文版，仅供人阅读：它说明这个任务要做什么、什么时候算完成。
"""

ADD_ARGS = [
    "add",
    "--title", "second task: do the second thing",
    "--instruction", "做第二件事（中文指令）",
    "--why", "a second task, on the human's instruction",
    "--done-when", "the tile at (3,4) reads CITY_CENTER owned by us, or turn 40",
    "--overrides", "the development plan, for this one slot",
    "--scope", "the second thing and nothing else",
    "--expires-turn", "40",
    "--cn", f"@{SCRATCH / 'cn-draft.md'}",   # the Chinese version every publish carries
    "--no-gate",
    "--no-commit",
]


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch) -> int:
    """The scratch tree has no saves, and the real ones would leak the live game's turn in here."""
    monkeypatch.setattr(tt, "game_turn", lambda root: (FIXTURE_TURN, "fixture"))
    return FIXTURE_TURN


@pytest.fixture()
def scratch() -> pathlib.Path:
    shutil.rmtree(SCRATCH, ignore_errors=True)
    tmp = SCRATCH / "prompts" / "tasks" / "tmp"
    (tmp / "done").mkdir(parents=True)
    (SCRATCH / ".civ6-mcp-data").mkdir(parents=True)
    (SCRATCH / "AGENTS.md").write_text(AGENTS_STUB, encoding="utf-8")
    (tmp / "README.md").write_text("# readme\n", encoding="utf-8")
    (tmp / "current_tasks.md").write_text(REGISTER_STUB, encoding="utf-8")
    (tmp / "001-first-task.md").write_text(TASK_STUB, encoding="utf-8")
    (tmp / "done" / "README.md").write_text("# retired\n", encoding="utf-8")
    (SCRATCH / "cn-draft.md").write_text(CN_DRAFT, encoding="utf-8")
    return SCRATCH


class TestTheProtocolRulesAreMirrored:
    def test_the_observable_pattern_is_the_suites_own(self):
        source = (ROOT / "tests" / "test_temp_tasks.py").read_text(encoding="utf-8")
        assert tt.OBSERVABLE.pattern in source, (
            "civ_mcp.temp_tasks.OBSERVABLE has drifted from the regex in tests/test_temp_tasks.py"
        )

    def test_header_fields_are_the_suites_own(self):
        source = (ROOT / "tests" / "test_temp_tasks.py").read_text(encoding="utf-8")
        for field in tt.HEADER_FIELDS:
            assert f'"{field}"' in source or f"'{field}'" in source


class TestRendering:
    def test_slugify(self):
        assert tt.slugify("Take Brussels: pre-war analysis!") == "take-brussels-pre-war-analysis"
        assert tt.slugify("占领布鲁塞尔") == ""
        assert tt.slugify("019 two scouts  to sea") == "019-two-scouts-to-sea"

    def test_next_number_spans_tmp_and_done(self, scratch):
        tmp, done, _, _ = tt.root_paths(scratch)
        assert tt.next_number(tmp, done) == 2
        (done / "007-old-done-T80.md").write_text("x", encoding="utf-8")
        assert tt.next_number(tmp, done) == 8

    def test_headers_start_at_column_zero_with_indented_continuations(self):
        block = tt.header_block(
            "2026-01-01 (human instruction: x)",
            "turn 40 - a hard stop",
            "the tile at (3,4) reads ours " + "and many more words " * 20,
            "overrides: a lot " * 20,
            "scope " * 30,
        )
        lines = block.splitlines()
        for field in tt.HEADER_FIELDS:
            assert any(line.startswith(field) for line in lines), field
        assert all(
            line.startswith(" ") for line in lines if not line.startswith(tt.HEADER_FIELDS)
        )

    def test_a_rendered_task_passes_every_protocol_bar(self):
        text = tt.render_task(
            2,
            "second task",
            "2026-01-01 (human instruction: 做第二件事)",
            "turn 40 - a hard stop",
            "the tile at (3,4) reads `[CITY_CENTER]` owned by us",
            "the development plan, for one slot",
            "the second thing",
            "Body.",
        )
        assert tt.problems(text) == []
        for field in tt.HEADER_FIELDS:
            assert re.search(rf"^{re.escape(field)}", text, re.MULTILINE)
        assert re.search(r"turn \d+", next(l for l in text.splitlines() if l.startswith("expires:")))
        assert tt.is_observable(next(l for l in text.splitlines() if l.startswith("done when:")))

    def test_a_vague_done_when_is_reported(self):
        text = tt.render_task(
            3,
            "vague",
            "2026-01-01",
            "turn 40 - a hard stop",
            "the legion has done well",
            "nothing",
            "nothing",
        )
        assert any("not observable" in problem for problem in tt.problems(text))

    def test_an_expiry_without_a_turn_is_reported(self):
        text = tt.render_task(4, "x", "d", "soon", "the tile at (5,5) is ours", "o", "s")
        assert any("expires:" in problem for problem in tt.problems(text))


class TestTheRegisterAndTheLineStayInStep:
    def row(self) -> tt.Row:
        return tt.Row(
            file="002-second-task.md",
            added="2026-01-01",
            expires="turn 40",
            why="a second task, on the human's instruction",
            done="the tile at (3,4) reads CITY_CENTER owned by us, or turn 40",
        )

    def test_a_row_survives_a_round_trip(self):
        text = tt.register_with_row(REGISTER_STUB, self.row())
        rows = tt.register_rows(text)
        assert [r["file"] for r in rows] == ["001-first-task.md", "002-second-task.md"]
        assert rows[1]["why"] == self.row()["why"]
        assert "Notes below the table." in text
        back = tt.register_without(text, "002-second-task.md")
        assert [r["file"] for r in tt.register_rows(back)] == ["001-first-task.md"]

    def test_a_retirement_note_never_backticks_the_plain_task_name(self):
        text = tt.register_without(
            REGISTER_STUB,
            "001-first-task.md",
            "Task 001 was retired as `done/001-first-task-done-T20.md`.",
        )
        note = [l for l in text.splitlines() if l.startswith("Task 001")][0]
        # A backticked plain name is read as a registered task by the suite's `named_tasks()`.
        assert tt.NAME_RE.findall(note) == []
        assert "`done/001-first-task-done-T20.md`" in note
        assert tt.register_rows(text) == []

    def test_the_in_force_line_is_one_line_and_regenerated_from_the_rows(self):
        text = tt.register_with_row(REGISTER_STUB, self.row())
        line = tt.in_force_line(tt.register_rows(text))
        assert "\n" not in line
        assert "`001-first-task.md`" in line and "`002-second-task.md`" in line
        assert tt.in_force_names(line) == {"001-first-task.md", "002-second-task.md"}
        assert tt.in_force_line([]) == tt.IN_FORCE_EMPTY
        assert tt.in_force_names(tt.IN_FORCE_EMPTY) == set()

    def test_the_line_refuses_to_carry_cjk_into_agents_md(self):
        with pytest.raises(ValueError):
            tt.agents_with_in_force(AGENTS_STUB, "**IN FORCE NOW:** `002-x.md` (中文原因).")

    def test_a_cjk_why_column_is_named_rather_than_left_to_fail_later(self):
        rows = tt.register_rows(
            REGISTER_STUB.replace("a first task (expires turn 10)", "任务一")
        )
        assert tt.non_ascii_rows(rows) == ["001-first-task.md"]

    def test_rewriting_swallows_an_old_continuation_line(self):
        stub = AGENTS_STUB.replace(
            "**IN FORCE NOW:** `001-first-task.md` (a first task; expires turn 10).",
            "**IN FORCE NOW:** `001-first-task.md` (a first task; expires turn 10) and\n"
            "`002-second-task.md` (a second task; expires turn 20).",
        )
        out = tt.agents_with_in_force(stub, "**IN FORCE NOW:** `001-first-task.md` (a first task).")
        assert "002-second-task.md" not in out
        assert "Prose below the line, which must survive." in out
        assert tt.in_force_names(out) == {"001-first-task.md"}

    def test_the_real_agents_md_parses_to_its_directory(self):
        """The writer's parser and the suite's parser must agree on the file that is actually in force."""
        tmp, _, _, agents = tt.root_paths(ROOT)
        assert tt.in_force_names(agents.read_text(encoding="utf-8-sig")) == {
            p.name for p in tt.task_files(tmp)
        }


class TestTheCliEndToEnd:
    def test_add_writes_a_task_the_suite_would_accept_and_retire_undoes_it(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 0
        tmp, done, register, agents = tt.root_paths(scratch)
        path = tmp / SECOND_NAME
        assert path.exists(), [p.name for p in tmp.glob("*.md")]

        text = path.read_text(encoding="utf-8-sig")
        assert all(re.search(rf"^{re.escape(f)}", text, re.MULTILINE) for f in tt.HEADER_FIELDS)
        assert tt.problems(text) == []
        # non-ASCII content means the file must carry the BOM, or a GBK editor shows mojibake
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")
        assert tt.in_force_names(agents.read_text(encoding="utf-8-sig")) == {
            "001-first-task.md",
            SECOND_NAME,
        }
        assert {r["file"] for r in tt.register_rows(register.read_text(encoding="utf-8-sig"))} == {
            "001-first-task.md",
            SECOND_NAME,
        }

        assert (
            tool.main(
                [
                    "--root", str(scratch),
                    "retire", "2",
                    "--done", "--turn", "40",
                    "--no-gate", "--no-commit",
                ]
            )
            == 0
        )
        assert not path.exists()
        retired = done / "002-second-task-do-the-second-thing-done-T40.md"
        assert retired.exists()
        assert tt.in_force_names(agents.read_text(encoding="utf-8-sig")) == {"001-first-task.md"}
        assert {r["file"] for r in tt.register_rows(register.read_text(encoding="utf-8-sig"))} == {
            "001-first-task.md"
        }
        register_text = register.read_text(encoding="utf-8-sig")
        assert "done/002-second-task-do-the-second-thing-done-T40.md" in register_text
        assert tt.NAME_RE.findall(register_text) == ["001-first-task.md"]
        capsys.readouterr()

    def test_dry_run_writes_nothing(self, scratch, capsys):
        before = {p.name for p in (scratch / "prompts/tasks/tmp").glob("*.md")}
        assert tool.main(["--root", str(scratch), *ADD_ARGS, "--dry-run"]) == 0
        after = {p.name for p in (scratch / "prompts/tasks/tmp").glob("*.md")}
        assert before == after
        capsys.readouterr()

    def test_a_non_ascii_why_is_refused_before_anything_is_written(self, scratch, capsys):
        args = list(ADD_ARGS)
        args[args.index("--why") + 1] = "拿下布鲁塞尔"
        assert tool.main(["--root", str(scratch), *args]) == 1
        assert not (scratch / "prompts/tasks/tmp" / SECOND_NAME).exists()
        assert "pure-ASCII" in capsys.readouterr().out

    def test_an_expiry_in_the_past_is_refused(self, scratch, capsys):
        args = list(ADD_ARGS)
        args[args.index("--expires-turn") + 1] = "5"
        assert tool.main(["--root", str(scratch), *args]) == 1
        assert "past" in capsys.readouterr().out

    def test_a_cjk_why_in_the_register_blocks_the_rewrite_before_anything_is_written(
        self, scratch, capsys
    ):
        register = scratch / "prompts/tasks/tmp/current_tasks.md"
        register.write_text(
            REGISTER_STUB.replace("a first task (expires turn 10)", "任务一"), encoding="utf-8-sig"
        )
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 1
        out = capsys.readouterr().out
        assert "001-first-task.md" in out and "English" in out
        assert not (scratch / "prompts/tasks/tmp" / SECOND_NAME).exists()

    def test_a_body_file_is_read_rather_than_taken_literally(self, scratch, capsys):
        body = ROOT / ".tmp" / "temp-task-fixture-body.md"
        body.write_text("## A real body\n\nWith a paragraph and a `done when:` mention.\n", encoding="utf-8")
        assert tool.main(["--root", str(scratch), *ADD_ARGS, "--body-file", str(body)]) == 0
        text = (scratch / "prompts/tasks/tmp" / SECOND_NAME).read_text(encoding="utf-8-sig")
        assert "With a paragraph and a `done when:` mention." in text
        # The body's *content* is inlined; its path appears only in the recorded command, never as the
        # way the content got there.
        assert str(body) not in text.split("<!-- published")[0]
        assert str(body) in text
        capsys.readouterr()

    def test_the_default_body_is_a_skeleton_when_none_is_given(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 0
        text = (scratch / "prompts/tasks/tmp" / SECOND_NAME).read_text(encoding="utf-8-sig")
        assert "## What to do" in text and "## Report when it is done" in text
        capsys.readouterr()

    def test_status_reports_agreement_and_the_clock(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), "status"]) == 0
        out = capsys.readouterr().out
        assert f"game turn: {FIXTURE_TURN} (from the fixture)" in out
        assert "the directory, the register and AGENTS.md agree" in out

    def test_status_names_a_mismatch(self, scratch, capsys):
        (scratch / "prompts/tasks/tmp/current_tasks.md").write_text("# empty\n", encoding="utf-8")
        assert tool.main(["--root", str(scratch), "status"]) == 0
        assert "MISMATCH" in capsys.readouterr().out


def without_cn() -> list[str]:
    """`ADD_ARGS` with the Chinese version taken out, for the refusal test."""
    return [arg for arg in ADD_ARGS if arg != "--cn" and not arg.startswith(f"@{SCRATCH}")]


class TestTheChineseBackup:
    """Human instruction 2026-09-28: every added task keeps a Chinese version as a backup.

    The load-bearing detail is **where** it lives. The turn loop's first step is "read every `*.md` in
    `prompts/tasks/tmp/`", so a backup inside that directory would be read as a second task - and the
    protocol suite would demand its five header lines. These tests pin the sibling directory and that
    the task directory itself stays English-only.
    """

    def test_the_backup_is_written_outside_the_directory_the_agent_reads(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 0
        backup = scratch / "prompts" / "tasks" / "cn" / CN_NAME
        assert backup.exists(), "the Chinese backup was not written"
        assert backup.read_bytes().startswith(b"\xef\xbb\xbf"), "Chinese needs a BOM"
        text = backup.read_text(encoding="utf-8-sig")
        assert "中文备份" in text and SECOND_NAME in text
        assert "不得" in text, "the banner must say it is not to be used as an instruction"
        capsys.readouterr()

    def test_the_task_directory_holds_only_english_files(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 0
        tmp = scratch / "prompts" / "tasks" / "tmp"
        assert not list(tmp.rglob("*.cn.md")), [str(p) for p in tmp.rglob("*.cn.md")]
        # The only things the agent's glob sees are tasks, the register and the README.
        assert {p.name for p in tmp.glob("*.md")} == {
            "README.md", "current_tasks.md", "001-first-task.md", SECOND_NAME,
        }
        capsys.readouterr()

    def test_publishing_without_a_backup_is_refused(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *without_cn()]) == 1
        out = capsys.readouterr().out
        assert "Chinese backup" in out and "--cn" in out
        assert not (scratch / "prompts" / "tasks" / "tmp" / SECOND_NAME).exists()
        assert not (scratch / "prompts" / "tasks" / "cn").exists()

    def test_no_cn_publishes_without_one_and_says_so(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *without_cn(), "--no-cn"]) == 0
        assert not (scratch / "prompts" / "tasks" / "cn" / CN_NAME).exists()
        text = (scratch / "prompts" / "tasks" / "tmp" / SECOND_NAME).read_text(encoding="utf-8-sig")
        assert "chinese backup: none (--no-cn)" in text
        capsys.readouterr()


class TestThePublishedCommandIsRecorded:
    """The command that published a task travels with it, so a reader can check how it was made."""

    def test_the_task_file_carries_the_command(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 0
        capsys.readouterr()
        text = (scratch / "prompts" / "tasks" / "tmp" / SECOND_NAME).read_text(encoding="utf-8-sig")
        blocks = tt.audit_blocks(text)
        assert len(blocks) == 1 and blocks[0].startswith("<!-- published by scripts/temp-task.py")
        # The argv as it was run: the tests pass `--root` first because argparse demands the global
        # option before the subcommand, and the record is faithful rather than prettified.
        assert "python scripts/temp-task.py" in blocks[0]
        assert " add " in blocks[0]
        assert "--title" in blocks[0] and "--cn" in blocks[0]
        assert f"chinese backup: prompts/tasks/cn/{CN_NAME}" in blocks[0]
        # A task file's protocol rules must not be disturbed by the audit block.
        assert tt.problems(text) == []

    def test_a_retirement_records_its_own_command(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 0
        assert tool.main(
            ["--root", str(scratch), "retire", "2", "--done", "--turn", "40", "--no-gate", "--no-commit"]
        ) == 0
        out = capsys.readouterr().out
        assert "command recorded in the retired file" in out
        retired = (
            scratch / "prompts" / "tasks" / "tmp" / "done"
            / "002-second-task-do-the-second-thing-done-T40.md"
        )
        blocks = tt.audit_blocks(retired.read_text(encoding="utf-8-sig"))
        assert len(blocks) == 2, blocks
        assert blocks[0].startswith("<!-- published")
        assert "retired by scripts/temp-task.py" in blocks[1]
        assert "retire 2 --done --turn 40" in blocks[1]

    def test_status_counts_the_records_and_the_backups(self, scratch, capsys):
        assert tool.main(["--root", str(scratch), *ADD_ARGS]) == 0
        capsys.readouterr()
        assert tool.main(["--root", str(scratch), "status"]) == 0
        out = capsys.readouterr().out
        # 001 is the fixture's pre-existing task: it has neither a record nor a backup, and status says so.
        assert "published command recorded: 1/2 task(s)" in out
        assert "001-first-task.md" in out
        assert "chinese backup: MISSING" in out
