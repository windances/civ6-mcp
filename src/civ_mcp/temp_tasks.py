"""The temporary-task protocol's mechanical half: the file, the register, the `IN FORCE NOW` line.

`tests/test_temp_tasks.py` is the **authority** on the protocol; this module mirrors its rules so that
`scripts/temp-task.py` can write a task, retire one, and re-sync the three places a task's status is
written down - the file, `current_tasks.md`, and AGENTS.md's single `IN FORCE NOW` line - without any of
them drifting. Each rule it mirrors, with the test that enforces it:

* a task file carries all five header lines (`added:`, `expires:`, `done when:`, `overrides:`, `scope:`)
  - `TestEveryTaskFileIsRetirable.test_each_task_file_has_the_four_header_lines_and_a_scope`;
* a `done when:` an agent has to argue about is a task that never retires, so its **first physical
  line** must name something the game can be queried for - `test_each_done_when_is_observable...`;
* `expires:` names a turn, and a task left in the directory past it is a failure
  - `..._names_a_turn`, `test_no_task_in_the_directory_is_past_its_expiry`;
* AGENTS.md's list and the register are each **exactly** the directory
  - `TestTheListAndTheDirectoryAgree`;
* AGENTS.md names no task outside that one line, so the line is regenerated as a **single** line and any
  old continuation lines are swallowed - `test_agents_md_names_no_task_outside_the_in_force_line`.

Two measured mistakes are designed out here. A retagged register note whose plain task name is
backticked counts as a registered task and turns the suite red, so a retirement note writes only the
`done/` path in backticks. And a task name left on the IN FORCE line's *second* line is "outside the
line" as far as the test is concerned, so the line is always rewritten in full.
"""

from __future__ import annotations

import pathlib
import re
import sys

TMP_REL = pathlib.Path("prompts") / "tasks" / "tmp"
DONE_REL = TMP_REL / "done"
AGENTS_REL = pathlib.Path("AGENTS.md")
REGISTER_NAME = "current_tasks.md"

# Neither of these is a task: `README.md` documents the directory, `current_tasks.md` is the register.
NON_TASKS = frozenset({"README.md", REGISTER_NAME})

HEADER_FIELDS = ("added:", "expires:", "done when:", "overrides:", "scope:")

# The same bar `tests/test_temp_tasks.py` applies to a `done when:`'s first line: it has to name
# something the game can be queried for - a tile, a coordinate, a count, a turn.
OBSERVABLE = re.compile(
    r"\(|-?\d+,\d+|turn \d+|no longer|>=|count ==|within \d+ tiles?|no hostile"
)

# `**IN FORCE NOW:**` and nothing else on the line; `none` (however emphasised) means the empty list.
IN_FORCE_MARKER = "IN FORCE NOW"
IN_FORCE_EMPTY = "**IN FORCE NOW:** none."

NAME_RE = re.compile(r"`(\d{3}-[^`]+\.md)`")
_SAVE_RE = re.compile(r"(0_MCP_|AutoSave_)(\d+)")
_TASK_NAME_RE = re.compile(r"^(\d{3})-(.+)\.md$")


def root_paths(root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path]:
    """(tmp dir, done dir, register, AGENTS.md) for a checkout root."""
    root = pathlib.Path(root)
    tmp = root / TMP_REL
    return tmp, tmp / "done", tmp / REGISTER_NAME, root / AGENTS_REL


def task_files(tmp: pathlib.Path) -> list[pathlib.Path]:
    """Every in-force task file, in name order. `README.md` and the register are not tasks."""
    return sorted(p for p in pathlib.Path(tmp).glob("*.md") if p.name not in NON_TASKS)


def next_number(tmp: pathlib.Path, done: pathlib.Path | None = None) -> int:
    """One past the highest number used anywhere, in force or retired."""
    highest = 0
    roots = [pathlib.Path(tmp)]
    if done is not None:
        roots.append(pathlib.Path(done))
    for directory in roots:
        for path in pathlib.Path(directory).glob("*.md"):
            found = _TASK_NAME_RE.match(path.name)
            if found:
                highest = max(highest, int(found.group(1)))
    return highest + 1


def slugify(text: str) -> str:
    """An ASCII slug for a file name, or `''` when the text holds nothing usable (e.g. all CJK)."""
    ascii_text = text.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def is_observable(done_when: str) -> bool:
    """True when the `done when:` text's first physical line satisfies the protocol's bar."""
    first = done_when.strip().splitlines()[0] if done_when.strip() else ""
    return bool(OBSERVABLE.search(first))


def _wrap(value: str) -> list[str]:
    """Wrap one header value into `(first, continuation...)` at the width the task files use."""
    width = 100
    indent = " " * 11
    words = " ".join(value.split()).split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        limit = width if not lines else width - len(indent)
        if current and len(candidate) > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current or not lines:
        lines.append(current)
    return lines


