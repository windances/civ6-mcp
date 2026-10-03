"""Add, retire and inspect temporary tasks - the mechanical half of `prompts/tasks/tmp/`.

    python scripts/temp-task.py status
    python scripts/temp-task.py add --title "take Brussels: analysis, staging, assault" \
        --instruction @.tmp/instruction.txt \
        --why "take the city-state Brussels on the human's instruction; expires turn 248" \
        --done-when "the tile at (69,29) reads CITY_CENTER owned by us ..." \
        --overrides "the directive's city-state rule, for this one city ..." \
        --scope "Brussels, its ring, and the train lent to it ..." \
        --body-file .tmp/brussels-body.md
    python scripts/temp-task.py retire 020 --done --turn 237 --note "..."

One command does the whole protocol, because doing it by hand has already gone wrong twice: the task
file, the register row and AGENTS.md's `IN FORCE NOW` line are written together, the mandatory text gate
runs, `tests/test_temp_tasks.py` is the verdict, and the commit follows. A red suite means **no commit**
- the files stay so you can see what is wrong.

Notes that are easy to get wrong and are handled here:

* the `IN FORCE NOW` line is regenerated from the register, as **one** line. A task name left on its
  second line is "outside the line" to `tests/test_temp_tasks.py`.
* a retirement note names the `done/` path in backticks and the plain task name **without** them: a
  backticked plain name counts as a registered task and turns the suite red.
* `--why` must be pure ASCII because it lands in AGENTS.md, which is held to the ASCII bar. The human's
  own words go in `--instruction`, verbatim, and are written into the task file's `added:` line (which
  carries a BOM). On Windows prefer `--instruction @file.txt`: CJK through a shell's argv is where it
  gets mangled, and every `--done-when`, `--overrides`, `--scope` and `--body-file` takes `@file` too.
* `--why` may not carry a **tile coordinate** for the same reason: AGENTS.md is the interface reference
  and stays game-agnostic (`tests/test_agents_is_game_agnostic.py` fails the file on any pair but the
  Coordinate System example). Name the target - "the city-state the file names" - and leave the
  coordinate in the task file, where the match's state belongs. Both `add` and `retire` refuse it.
* `--expires-turn` defaults to the current game turn plus `--turns` (30). The current turn is read the
  way the suite reads it - the newest save first, since that is the only record that keeps moving while
  a human plays with no session attached.
"""

from __future__ import annotations

import argparse
import datetime
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import temp_tasks as tt  # noqa: E402


def _value(raw: str) -> str:
    """A `--field` value, or the UTF-8 contents of the file it names with a leading `@`."""
    if raw.startswith("@"):
        return pathlib.Path(raw[1:]).read_text(encoding="utf-8-sig")
    return raw


def _one_line(text: str) -> str:
    return " ".join(text.strip().split())


def _command(argv: list[str]) -> str:
    """The command as a reader can re-run it: the argv, with spaces quoted.

    Recorded verbatim rather than reconstructed from the parsed values, because the point of the audit
    block is *what was run* - including the `@file` references a long field arrived in, which is also
    what keeps a Chinese instruction out of a shell's argv.
    """
    quoted = [f'"{arg}"' if any(c in arg for c in " \t") else arg for arg in argv]
    return "python scripts/temp-task.py " + " ".join(quoted)


