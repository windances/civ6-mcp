"""Forget this match's past, and start again from the position the game is loaded at.

A rollback (`rollback-to-turn.py`) puts the *branch* back in order: it archives the abandoned
future, splits the diary at the boundary, restores the tasks and goals that branch retired, and
reloads. What it deliberately keeps is the past - the diary up to the boundary, the tasks already
in force, the rules already met before it - because normally that history is the memory that makes
the replayed turns make sense.

This script is the other choice, for the times the human wants none of it: **the same match, from
the loaded position, with no memory of how it got there.** It forgets, for this match only:

  - the diary (the player rows and the city rows) - what `get_diary` reads;
  - the achieved-goal state, and the ``achieved T...`` notes in ``prompts/checks/turn-checks.md``
    **that belong to this match** (keyed to it, or un-keyed - an un-keyed trace is "unknown match",
    which `turn_checks.restore_foreign_games` already treats as this match's). Their **rule bodies
    are re-armed from the archive**, because the check file's own contract is that a goal is either
    live or traceable: "the achieved note goes, the rule stays". Notes keyed to another match are
    left alone - the check file is shared by every match played from this checkout;
  - the run manifest's played-to turn, reset to the turn being resumed at;
  - the run's session scratch: a stale ``heartbeat.json``, ``agent-half.txt`` and
    ``stop-request.json``.

With ``--tasks`` it also withdraws the **temporary tasks in force** - and that is the one thing here
a session would otherwise still read and act on, because a task is an instruction rather than a
memory. The withdrawal goes through ``scripts/temp-task.py``'s own ``retire --expired`` path, so the
task file moves to ``done/``, the register row goes and ``AGENTS.md``'s ``IN FORCE NOW`` line is
rebuilt with them; ``--no-commit --no-gate`` because the commit belongs to whoever ran the fresh
start. Without the flag they are kept and the plan prints the command to withdraw one deliberately.

It keeps what is an *instruction* rather than a memory, because withdrawing one silently is the
failure this repository keeps re-learning:

  - ``prompts/checks/turn-checks.md``'s rule bodies - every one of them, including the re-armed
    ones;
  - the temporary tasks in force (``prompts/tasks/tmp/``) unless ``--tasks`` was passed;
  - ``AGENTS.md``, the orchestrator skill and the strategy directive;
  - every archive: ``.civ6-mcp-data/branches/**``, including the backup this script writes.

Nothing is deleted without a copy: everything forgotten is first written to
``.civ6-mcp-data/branches/fresh-start-<stamp>/`` with a manifest of what it held.

Usage:
  .venv\\Scripts\\python.exe scripts\\fresh-start.py 352                 # plan only
  .venv\\Scripts\\python.exe scripts\\fresh-start.py 352 --apply         # forget it
  .venv\\Scripts\\python.exe scripts\\fresh-start.py 352 --apply --tasks # ...and withdraw the tasks
  .venv\\Scripts\\python.exe scripts\\fresh-start.py 352 --apply --force
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import shutil
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Written under the branch archives, beside the rollback folders, so the evidence for "what was
#: forgotten" sits with the evidence for "what was rolled back".
BACKUP_PREFIX = "fresh-start-"

#: The rule file the traces are cut from. Its rule *bodies* are never touched.
CHECKS_REL = pathlib.Path("prompts") / "checks" / "turn-checks.md"

TASKS_REL = pathlib.Path("prompts") / "tasks" / "tmp"

#: The session's scratch inside the run directory. None of it is memory the agent reads back, but
#: all of it describes the session that has just been stopped, so it goes with the rest.
SCRATCH = ("heartbeat.json", "agent-half.txt", "stop-request.json")


def _src_on_path() -> None:
    """`civ_mcp` has to import when this file is run as a script from the repo root."""
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def data_root(root: pathlib.Path) -> pathlib.Path:
    return root / ".civ6-mcp-data"


def run_dir(root: pathlib.Path) -> pathlib.Path:
    """The run the session would read, resolved the way every other caller resolves it."""
    _src_on_path()
    from civ_mcp import run_manifest

    return run_manifest.resolve_data_dir(data_root(root))


def manifest_of(data_dir: pathlib.Path) -> dict:
    _src_on_path()
    from civ_mcp import run_manifest

    return run_manifest.load(data_dir) or {}


def game_key(manifest: dict) -> str:
    """`china_-1894041591` - the key the telemetry, the diary and the traces use."""
    civ = str(manifest.get("civ") or "")
    seed = manifest.get("seed")
    return f"{civ}_{seed}" if civ and seed is not None else ""


def trace_pattern() -> re.Pattern[str]:
    """The module's own trace parser, so the two cannot drift apart."""
    _src_on_path()
    from civ_mcp import turn_checks

    return turn_checks._ACHIEVED_TRACE


