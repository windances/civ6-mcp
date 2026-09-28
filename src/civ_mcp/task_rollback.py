"""Roll the temporary-task state back with the game.

A rollback moves the *game* to an earlier turn. The tasks do not follow on their own, and nothing else
notices: the task files are the only record of what is in force, and a retirement is a file move whose
name carries the turn (`...-done-T224.md`). So when the game goes back to turn N, **every task retired
after N has a `done when:` that is false again at N** - the capture it recorded has been undone, the
deadline it outlived is in the future again - and leaving it in `done/` is an instruction silently
withdrawn. Measured 2026-09-28: the rollback from T301 to T218 left `024-take-brussels` retired while
`布鲁塞尔` was a city-state again, and its human instruction had no carrier anywhere.

What this module does, for a boundary turn:

1. **Restore** every task retired after the boundary: the file moves back to `prompts/tasks/tmp/` under
   its original name, and its register row and the `IN FORCE NOW` line are rebuilt with it.
2. **Keep, and report**, every task *added* after the boundary. The instruction came from the human and
   a game rollback does not withdraw it, but its body was written for a position the game no longer
   occupies - the `expires:` line records the turn it was anchored at, which is the turn to re-count
   from. `strict=True` drops them instead, which is what an exact reconstruction of turn N's state
   requires.
3. **Report the overlaps** a restore creates - two files can share an objective (020 and 024 both take
   `布鲁塞尔`), and the rollback script cannot know which one the human still wants. `skip` leaves one
   retired deliberately.

It is reversible: every file it touches is copied into `.civ6-mcp-data/branches/` first, and the
register and `AGENTS.md` are rebuilt through `civ_mcp.temp_tasks`, which is the same code path
`temp-task.py` uses - including the pure-ASCII and no-tile-coordinate guards on the `IN FORCE NOW`
line.
"""

from __future__ import annotations

import datetime
import pathlib
import re
import shutil
import subprocess
from dataclasses import dataclass, field

from . import temp_tasks as tt

# A retired file carries its turn: `024-take-brussels-done-T224.md` / `...-expired-T270.md`.
_RETIRED = re.compile(r"-(done|expired)-T(\d+)\.md$")

# `expires: turn 280 - fifty-four turns from T226, where this branch stands ...` - temp-task.py writes
# the turn the match stood on, which is the only record of *when* a task entered force. The **stop** is
# the first `turn N`; the `from T<n>` is when it was counted, and the two are different numbers (024:
# stops at 241, anchored at 220) - using the anchor as the deadline would put a wrong date in the
# register.
_ANCHOR = re.compile(r"\bfrom T(\d+)\b")
_EXPIRY = re.compile(r"\bturn (\d+)\b")


@dataclass
class Task:
    """One task file, with the two turns that bound the branch it belongs to."""

    name: str
    path: pathlib.Path
    in_force: bool
    anchor: int | None = None
    retired_at: int | None = None

    @property
    def number(self) -> int:
        return int(self.name.split("-", 1)[0])


@dataclass
class Plan:
    """What the rollback would change, and what it would only report."""

    boundary: int
    restores: list[Task] = field(default_factory=list)
    added_after: list[Task] = field(default_factory=list)
    unchanged: list[Task] = field(default_factory=list)
    unknown_anchor: list[Task] = field(default_factory=list)

    @property
    def changes(self) -> list[Task]:
        return [*self.restores]

    def overlaps(self) -> list[tuple[str, str]]:
        """Pairs of restored files whose `done when:` first lines are identical."""
        seen: dict[str, str] = {}
        pairs: list[tuple[str, str]] = []
        for task in self.restores:
            line = done_when(task.path)
            if line and line in seen:
                pairs.append((seen[line], task.name))
            else:
                seen[line] = task.name
        return pairs


def retired_turn(path: pathlib.Path) -> int | None:
    """The turn a `done/` file records in its name, or None when it is not a retired task."""
    found = _RETIRED.search(path.name)
    return int(found.group(2)) if found else None


def original_name(name: str) -> str:
    """`024-take-brussels-done-T224.md` -> `024-take-brussels.md` (anything else is returned as is)."""
    return _RETIRED.sub(".md", name)


def anchor_turn(text: str) -> int | None:
    """The turn the task's own `expires:` line was counted from, when it says so."""
    for line in text.splitlines():
        if line.startswith("expires:"):
            found = _ANCHOR.search(line)
            if found:
                return int(found.group(1))
    return None


def expiry_turn(text: str) -> int | None:
    """The turn the task stops at - the **first** `turn N` of its `expires:` line, not the anchor."""
    for line in text.splitlines():
        if line.startswith("expires:"):
            found = _EXPIRY.search(line)
            if found:
                return int(found.group(1))
    return None