def header_block(
    added: str,
    expires: str,
    done_when: str,
    overrides: str,
    scope: str,
) -> str:
    """The five header lines, each wrapped with the continuation indent the task files use.

    The field names are padded to eleven columns (`added:     `, `done when: `) because that is the
    shape every hand-written task file in this repo already has - the tool's output should be
    indistinguishable from one a person wrote.
    """
    out: list[str] = []
    for field, value in (
        ("added:", added),
        ("expires:", expires),
        ("done when:", done_when),
        ("overrides:", overrides),
        ("scope:", scope),
    ):
        lines = _wrap(value)
        out.append(f"{field:<11}{lines[0]}".rstrip())
        out.extend(f"{' ' * 11}{line}".rstrip() for line in lines[1:])
    return "\n".join(out)


def render_task(
    number: int,
    title: str,
    added: str,
    expires: str,
    done_when: str,
    overrides: str,
    scope: str,
    body: str = "",
) -> str:
    """A complete task file: the title line, the five header lines, then the body."""
    parts = [
        f"# TEMP TASK {number:03d} - {title}".rstrip(),
        "",
        header_block(added, expires, done_when, overrides, scope),
        "",
    ]
    if body.strip():
        parts.append(body.strip())
        parts.append("")
    text = "\n".join(parts)
    return text if text.endswith("\n") else text + "\n"


def problems(text: str) -> list[str]:
    """Every protocol rule the given task text breaks, so the caller can refuse before writing."""
    found: list[str] = []
    for field in HEADER_FIELDS:
        if not re.search(rf"^{re.escape(field)}", text, re.MULTILINE):
            found.append(f"missing the {field!r} line")
    line = next((l for l in text.splitlines() if l.startswith("done when:")), "")
    if line and not OBSERVABLE.search(line):
        found.append(
            "done when: is not observable on its first line - name a coordinate (x,y), a `turn N`, "
            "`>=`, `count ==`, or a phrase like 'no longer'"
        )
    expires = next((l for l in text.splitlines() if l.startswith("expires:")), "")
    if expires and not re.search(r"turn \d+", expires):
        found.append("expires: has no 'turn N'")
    if not re.search(r"^#\s+\S", text):
        found.append("no '# TEMP TASK ...' title line")
    return found


def read_text(path: pathlib.Path) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8-sig")


def write_text(path: pathlib.Path, text: str) -> None:
    """Write a document the way this repo requires: UTF-8, with a BOM when it holds non-ASCII."""
    path = pathlib.Path(path)
    raw = text.encode("utf-8")
    if any(byte > 127 for byte in raw) and not raw.startswith(b"\xef\xbb\xbf"):
        raw = b"\xef\xbb\xbf" + raw
    path.write_bytes(raw)


# --------------------------------------------------------------------------------------
# The register: one table row per in-force task, and the IN FORCE line is derived from it
# --------------------------------------------------------------------------------------


class Row(dict):
    """One register row: `file`, `added`, `expires`, `why`, `done` (the done-when's first line)."""

    @property
    def file(self) -> str:
        return self["file"]

    @property
    def why(self) -> str:
        return self["why"]


def register_rows(register_text: str) -> list[Row]:
    """Every table row of the register, in file order. The header row is skipped."""
    rows: list[Row] = []
    for line in register_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].startswith("---") or cells[0] == "task file":
            continue
        name = cells[0].strip("`")
        if not _TASK_NAME_RE.match(name):
            continue
        rows.append(Row(file=name, added=cells[1], expires=cells[2], why=cells[3], done=cells[4]))
    return rows


def row_markdown(row: Row) -> str:
    return f"| `{row['file']}` | {row['added']} | {row['expires']} | {row['why']} | {row['done']} |"


def register_with_row(register_text: str, row: Row) -> str:
    """Insert (or replace) a row at the end of the register's table, keeping the notes below it."""
    lines = register_text.splitlines()
    out: list[str] = []
    placed = False
    last_row = -1
    for index, line in enumerate(lines):
        if line.startswith("|") and not line.startswith("|---") and not line.startswith("| task file"):
            last_row = index
    for index, line in enumerate(lines):
        if index == last_row:
            if any(r["file"] == row["file"] for r in register_rows(register_text)):
                continue
            out.append(line)
            out.append(row_markdown(row))
            placed = True
            continue
        out.append(line)
    if not placed:
        out.append(row_markdown(row))
    return "\n".join(out) + ("\n" if register_text.endswith("\n") else "")


def register_without(register_text: str, name: str, note: str = "") -> str:
    """Drop a task's row and optionally leave a retirement note.

    The note names the `done/` path in backticks and the **plain** task name without them: a
    backticked plain name is read as a registered task by `named_tasks()` and turns the suite red.
    """
    kept = [line for line in register_text.splitlines() if not _row_is(line, name)]
    text = "\n".join(kept).rstrip() + "\n"
    if note:
        text += "\n" + note.strip() + "\n"
    return text