def rearm_traces(
    text: str, key: str, checks_dir: pathlib.Path
) -> tuple[str, list[int], list[str], list[int]]:
    """Put this match's achieved goals back and take their trace lines out.

    Returns ``(new text, re-armed turns, re-armed goal ids, foreign turns kept)``.

    **Removing a trace without re-arming its block is not an option**, and the check file's own
    contract says so: a goal that leaves the file must leave a trace that resolves to its archived
    block, and the suite asserts it (``test_every_retirement_trace_still_resolves_to_its_archived_block``
    asserts the traces are not empty; ``..._wonder_obligation_is_live_or_recoverable`` asserts the
    goal is live *or* traceable). So "forget what was achieved" means **the rule is live again and
    the achieved note is gone** - the rule body is kept, which is exactly the human's instruction
    (只清掉 achieved 注释、保留规则本体).

    A trace keyed to another match is left alone: the file is shared by every match in this
    checkout. A trace whose archive block cannot be found is also left alone, and reported - a
    silently dropped rule is the failure this whole mechanism exists to prevent.
    """
    pattern = trace_pattern()
    out = text
    rearmed_turns: list[int] = []
    rearmed_ids: list[str] = []
    foreign: list[int] = []
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        owner = match.group("game")
        if owner and owner != key:
            foreign.append(int(match.group("turn")))
            continue
        archive = checks_dir / "archive" / pathlib.Path(match.group("archive")).name
        block = archived_goal_block(archive, match.group("id"))
        if block is None:
            log_unrecoverable(match.group("id"), archive)
            continue
        marker = line + "\n" if line + "\n" in out else line
        out = out.replace(marker, block + "\n", 1)
        rearmed_turns.append(int(match.group("turn")))
        rearmed_ids.append(match.group("id"))
    return out, rearmed_turns, rearmed_ids, foreign


def archived_goal_block(archive: pathlib.Path, goal_id: str) -> str | None:
    _src_on_path()
    from civ_mcp import turn_checks

    return turn_checks.archived_goal_block(archive, goal_id)


def log_unrecoverable(goal_id: str, archive: pathlib.Path) -> None:
    print(f"  WARNING: {goal_id}: no block in {archive} - its trace is left in place")


def diary_rows(path: pathlib.Path) -> tuple[int, int | None, int | None]:
    """``(rows, first turn, last turn)`` for a diary file that may not parse cleanly."""
    if not path.exists():
        return 0, None, None
    rows = 0
    turns: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows += 1
        try:
            turn = json.loads(line).get("turn")
        except Exception:  # noqa: BLE001 - a damaged row is still a row to report
            continue
        if isinstance(turn, int):
            turns.append(turn)
    return rows, (min(turns) if turns else None), (max(turns) if turns else None)


def load_stop_agent():
    """`scripts/stop-agent.py` by path: its liveness rule is the one the operator already uses.

    Loaded from this script's own directory, not from the tree being forgotten: the tool lives in
    the checkout, and a run directory has no `scripts/` in it.
    """
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("fresh_start_stop_agent", here / "stop-agent.py")
    if spec is None or spec.loader is None:  # pragma: no cover - only on a damaged checkout
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def session_live(run: pathlib.Path) -> tuple[bool, str]:
    """``(live, description)`` - is a session still writing into this run?

    A wipe while a session plays is not a wipe: the session rewrites the heartbeat, appends diary
    rows and holds the tuner, so the files come back within one turn. The check is `stop-agent.py`'s
    own, imported rather than copied, so "no session is running" means the same thing to both.
    """
    module = load_stop_agent()
    if module is None:  # pragma: no cover - only on a damaged checkout
        return False, "stop-agent.py not found: liveness not checked"
    state = module.session_state(run)
    return (not module.stopped(state)), module.describe(state)