def _stamp() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _line_guard(rows: list[tt.Row]) -> int:
    """0 when the rebuilt `IN FORCE NOW` line may be written into AGENTS.md, else 1 after saying why.

    AGENTS.md is the interface reference, not this match's diary: it is held to the pure-ASCII bar and
    to game-agnostic prose (`tests/test_agents_is_game_agnostic.py`), and the register's one-line `why`
    is the one field of it that reaches that line. Both `add` and `retire` rewrite the line, so both ask
    here - the earlier a leak is refused, the fewer files carry it.
    """
    blocked = tt.non_ascii_rows(rows)
    if blocked:
        print("refusing: these register rows hold non-ASCII text in the 'why' column, and AGENTS.md")
        print("          cannot carry it: " + ", ".join(blocked))
        print("          write each one-line reason in English (the Chinese stays in the task file).")
        return 1
    stray = tt.stray_coordinates(tt.in_force_line(rows))
    if stray:
        print("refusing: the 'why' column carries tile coordinates (" + ", ".join(stray) + "), and")
        print("          AGENTS.md stays game-agnostic - a coordinate there is this match's state.")
        print("          Name the target instead ('the city-state the file names'); the task file")
        print("          itself still carries the coordinate, which is where a player reads it.")
        return 1
    return 0


def _run(cmd: list[str], cwd: pathlib.Path) -> tuple[int, str]:
    done = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def _gates(root: pathlib.Path, no_gate: bool) -> list[str]:
    """Run the mandatory text gate and the protocol suite. Returns the failures, empty when green."""
    failures: list[str] = []
    if no_gate:
        print("  gates: skipped (--no-gate)")
        return failures
    script = root / "scripts" / "fix-text-encoding.py"
    if script.exists():
        code, out = _run([sys.executable, str(script)], root)
        print(f"  text gate: {out.strip().splitlines()[-1] if out.strip() else 'no output'}")
        if code != 0:
            failures.append("fix-text-encoding.py reported a problem (see its output above)")
    else:
        failures.append("scripts/fix-text-encoding.py is missing")
    code, out = _run([sys.executable, "-m", "pytest", "tests/test_temp_tasks.py", "-q"], root)
    tail = [l for l in out.strip().splitlines() if l.strip()][-1:] or ["no output"]
    print(f"  protocol suite: {tail[0]}")
    if code != 0:
        failures.append("tests/test_temp_tasks.py is red - not committing")
        print(out.strip())
    return failures


def _commit(root: pathlib.Path, subject: str, body: str, paths: list[pathlib.Path]) -> int:
    tracked = [str(p.relative_to(root)) for p in paths if p.exists()]
    removed = [str(p.relative_to(root)) for p in paths if not p.exists()]
    if tracked:
        code, out = _run(["git", "add", "--", *tracked], root)
        if code != 0:
            print(out.strip())
            return 1
    if removed:
        _run(["git", "add", "-A", "--", *removed], root)

    message = root / ".tmp" / "temp-task-commit.txt"
    message.parent.mkdir(parents=True, exist_ok=True)
    message.write_text(f"{subject}\n\n{body.strip()}\n", encoding="utf-8")
    code, out = _run(["git", "commit", "-F", str(message)], root)
    message.unlink(missing_ok=True)
    print(out.strip().splitlines()[0] if out.strip() else "git commit: no output")
    if code != 0:
        print(out.strip())
        return 1
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    tmp, done, register, agents = tt.root_paths(root)
    turn, source = tt.game_turn(root)
    print(f"game turn: {turn if turn is not None else 'unknown'} (from the {source})")
    files = tt.task_files(tmp)
    rows = {row["file"]: row for row in tt.register_rows(tt.read_text(register))}
    listed = tt.in_force_names(tt.read_text(agents)) if agents.exists() else set()
    on_disk = {p.name for p in files}
    print(f"in force: {len(files)}")
    for path in files:
        row = rows.get(path.name, {})
        expiry = _expiry_of(path)
        left = "" if (expiry is None or turn is None) else f", {expiry - turn} turn(s) left"
        state = "" if not expiry or turn is None or expiry >= turn else "  ** PAST ITS EXPIRY **"
        print(f"  {path.name}  expires turn {expiry if expiry is not None else '?'}{left}{state}")
        print(f"      {row.get('why', '(not in the register)')}")
        backup = tt.cn_path_for(root, path.name)
        print(f"      chinese backup: {backup.relative_to(root).as_posix()}"
              if backup.exists() else
              f"      chinese backup: MISSING ({backup.relative_to(root).as_posix()})")
    published = [
        path.name for path in files
        if tt.audit_blocks(tt.read_text(path))
    ]
    print(f"published command recorded: {len(published)}/{len(files)} task(s)"
          + (f" - missing in {[n for n in on_disk if n not in published]}" if len(published) != len(files) else ""))
    if listed != on_disk:
        print(f"  MISMATCH: AGENTS.md lists {sorted(listed)}, the directory holds {sorted(on_disk)}")
    if set(rows) != on_disk:
        print(f"  MISMATCH: the register lists {sorted(set(rows))}, the directory holds {sorted(on_disk)}")
    if listed == on_disk and set(rows) == on_disk:
        print("  the directory, the register and AGENTS.md agree")
    retired_files = []
    if done.exists():
        retired_files = sorted(
            (p for p in pathlib.Path(done).glob("*.md") if p.name != "README.md"),
            key=lambda p: p.stat().st_mtime,
        )
    print(f"retired: {len(retired_files)} in done/ (newest: {retired_files[-1].name if retired_files else '-'})")
    return 0