def _row_is(line: str, name: str) -> bool:
    if not line.startswith("|"):
        return False
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and cells[0].strip("`") == name


def in_force_line(rows: list[Row]) -> str:
    """The single `IN FORCE NOW` line, rebuilt from the register so the two cannot disagree."""
    if not rows:
        return IN_FORCE_EMPTY
    parts = [f"`{row['file']}` ({row['why']})" for row in rows]
    return "**IN FORCE NOW:** " + " and ".join(parts) + "."


def non_ascii_rows(rows: list[Row]) -> list[str]:
    """The register rows whose `why` cannot travel into AGENTS.md, which is held to the ASCII bar.

    The line is regenerated from those rows, so one Chinese blurb blocks every later add and retire -
    the fix is to write that one-line reason in English and keep the Chinese in the task file, which is
    where a reader looks for it anyway.
    """
    return [row["file"] for row in rows if not row["why"].isascii()]


def agents_with_in_force(agents_text: str, line: str) -> str:
    """Replace the `IN FORCE NOW` line, swallowing any continuation lines that named tasks.

    AGENTS.md is held to the pure-ASCII bar, so the line itself is checked here rather than left for
    the gate: a Chinese blurb belongs in the task file, not in the reference.
    """
    if not line.isascii():
        raise ValueError("the IN FORCE NOW line must be pure ASCII (it is part of AGENTS.md)")
    lines = agents_text.splitlines()
    start = next((i for i, l in enumerate(lines) if IN_FORCE_MARKER in l), None)
    if start is None:
        raise ValueError(f"AGENTS.md has no {IN_FORCE_MARKER} line")
    end = start + 1
    while end < len(lines):
        candidate = lines[end]
        if not candidate.strip() or candidate.startswith("("):
            break
        if not NAME_RE.search(candidate):
            break
        end += 1
    out = lines[:start] + [line] + lines[end:]
    return "\n".join(out) + ("\n" if agents_text.endswith("\n") else "")


def in_force_names(agents_text: str) -> set[str]:
    """The file names the `IN FORCE NOW` line lists, with the same continuation rule the test uses."""
    lines = agents_text.splitlines()
    start = next((i for i, l in enumerate(lines) if IN_FORCE_MARKER in l), None)
    if start is None:
        return set()

    def names_on(line: str) -> set[str]:
        if line.strip().strip("*_` ").lower().startswith("none"):
            return set()
        return {n for n in re.findall(r"`([^`]+\.md)`", line) if n not in NON_TASKS}

    names = names_on(lines[start])
    for line in lines[start + 1:]:
        if not line.strip() or line.startswith("("):
            break
        found = names_on(line)
        if not found:
            break
        names |= found
    return names


# --------------------------------------------------------------------------------------
# The clock: what turn the match stands on, read offline
# --------------------------------------------------------------------------------------


def game_turn(root: pathlib.Path) -> tuple[int | None, str]:
    """(turn, source) - the newest save first, then the heartbeat, then the newest diary.

    This mirrors `tests/test_temp_tasks.py:game_turn`, including why the save leads: the saves are the
    only record that keeps moving while a human plays with no session attached, and the heartbeat and
    the diary are written *by* a session, so after a rollback they can name a turn the game has left.
    """
    root = pathlib.Path(root)
    try:
        sys.path.insert(0, str(root / "src"))
        from civ_mcp import game_launcher as gl  # noqa: PLC0415
        from civ_mcp import handoff  # noqa: PLC0415

        saves = []
        for directory in (gl.SAVE_DIR, gl.SINGLE_SAVE_DIR):
            for path in pathlib.Path(directory).glob("*.Civ6Save"):
                found = _SAVE_RE.match(path.name)
                if found:
                    number = int(found.group(2))
                    turn = number if found.group(1) == "0_MCP_" else number - 1
                    saves.append((path.stat().st_mtime, turn, path))
        if saves:
            newest = max(saves, key=lambda entry: entry[0])
            try:
                real = handoff.save_turn(newest[2])
            except Exception:  # noqa: BLE001 - an unreadable save falls back to its name
                real = None
            if isinstance(real, int) and real > 0:
                return real, "save"
            return newest[1], "save name"
    except Exception:  # a fresh clone has no game install, and that is not a failure
        pass

    heartbeat = root / ".civ6-mcp-data" / "heartbeat.json"
    if heartbeat.exists():
        try:
            import json  # noqa: PLC0415

            turn = json.loads(heartbeat.read_text(encoding="utf-8-sig")).get("turn")
            if isinstance(turn, int) and turn > 0:
                return turn, "heartbeat"
        except (OSError, ValueError):
            pass

    diaries = sorted(
        (root / ".civ6-mcp-data").glob("diary_*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for diary in diaries[:1]:
        tail = diary.read_bytes()[-200_000:].decode("utf-8", errors="replace")
        turns = [int(n) for n in re.findall(r'"turn":\s*(\d+)', tail)]
        if turns:
            return max(turns), "diary"
    return None, "none"