def load_temp_task():
    """`scripts/temp-task.py` by path, so a withdrawal goes through the blessed retirement path.

    That path is what keeps the task file, the register (`current_tasks.md`) and `AGENTS.md`'s
    `IN FORCE NOW` line in step with each other; a fresh start that moved the files itself would be a
    second implementation of a rule the suite tests, which is how the two drift apart.
    """
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("fresh_start_temp_task", here / "temp-task.py")
    if spec is None or spec.loader is None:  # pragma: no cover - only on a damaged checkout
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def withdraw_tasks(root: pathlib.Path, names: list[str], turn: int) -> list[tuple[str, int]]:
    """Retire every named task as **withdrawn**, through `temp-task.py`'s own `cmd_retire`.

    Returns ``(name, exit code)`` per task. The tool's default is to keep them, because a task is an
    instruction and withdrawing one silently is the failure the register and the suite exist to
    prevent; `--tasks` is the human asking for the opposite, and this is how that request is carried
    out - `done/<stem>-expired-T<turn>.md`, the register row dropped with a retirement note, and the
    `IN FORCE NOW` line rebuilt. `--no-commit --no-gate` because the commit belongs to whoever ran
    the fresh start, not to this loop.
    """
    module = load_temp_task()
    if module is None:  # pragma: no cover - only on a damaged checkout
        return [(name, 1) for name in names]
    results: list[tuple[str, int]] = []
    for name in names:
        number = name.split("-", 1)[0]
        args = argparse.Namespace(
            root=str(root),
            number=number,
            turn=turn,
            done=False,
            note=(
                "Withdrawn by scripts/fresh-start.py: the match was restarted from the loaded "
                "position, with no memory of the branch before it."
            ),
            dry_run=False,
            no_gate=True,
            no_commit=True,
            # The retired file's audit block records the equivalent, re-runnable command.
            argv=["retire", number, "--expired", "--turn", str(turn), "--no-commit"],
        )
        results.append((name, module.cmd_retire(args)))
    return results


def build_plan(root: pathlib.Path, turn: int, tasks: bool = False) -> dict:
    """What exists, what would be forgotten, and what is deliberately kept."""
    data = data_root(root)
    run = run_dir(root)
    manifest = manifest_of(run)
    key = game_key(manifest)

    diary = run / f"diary_{key}.jsonl" if key else None
    cities = run / f"diary_{key}_cities.jsonl" if key else None
    legacy_diary = (data / f"diary_{key}.jsonl") if key else None
    legacy_cities = (data / f"diary_{key}_cities.jsonl") if key else None
    state = run / "turn-checks-state.json"
    legacy_state = data / "turn-checks-state.pre-runs.json"

    forgets: list[dict] = []
    for path in (diary, cities, legacy_diary, legacy_cities):
        if path is None or not path.exists():
            continue
        rows, first, last = diary_rows(path)
        forgets.append(
            {
                "path": str(path.relative_to(root)),
                "what": "diary",
                "detail": f"{rows} row(s), turns {first}..{last}" if rows else "empty",
                "size": path.stat().st_size,
            }
        )
    for path in (state, legacy_state):
        if not path.exists():
            continue
        try:
            entries = sum(
                len(per_game) if isinstance(per_game, dict) else 0
                for per_game in json.loads(path.read_text(encoding="utf-8")).values()
            )
        except Exception:  # noqa: BLE001 - an unreadable state file is reported as such
            entries = -1
        forgets.append(
            {
                "path": str(path.relative_to(root)),
                "what": "achieved-goal state",
                "detail": f"{entries} entry(ies)" if entries >= 0 else "unreadable",
                "size": path.stat().st_size,
            }
        )
    for name in SCRATCH:
        path = run / name
        if path.exists():
            forgets.append(
                {"path": str(path.relative_to(root)), "what": "session scratch", "detail": name,
                 "size": path.stat().st_size}
            )

    checks = root / CHECKS_REL
    text = checks.read_text(encoding="utf-8") if checks.exists() else ""
    stripped, rearmed_turns, rearmed_ids, foreign = rearm_traces(
        text, key, root / CHECKS_REL.parent
    )

    # `temp_tasks.task_files` is the definition of "in force": README and the register are not tasks,
    # and a second opinion here would list `current_tasks.md` as one (it did, on the first run).
    _src_on_path()
    from civ_mcp import temp_tasks

    in_force = temp_tasks.task_files(root / TASKS_REL) if (root / TASKS_REL).is_dir() else []

    return {
        "turn": turn,
        "run_id": manifest.get("run_id") or "?",
        "game_key": key,
        "run": run,
        "manifest": manifest,
        "forgets": forgets,
        "checks_changed": stripped != text,
        "checks_text": stripped,
        "traces_rearmed": rearmed_turns,
        "goals_rearmed": rearmed_ids,
        "traces_foreign": foreign,
        "tasks_in_force": [p.name for p in in_force],
        "tasks_to_withdraw": [p.name for p in in_force] if tasks else [],
        "playing_to": manifest.get("last_turn"),
    }