def _expiry_of(path: pathlib.Path) -> int | None:
    import re  # noqa: PLC0415

    line = next(
        (l for l in path.read_text(encoding="utf-8-sig").splitlines() if l.startswith("expires:")),
        "",
    )
    found = re.search(r"turn (\d+)", line)
    return int(found.group(1)) if found else None


def cmd_add(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    tmp, done, register, agents = tt.root_paths(root)
    turn, source = tt.game_turn(root)
    prints = args.expires_turn or ((turn or 0) + args.turns)
    if turn is not None and prints < turn:
        print(f"refusing: expires turn {prints} is already past (the game is on turn {turn}, {source})")
        return 1
    if not args.why.isascii():
        print("refusing: --why lands in AGENTS.md, which is held to the pure-ASCII bar;")
        print("          write the one-line reason in English and keep the Chinese in --instruction")
        return 1
    if "|" in args.why:
        print("refusing: --why may not contain '|' (it is a table cell)")
        return 1
    # Human instruction 2026-09-28: every added task keeps a Chinese version as a backup. It is
    # required unless the caller says --no-cn, so a task cannot be published without one by accident.
    if not args.cn and not args.no_cn:
        print("refusing: every task keeps a Chinese backup (human instruction 2026-09-28).")
        print("          pass --cn @<file> with the Chinese version, or --no-cn on purpose.")
        print(f"          it would be written to {tt.CN_REL}\\<name>{tt.CN_SUFFIX}, outside the")
        print("          directory the turn loop reads.")
        return 1
    if args.cn and args.no_cn:
        print("refusing: --cn and --no-cn contradict each other")
        return 1

    number = tt.next_number(tmp, done)
    slug = args.slug or tt.slugify(args.title)
    if not slug:
        print("refusing: the title has no ASCII words to build a file name from; pass --slug")
        return 1
    # Re-running the same publish is how an audit block gets added to a task that already exists
    # (measured 2026-09-28: it filed a second task, 026, beside the 025 it meant to update). The slug
    # is the identity, so a second publish must say `--replace` and then it rewrites that file in
    # place, keeping its number.
    existing = next(
        (p for p in tt.task_files(tmp) if p.stem.split("-", 1)[-1] == slug),
        None,
    )
    if existing is not None and not args.replace:
        print(f"refusing: {existing.name} already has this slug - a second publish would file a")
        print("          duplicate task. Pass --replace to rewrite that file in place (its number")
        print("          and its place in the register are kept), or --slug <other> for a new task.")
        return 1
    if existing is not None:
        number = int(existing.stem.split("-", 1)[0])
        name = existing.name
        print(f"replacing {name} in place (number {number:03d} kept)")
    else:
        name = f"{number:03d}-{slug}.md"
    instruction = _one_line(_value(args.instruction) if args.instruction else "")
    added = args.added or datetime.date.today().isoformat()
    added_text = f"{added} (human instruction: {instruction})" if instruction else added
    expires_text = args.expires or (
        f"turn {prints} - {args.turns} turn(s) from T{turn if turn is not None else '?'}, the turn the "
        f"match stands on (read from the {source}); a hard stop, retired either way on that turn"
    )
    body = ""
    if args.body_file:
        # `--body-file` names a file, so it is read; the value flags take `@path` for the same effect.
        body = pathlib.Path(args.body_file).read_text(encoding="utf-8-sig")
    elif args.body:
        body = _value(args.body)
    if not body.strip():
        body = _skeleton(name)

    text = tt.render_task(
        number,
        args.title,
        added_text,
        expires_text,
        _value(args.done_when),
        _value(args.overrides),
        _value(args.scope),
        body,
    )
    broken = tt.problems(text)
    if broken:
        print("refusing: the task would not pass the protocol suite:")
        for problem in broken:
            print(f"  - {problem}")
        return 1

    backup = tt.cn_path_for(root, name)
    backup_text = None
    if args.cn:
        backup_text = tt.cn_banner(name) + "\n" + _value(args.cn).strip() + "\n"
    text = tt.with_audit(
        text,
        tt.audit_block(
            "published",
            [
                f"command: {_command(args.argv)}",
                f"at: {_stamp()}",
                f"chinese backup: {backup.relative_to(root).as_posix()}"
                if backup_text is not None else "chinese backup: none (--no-cn)",
            ],
        ),
    )

    first_line = _one_line(next(l for l in text.splitlines() if l.startswith("done when:")))
    row = tt.Row(
        file=name,
        added=added,
        expires=f"turn {prints}",
        why=_one_line(args.why),
        done=first_line.removeprefix("done when:").strip()[:160],
    )
    path = tmp / name
    register_text = tt.read_text(register)
    if existing is not None:
        # The row is being rewritten: drop the old one so the new `expires`/`why`/`done` replace it
        # instead of the old row being kept because a row with that name already exists.
        register_text = tt.register_without(register_text, name)
    register_text = tt.register_with_row(register_text, row)
    rows = tt.register_rows(register_text)
    if _line_guard(rows):
        return 1
    agents_text = tt.agents_with_in_force(tt.read_text(agents), tt.in_force_line(rows))

    print(f"task: {name}")
    print(f"  expires: turn {prints} (game turn {turn if turn is not None else '?'}, from the {source})")
    print(f"  register row: {tt.row_markdown(row)}")
    print(f"  IN FORCE NOW: {tt.in_force_line(rows)}")
    print(f"  command recorded in the file: {_command(args.argv)}")
    if backup_text is None:
        print(f"  chinese backup: none (--no-cn); the task directory is what the agent reads")
    else:
        print(f"  chinese backup: {backup.relative_to(root).as_posix()} (not read by the agent)")
    if args.dry_run:
        print("dry run: nothing written")
        return 0

    tt.write_text(path, text)
    if backup_text is not None:
        backup.parent.mkdir(parents=True, exist_ok=True)
        tt.write_text(backup, backup_text)
    tt.write_text(register, register_text)
    tt.write_text(agents, agents_text)
    print("  wrote the task file, the register and AGENTS.md"
          + (", and the Chinese backup" if backup_text is not None else ""))
    failures = _gates(root, args.no_gate)
    if failures or args.no_commit:
        for failure in failures:
            print(f"  ! {failure}")
        print("  not committed. Undo with: git checkout -- AGENTS.md prompts/tasks/tmp/current_tasks.md")
        print(f"                          and delete prompts/tasks/tmp/{name}")
        if backup_text is not None:
            print(f"                          and delete {backup.relative_to(root).as_posix()}")
        return 1 if failures else 0
    return _commit(
        root,
        f"Task {number:03d}: {args.title}",
        f"Added by scripts/temp-task.py.\n\n{expires_text}\n\n"
        + (f"Verbatim instruction: {instruction}\n" if instruction else "")
        + (f"Chinese backup: {backup.relative_to(root).as_posix()}\n" if backup_text else "")
        + f"\nCommand recorded in the task file: {_command(args.argv)}\n",
        [path, register, agents, *([backup] if backup_text is not None else [])],
    )


def _skeleton(name: str) -> str:
    return (
        "## What to do\n\n"
        "1. Fill this in: the ordered steps, the reads that must precede them, and what the turn loop\n"
        "   should do when a step is refused.\n\n"
        "## Report when it is done\n\n"
        "The numbers the `done when:` names, each with the read that produced it, and the cost paid.\n\n"
        "## Why this is a file and not a turn-check rule\n\n"
        "No metric the running server computes carries this finish line, and a rule naming a metric the\n"
        "server does not compute reports `un-evaluable` every turn.\n"
    )


def cmd_retire(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root).resolve()
    tmp, done, register, agents = tt.root_paths(root)
    wanted = str(args.number).strip()
    if not wanted.isdigit():
        wanted_name = wanted if wanted.endswith(".md") else f"{wanted}.md"
        wanted = wanted_name.split("-", 1)[0]
    matches = [p for p in tt.task_files(tmp) if p.name.startswith(f"{int(wanted):03d}-")]
    if not matches:
        print(f"refusing: no in-force task numbered {int(wanted):03d} in {tmp}")
        return 1
    if len(matches) > 1:
        print(f"refusing: {len(matches)} files match that number: {[p.name for p in matches]}")
        return 1
    path = matches[0]
    turn = args.turn
    if turn is None:
        turn, source = tt.game_turn(root)
        if turn is None:
            print("refusing: no --turn given and no save, heartbeat or diary to read one from")
            print(
                "  note: with the runs layout the heartbeat and the diary live in "
                "<data-root>/runs/<run>/, not at the root - check `scripts/run.py status`"
            )
            return 1
        print(f"game turn: {turn} (from the {source})")
    status = "done" if args.done else "expired"
    target = done / f"{path.stem}-{status}-T{turn}.md"
    note = args.note or f"Task {int(wanted):03d} was retired as `done/{target.name}`."
    if not note.strip().startswith("Task"):
        note = f"Task {int(wanted):03d} was retired as `done/{target.name}`: {_one_line(note)}"
    register_text = tt.register_without(tt.read_text(register), path.name, note)
    rows = tt.register_rows(register_text)
    if _line_guard(rows):
        return 1
    agents_text = tt.agents_with_in_force(tt.read_text(agents), tt.in_force_line(rows))
    backup = tt.cn_path_for(root, path.name)
    retired_text = tt.with_audit(
        tt.read_text(path),
        tt.audit_block(
            "retired",
            [
                f"command: {_command(args.argv)}",
                f"at: {_stamp()}",
                f"status: {status} at T{turn}",
                f"chinese backup: {backup.relative_to(root).as_posix()}"
                if backup.exists() else "chinese backup: none",
            ],
        ),
    )

    print(f"retire: {path.name} -> done/{target.name} ({status} at T{turn})")
    print(f"  IN FORCE NOW: {tt.in_force_line(rows)}")
    print(f"  command recorded in the retired file: {_command(args.argv)}")
    if not backup.exists():
        print(f"  note: no Chinese backup at {backup.relative_to(root).as_posix()} "
              "(publish with --cn next time)")
    if args.dry_run:
        print("dry run: nothing moved")
        return 0

    tt.write_text(path, retired_text)
    path.rename(target)
    tt.write_text(register, register_text)
    tt.write_text(agents, agents_text)
    print("  moved the file, and rewrote the register and AGENTS.md")
    print("  remember: the diary's `tooling` line records this turn, and docs/task-history.md is the")
    print("            prose record - neither is written by this script.")
    failures = _gates(root, args.no_gate)
    if failures or args.no_commit:
        for failure in failures:
            print(f"  ! {failure}")
        print("  not committed; the files on disk are already changed")
        return 1 if failures else 0
    return _commit(
        root,
        f"Retire task {int(wanted):03d} ({status} at T{turn})",
        f"{note}\n\nRetired by scripts/temp-task.py; `IN FORCE NOW` and the register were rewritten in "
        "the same commit.",
        [path, target, register, agents],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="temp-task.py",
        description="Add, retire and inspect the temporary tasks in prompts/tasks/tmp/.",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="checkout root; a global option, so it goes before the subcommand (default: this repo)",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    status = subs.add_parser("status", help="what is in force, and what turn the game is on")
    status.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    status.set_defaults(func=cmd_status)

    add = subs.add_parser("add", help="write a task file, the register row and the IN FORCE line")
    add.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    add.add_argument("--title", required=True, help="the '# TEMP TASK NNN - ...' title")
    add.add_argument("--instruction", help="the human instruction, verbatim (CJK is fine here)")
    add.add_argument("--done-when", required=True, help="observable finish line; @file reads UTF-8")
    add.add_argument("--overrides", required=True, help="what the task outranks; @file reads UTF-8")
    add.add_argument("--scope", required=True, help="what the task authorizes; @file reads UTF-8")
    add.add_argument("--why", required=True, help="one ASCII line, no (x,y), for the register and AGENTS.md")
    add.add_argument("--slug", help="file-name slug (default: from the title)")
    add.add_argument("--turns", type=int, default=30, help="expiry = game turn + this (default 30)")
    add.add_argument("--expires-turn", type=int, help="an explicit expiry turn")
    add.add_argument("--expires", help="the whole 'expires:' sentence, verbatim")
    add.add_argument("--added", help="the date for the 'added:' line (default: today)")
    add.add_argument("--body", help="the body markdown; @file reads UTF-8")
    add.add_argument("--body-file", help="a UTF-8 file with the body markdown, read directly")
    add.add_argument(
        "--cn",
        help=f"the task's Chinese version; @file reads UTF-8. Written to {tt.CN_REL}\\<name>{tt.CN_SUFFIX}, "
             "which the turn loop does not read. Required unless --no-cn",
    )
    add.add_argument("--no-cn", action="store_true",
                     help="publish without a Chinese backup (deliberate, and recorded in the file)")
    add.add_argument("--replace", action="store_true",
                     help="rewrite the task that already has this slug, in place, instead of refusing")
    add.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    add.add_argument("--no-commit", action="store_true", help="write the files, do not commit")
    add.add_argument("--no-gate", action="store_true", help="skip the text gate and the protocol suite")
    add.set_defaults(func=cmd_add)

    retire = subs.add_parser("retire", help="move a task to done/ and re-sync the register and AGENTS.md")
    retire.add_argument("number", help="the task number (020) or its file name")
    retire.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    group = retire.add_mutually_exclusive_group(required=True)
    group.add_argument("--done", action="store_true", help="its done-when held")
    group.add_argument("--expired", action="store_true", help="its expiry arrived first")
    retire.add_argument("--turn", type=int, help="the turn it ended on (default: the game turn)")
    retire.add_argument("--note", help="the prose note for the register (plain task name unbackticked)")
    retire.add_argument("--dry-run", action="store_true", help="print the plan, move nothing")
    retire.add_argument("--no-commit", action="store_true", help="change the files, do not commit")
    retire.add_argument("--no-gate", action="store_true", help="skip the text gate and the protocol suite")
    retire.set_defaults(func=cmd_retire)

    args = parser.parse_args(argv)
    # The audit block records *this* invocation, so the argv travels with the parsed arguments: a test
    # that calls `main([...])` must not record pytest's own command line.
    args.argv = list(argv) if argv is not None else list(sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