def done_when(path: pathlib.Path) -> str:
    """The first line of the task's `done when:`, the register's last column."""
    text = tt.read_text(path)
    for line in text.splitlines():
        if line.startswith("done when:"):
            return " ".join(line.removeprefix("done when:").split())[:160]
    return ""


def field_line(path: pathlib.Path, field: str) -> str:
    """The value of a header field (`added:`, `expires:`), unwrapped onto one line."""
    text = tt.read_text(path)
    collected: list[str] = []
    for line in text.splitlines():
        if collected:
            if line.startswith(" ") or line.startswith("\t"):
                collected.append(line.strip())
                continue
            break
        if line.startswith(f"{field}:"):
            collected.append(line.removeprefix(f"{field}:").strip())
    return " ".join(" ".join(collected).split())


def survey(root: pathlib.Path) -> list[Task]:
    """Every task file in the checkout - in force and retired - with its two bounding turns."""
    tmp, done, _, _ = tt.root_paths(root)
    tasks: list[Task] = []
    for path in tt.task_files(tmp):
        text = tt.read_text(path)
        tasks.append(Task(name=path.name, path=path, in_force=True, anchor=anchor_turn(text)))
    for path in sorted(done.glob("*.md")):
        if path.name in tt.NON_TASKS:
            continue
        turn = retired_turn(path)
        if turn is None:
            continue
        text = tt.read_text(path)
        tasks.append(
            Task(name=original_name(path.name), path=path, in_force=False,
                 anchor=anchor_turn(text), retired_at=turn)
        )
    return sorted(tasks, key=lambda task: task.number)


def build_plan(root: pathlib.Path, boundary: int) -> Plan:
    """What the boundary turn implies for the task set.

    A retired task whose `done when:` the rollback undid comes back, whatever turn it was added on:
    the objective is un-done at the boundary, and the file is the only thing that says so. A task that
    is *in force* and was anchored after the boundary is kept and reported - see the module docstring.
    """
    plan = Plan(boundary=boundary)
    for task in survey(root):
        if not task.in_force:
            if task.retired_at is not None and task.retired_at > boundary:
                plan.restores.append(task)
            else:
                plan.unchanged.append(task)
        elif task.anchor is None:
            plan.unknown_anchor.append(task)
        elif task.anchor > boundary:
            plan.added_after.append(task)
        else:
            plan.unchanged.append(task)
    return plan