def show_plan(plan: dict) -> None:
    print(f"match                {plan['game_key'] or '?'}  run {plan['run_id']}")
    print(f"resume at            T{plan['turn']}  (manifest says played to T{plan['playing_to']})")
    print(f"run directory        {plan['run']}")
    if not plan["forgets"]:
        print("nothing to forget    the diary and the state are already gone")
    for item in plan["forgets"]:
        print(f"forget               {item['path']:<62} {item['what']} ({item['detail']})")
    if plan["checks_changed"]:
        names = ", ".join(plan["goals_rearmed"]) or "none"
        print(
            f"forget               {CHECKS_REL} - {len(plan['traces_rearmed'])} achieved note(s) of "
            f"this match: {names}"
        )
        print("re-arm               the archived rule bodies for those goals (a rule cannot be live "
              "and absent at once)")
    else:
        print(f"forget               {CHECKS_REL} - no achieved note of this match")
    if plan["traces_foreign"]:
        print(
            f"keep                 {len(plan['traces_foreign'])} trace(s) keyed to another match "
            "in the shared check file"
        )
    print("keep                 every rule body in the file, and every archive it cites")
    print(f"keep                 every archive under .civ6-mcp-data/branches/")
    if plan["tasks_to_withdraw"]:
        print(
            f"withdraw             {len(plan['tasks_to_withdraw'])} temporary task(s), through "
            "temp-task.py retire --expired (the register and AGENTS.md are rebuilt with them):"
        )
        for name in plan["tasks_to_withdraw"]:
            print(f"                       {name}")
    elif plan["tasks_in_force"]:
        print(f"keep                 {len(plan['tasks_in_force'])} temporary task(s) in force:")
        for name in plan["tasks_in_force"]:
            print(f"                       {name}")
        print("                       withdraw one deliberately with: "
              f"scripts\\temp-task.cmd retire <nnn> --expired --turn {plan['turn']}")
        print("                       (or run this again with --tasks to withdraw all of them)")


def apply_plan(root: pathlib.Path, plan: dict, stamp: str) -> dict:
    """Do it: back everything up first, then forget, then reset the manifest."""
    data = data_root(root)
    backup = data / "branches" / f"{BACKUP_PREFIX}{stamp}"
    (backup / "files").mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    removed: list[str] = []
    for item in plan["forgets"]:
        source = root / item["path"]
        if not source.exists():
            continue
        # The source path is mirrored, never flattened: the run-dir diary and the legacy root diary
        # of the same match share a file name, and a flattened copy silently keeps only the last one
        # (measured 2026-10-05, when two test runs of this script forgot the real match).
        destination = backup / "files" / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(item["path"])
        source.unlink()
        removed.append(item["path"])

    checks = root / CHECKS_REL
    if plan["checks_changed"] and checks.exists():
        before = backup / "files" / CHECKS_REL.parent / f"turn-checks-before-{stamp}.md"
        before.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(checks, before)
        copied.append(str(CHECKS_REL))
        # newline="": text mode would rewrite every \n as os.linesep on Windows.
        checks.write_text(plan["checks_text"], encoding="utf-8", newline="")

    # Withdrawn tasks are copied into the same backup first, so this run's undo is one directory.
    withdrawn: list[tuple[str, int]] = []
    if plan["tasks_to_withdraw"]:
        for name in plan["tasks_to_withdraw"]:
            source = root / TASKS_REL / name
            if not source.exists():
                continue
            destination = backup / "files" / TASKS_REL / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(f"{TASKS_REL}\\{name}")
        withdrawn = withdraw_tasks(root, plan["tasks_to_withdraw"], plan["turn"])

    _src_on_path()
    from civ_mcp import run_manifest

    manifest = run_manifest.reset_turn(plan["turn"], plan["run"])

    forgets_text = "\n".join(
        f"  {item['path']}  -  {item['what']} ({item['detail']})" for item in plan["forgets"]
    ) or "  (nothing was left to forget)"
    tasks_text = "\n".join(f"  {name}" for name in plan["tasks_in_force"]) or "  (none)"
    withdrawn_text = "\n".join(
        f"  {name}  -  withdrawn (exit {code})" for name, code in withdrawn
    )
    (backup / "README.txt").write_text(
        f"Fresh start for {plan['game_key']} at T{plan['turn']}, written {stamp}.\n"
        f"Run {plan['run_id']}.\n\n"
        "This match's past was forgotten so the game could be played on from the loaded position\n"
        "with no memory of the branch that led there. Everything forgotten was copied into\n"
        "files/ first; nothing here is a deletion.\n\n"
        f"Forgotten:\n{forgets_text}\n"
        + (
            f"  {CHECKS_REL}  -  {len(plan['traces_rearmed'])} achieved note(s) of this match "
            f"removed and their rule bodies re-armed from the archive: "
            f"{', '.join(plan['goals_rearmed']) or 'none'} "
            f"(the file before the change is in files/{CHECKS_REL.parent}/)\n"
            if plan["checks_changed"]
            else ""
        )
        + f"\nThe run manifest's played-to turn was reset to T{plan['turn']}.\n\n"
        + (
            f"Withdrawn through temp-task.py (they were instructions, so this path is the one that\n"
            f"keeps the register and AGENTS.md in step):\n{withdrawn_text}\n"
            if withdrawn
            else f"Kept in force (withdraw deliberately with temp-task.py retire):\n{tasks_text}\n"
        )
        + "\nTo put the memory back: copy files/ over the checkout again, keeping the tree shape.\n",
        encoding="utf-8",
    )
    (backup / "manifest.json").write_text(
        json.dumps(
            {
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "kind": "fresh-start",
                "game_key": plan["game_key"],
                "run_id": plan["run_id"],
                "resume_at": plan["turn"],
                "played_to_before": plan["playing_to"],
                "forgotten": plan["forgets"],
                "traces_rearmed": plan["traces_rearmed"],
                "goals_rearmed": plan["goals_rearmed"],
                "traces_foreign_kept": plan["traces_foreign"],
                "tasks_kept": plan["tasks_in_force"],
                "tasks_withdrawn": [name for name, code in withdrawn if code == 0],
                "tasks_withdraw_failed": [name for name, code in withdrawn if code != 0],
                "checks_copied": bool(plan["checks_changed"]),
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return {
        "backup": backup,
        "copied": copied,
        "removed": removed,
        "manifest": manifest,
        "withdrawn": withdrawn,
    }


def main(root: pathlib.Path | None = None) -> int:
    """The CLI. ``root`` is injectable so a test can never wipe the checkout it is testing."""
    root = ROOT if root is None else pathlib.Path(root)
    parser = argparse.ArgumentParser(
        description="Forget this match's past and resume from the loaded position."
    )
    parser.add_argument("turn", type=int, help="the turn the game is being resumed at")
    parser.add_argument("--apply", action="store_true", help="forget it (default: plan only)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="even while a session looks live (it will rewrite what this forgets)",
    )
    parser.add_argument(
        "--tasks",
        action="store_true",
        help=(
            "also withdraw the temporary tasks in force, through scripts/temp-task.py, so the "
            "register and AGENTS.md's IN FORCE NOW line stay in step"
        ),
    )
    args = parser.parse_args()

    plan = build_plan(root, args.turn, tasks=args.tasks)
    show_plan(plan)

    live, why = session_live(plan["run"])
    print(f"session              {'LIVE' if live else 'not running'}  ({why})")

    if not args.apply:
        print("\nplan only. re-run with --apply to forget it.")
        return 0

    if live and not args.force:
        print(
            "\nrefusing: a session is still playing this run, and it would write the diary, the\n"
            "heartbeat and the state straight back. Stop it first:\n"
            "    .venv\\Scripts\\python.exe scripts\\stop-agent.py --wait 120\n"
            "(--force forgets anyway; the files come back the next time it acts.)"
        )
        return 2

    stamp = time.strftime("%Y%m%d-%H%M%S")
    result = apply_plan(root, plan, stamp)
    print(f"\nbackup               {result['backup'].relative_to(root)}")
    print(f"                     {len(result['copied'])} file(s) copied before forgetting")
    print(f"forgotten            {len(result['removed'])} file(s)")
    if result["withdrawn"]:
        ok = [name for name, code in result["withdrawn"] if code == 0]
        bad = [name for name, code in result["withdrawn"] if code != 0]
        print(f"withdrawn            {len(ok)} task(s) -> prompts/tasks/tmp/done/")
        for name in bad:
            print(f"  ! NOT withdrawn    {name} (temp-task.py refused it - see its output above)")
    if result["manifest"]:
        print(f"manifest             run {result['manifest']['run_id']}: played-to is now "
              f"T{result['manifest']['last_turn']}")
    else:
        print("manifest             no run.json for this run: nothing to reset")
    print(
        "\nnext: make sure the game is loaded at T"
        f"{args.turn}, then start a fresh session:\n"
        "    scripts\\resume-game.ps1 -Wait -HumanMilitary\n"
        "The new session reads an empty diary, no achieved goals, the rules as they stand"
        + (", and no temporary tasks." if result["withdrawn"] else ".")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