def why_from_history(diff_text: str, name: str) -> str | None:
    """The register's last known `why` for `name`, read out of `git log -p` output.

    The row is deleted when a task retires, so the blurb that belongs to a restored task exists only in
    the register's history. Pure, so the parsing is testable without a repository.
    """
    found: str | None = None
    prefix = f"+| `{name}` |"
    for line in diff_text.splitlines():
        if not line.startswith(prefix):
            continue
        cells = [cell.strip() for cell in line[1:].strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[3]:
            found = cells[3]
    return found


def _git(root: pathlib.Path, args: list[str]) -> str | None:
    """Run a git command and decode its output as UTF-8, or None when git cannot answer.

    `text=True` alone decodes with the **locale** code page - gbk on this machine - while git writes
    UTF-8, so a commit subject holding Chinese raised `UnicodeDecodeError` in the reader thread and left
    `stdout` as None: the first real use of this module died on it (2026-09-28). A checkout with no
    history is a report, not a crash, so failures come back as None.
    """
    try:
        done = subprocess.run(
            ["git", *args], cwd=str(root), capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def why_from_git(root: pathlib.Path, name: str) -> str | None:
    """`why_from_history` against this checkout's history, or None when that is not available."""
    register = tt.root_paths(root)[2]
    diff = _git(root, ["log", "-p", "--", str(register.relative_to(root))])
    return why_from_history(diff, name) if diff else None


_TURN_REF = re.compile(r"\bT\d{2,4}\b")


def why_is_usable(why: str) -> bool:
    """Whether a blurb may travel into `AGENTS.md`: ASCII, no tile coordinate, no bare turn reference.

    The register's history is **not** safe by construction, in two ways that were both measured:

    - the row task 024 was added with named its target's tile - "(69,29)" - which is the exact
      coordinate that turned `AGENTS.md` red and was repaired out of the reference the same day; and
    - the row task 019 was added with read `(T220: 32% of the map explored, four living majors not
      met)`, and restoring it put a bare turn reference into the `IN FORCE NOW` line, which
      `tests/test_agents_is_game_agnostic.py` counts in prose against a budget of four - the restore
      turned the suite red on 2026-09-28, one turn after the rollback that performed it.

    A recovered blurb is checked here and falls back to the derived one when it cannot travel, so a
    restore can never write either shape back into the reference.
    """
    return (
        bool(why)
        and why.isascii()
        and not tt.stray_coordinates(why)
        and not _TURN_REF.search(why)
    )


# Kept lowercase inside a derived blurb, so a slug does not read like a headline.
_LOWER_WORDS = frozenset(
    {"the", "a", "an", "of", "to", "in", "on", "at", "and", "or", "for", "from", "with"}
)


def derived_why(task: Task, boundary: int) -> str:
    """An ASCII, coordinate-free blurb for a restore whose original cannot be recovered.

    The slug is the only English in the file name, so a proper noun can only be recovered by
    capitalising: `024-take-brussels.md` becomes "take Brussels", not "take brussels". The boundary is
    written as "turn 218", not "T218": `AGENTS.md`'s evidence test counts bare `T<number>` references in
    its prose and that line is prose, so a status blurb must not spend one of its four anchors.
    """
    words = [word for word in task.name.removesuffix(".md").split("-")[1:] if word.isascii()]
    label = (
        " ".join(
            word if index == 0 or word in _LOWER_WORDS else word.capitalize()
            for index, word in enumerate(words)
        )
        if words
        else "the task"
    )
    return f"{label} - restored by the rollback to turn {boundary}; re-read the file before acting"


def resolve_why(root: pathlib.Path, task: Task, boundary: int, overrides: dict[str, str]) -> tuple[str, str]:
    """The blurb for a restored task, and where it came from (`override`, `history`, `derived`)."""
    for key in (task.name, f"{task.number:03d}", str(task.number)):
        if key in overrides:
            return overrides[key], "override"
    found = why_from_git(root, task.name)
    if found:
        return found, "history"
    return derived_why(task, boundary), "derived"


def _row(root: pathlib.Path, task: Task, why: str) -> tt.Row:
    stop = expiry_turn(tt.read_text(task.path))
    return tt.Row(
        file=task.name,
        added=(field_line(task.path, "added").split(" ")[0] or datetime.date.today().isoformat()),
        expires=f"turn {stop}" if stop is not None else "turn ?",
        why=why,
        done=done_when(task.path),
    )


@dataclass
class Report:
    """What an apply did (or a dry run would do)."""

    boundary: int
    restored: list[tuple[str, str, str]] = field(default_factory=list)   # name, why, source
    dropped: list[str] = field(default_factory=list)
    backup: pathlib.Path | None = None
    skipped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def apply_plan(
    root: pathlib.Path,
    plan: Plan,
    *,
    skip: set[str] | None = None,
    overrides: dict[str, str] | None = None,
    strict: bool = False,
) -> Report:
    """Move the files back, rebuild the register and `IN FORCE NOW`, and verify by reading back.

    Nothing is written when there is nothing to change: a rollback of a branch that retired no task
    leaves all three sources exactly as they were, which is what makes the step safe to run twice.
    """
    skip = {name for name in (skip or set())}
    overrides = overrides or {}
    report = Report(boundary=plan.boundary)

    restores = [task for task in plan.restores if _matches(task, skip)]
    drops = [task for task in plan.added_after if _matches(task, skip)] if strict else []
    report.skipped = sorted(task.name for task in plan.restores if not _matches(task, skip))
    if not restores and not drops:
        report.notes.append("nothing to change: no task was retired after the boundary"
                            + ("" if not plan.added_after else
                               f", and {len(plan.added_after)} added after it are kept in force"))
        return report

    # Resolve and validate every blurb **before** a single file moves: a refusal has to leave the
    # checkout exactly as it was, and `AGENTS.md`'s guards are what make the check possible.
    resolved: list[tuple[Task, str, str]] = []
    for task in restores:
        why, source = resolve_why(root, task, plan.boundary, overrides)
        if not why_is_usable(why):
            if source == "history":
                why, source = derived_why(task, plan.boundary), "derived (the register's row cannot travel)"
            else:
                report.notes.append(
                    f"refused: the {source} blurb for {task.name} cannot go into AGENTS.md "
                    f"(ASCII only, and no tile coordinate): {why!r}"
                )
                return report
        resolved.append((task, why, source))

    tmp, _, register, agents = tt.root_paths(root)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = root / ".civ6-mcp-data" / "branches" / f"rollback-tasks-T{plan.boundary}-{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    report.backup = backup
    shutil.copy2(register, backup / register.name)
    shutil.copy2(agents, backup / agents.name)

    register_text = tt.read_text(register)
    moved: list[tuple[pathlib.Path, pathlib.Path]] = []
    for task, why, source in resolved:
        # Read the header fields while the file is still where it is: the row is built from them, and
        # the move below is what makes the file the in-force copy.
        row = _row(root, task, why)
        target = tmp / task.name
        if target.exists():
            report.notes.append(f"{task.name} is already in force - left alone")
            continue
        shutil.copy2(task.path, backup / task.path.name)
        task.path.rename(target)
        moved.append((target, task.path))
        register_text = tt.register_with_row(register_text, row)
        register_text = _note(register_text, task, plan.boundary)
        report.restored.append((task.name, why, source))

    for task in drops:
        why, _ = resolve_why(root, task, plan.boundary, overrides)
        shutil.copy2(task.path, backup / task.path.name)
        task.path.unlink()
        register_text = tt.register_without(register_text, task.name)
        # The file has to stay readable: a dropped task is not a retirement, it is a position the game
        # has not reached, so it belongs beside the backup rather than in `done/` (whose names have to
        # carry a retirement turn for `tests/test_temp_tasks.py`).
        shutil.copy2(backup / task.path.name, backup / f"not-yet-T{task.anchor or '?'}-{task.name}")
        report.dropped.append(task.name)

    register_text = _reconcile(root, register_text, plan.boundary, overrides, report)

    rows = tt.register_rows(register_text)
    blocked = tt.non_ascii_rows(rows)
    stray = [] if blocked else tt.stray_coordinates(tt.in_force_line(rows))
    if blocked or stray:
        # A refusal has to leave the checkout as it was found: the moves are reversed rather than left
        # half-done, because a task file in `tmp/` that no register row and no `IN FORCE NOW` line
        # names is worse than the state this call started from.
        for target, original in moved:
            target.rename(original)
        report.restored.clear()
        report.notes.append(
            "refused: the register or the `IN FORCE NOW` line would not pass its guard ("
            + ("non-ASCII `why` for: " + ", ".join(blocked) if blocked
               else "tile coordinates: " + ", ".join(stray))
            + ") - the moved files were put back and nothing was written"
        )
        return report

    tt.write_text(register, register_text)
    tt.write_text(agents, tt.agents_with_in_force(tt.read_text(agents), tt.in_force_line(rows)))

    report.notes.extend(_verify(root, report))
    return report


def _matches(task: Task, skip: set[str]) -> bool:
    return not ({task.name, f"{task.number:03d}", str(task.number)} & skip)


def _reconcile(
    root: pathlib.Path,
    register_text: str,
    boundary: int,
    overrides: dict[str, str],
    report: Report,
) -> str:
    """Make the register's table match the directory, then the `IN FORCE NOW` line match the register.

    The directory is the authority (`AGENTS.md` says so), so a row is **added for every file that is in
    force and has none**, and a row for a file that is not in force is dropped. Without this the line is
    rebuilt from whatever rows happened to exist, and a task that was in force but unregistered would
    disappear from `AGENTS.md` on the first rollback - which is the opposite of the point.
    """
    tmp = tt.root_paths(root)[0]
    present = {path.name: path for path in tt.task_files(tmp)}
    registered = {row["file"] for row in tt.register_rows(register_text)}
    for name, path in present.items():
        if name in registered:
            continue
        task = Task(name=name, path=path, in_force=True, anchor=anchor_turn(tt.read_text(path)))
        why, source = resolve_why(root, task, boundary, overrides)
        if not why_is_usable(why):
            # Same fallback as a restore: this row is being *created* here, so it must be a blurb that
            # can travel, whatever the history says.
            why, source = derived_why(task, boundary), "derived (could not travel)"
        register_text = tt.register_with_row(register_text, _row(root, task, why))
        report.notes.append(f"{name} had no register row; added one (why from {source})")
    for name in sorted(registered - set(present)):
        register_text = tt.register_without(register_text, name)
        report.notes.append(f"{name} had a register row but is not in force; row dropped")
    return register_text


def _note(register_text: str, task: Task, boundary: int) -> str:
    """Say in the register that this task came back, and why - the record of the rollback."""
    line = (
        f"Task {task.number:03d} was restored by the rollback to T{boundary}: it was retired at "
        f"T{task.retired_at}, after the target turn, so its `done when:` is false again there."
    )
    if line in register_text:
        return register_text
    return register_text.rstrip("\n") + "\n\n" + line + "\n"


def _verify(root: pathlib.Path, report: Report) -> list[str]:
    """Read the three sources back and say whether they agree, rather than trusting the write."""
    tmp, _, register, agents = tt.root_paths(root)
    rows = tt.register_rows(tt.read_text(register))
    on_disk = {path.name for path in tt.task_files(tmp)}
    registered = {row["file"] for row in rows}
    listed = tt.in_force_names(tt.read_text(agents))
    problems: list[str] = []
    if on_disk != registered:
        problems.append(f"the register and the directory disagree: {sorted(on_disk ^ registered)}")
    if on_disk != listed:
        problems.append(f"AGENTS.md and the directory disagree: {sorted(on_disk ^ listed)}")
    for name, _, _ in report.restored:
        if not (tmp / name).exists():
            problems.append(f"{name} was not moved into force")
    return problems or ["verified: the directory, the register and AGENTS.md agree"]
