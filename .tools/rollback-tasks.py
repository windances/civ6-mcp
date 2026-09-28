"""Roll the temporary-task state back to a turn: restore what the rollback undid.

Called by `scripts/rollback-to-turn.py` as one of its jobs, and usable on its own:

    .venv\\Scripts\\python.exe .tools\\rollback-tasks.py 218            # plan only
    .venv\\Scripts\\python.exe .tools\\rollback-tasks.py 218 --apply    # restore + rebuild
    .venv\\Scripts\\python.exe .tools\\rollback-tasks.py 218 --skip 020 --apply

`BOUNDARY` is the turn the game is being rolled back to. Every task retired after it is restored to
force (its `done when:` is false again there), a task still in force that was added after it is kept
and reported with the turn its deadline was anchored at, and `--strict` drops those instead. `--skip`
takes a task number or file name and leaves it retired, which is how two files sharing one objective
are settled deliberately.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import task_rollback as tr  # noqa: E402


def _show(root: pathlib.Path, plan: tr.Plan) -> None:
    print(f"rollback boundary   T{plan.boundary}")
    print(f"in force now        {len([t for t in tr.survey(root) if t.in_force])} task(s)")
    print(f"to restore          {len(plan.restores)}")
    for task in plan.restores:
        anchor = f"added T{task.anchor}" if task.anchor is not None else "added turn unknown"
        print(f"   {task.name:<34s} retired T{task.retired_at}, {anchor}")
    if plan.added_after:
        print(f"added after T{plan.boundary}   {len(plan.added_after)} kept in force (re-read each):")
        for task in plan.added_after:
            print(f"   {task.name:<34s} anchored at T{task.anchor}")
    if plan.unknown_anchor:
        for task in plan.unknown_anchor:
            print(f"   {task.name:<34s} no `from T<n>` in its expires: line - re-count it by hand")
    for first, second in plan.overlaps():
        print(f"   OVERLAP {first} and {second} share a done-when - --skip one of them")
    if not plan.restores and not plan.added_after:
        print("   (nothing changes: no task was retired after the boundary)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roll the temporary-task state back to a turn.")
    parser.add_argument("boundary", type=int, help="the turn the game is being rolled back to")
    parser.add_argument("--apply", action="store_true", help="move the files and rebuild the register")
    parser.add_argument("--strict", action="store_true",
                        help="also drop tasks that were added after the boundary")
    parser.add_argument("--skip", action="append", default=[],
                        help="a task number or file name to leave retired (repeatable)")
    parser.add_argument("--why", action="append", default=[],
                        help="WHY for a restored task, as NAME=TEXT (repeatable)")
    parser.add_argument("--root", default=str(ROOT), help="checkout root (default: this repo)")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    overrides: dict[str, str] = {}
    for pair in args.why:
        name, _, text = pair.partition("=")
        overrides[name.strip()] = text.strip()

    plan = tr.build_plan(root, args.boundary)
    _show(root, plan)

    if not args.apply:
        print("\nplan only. re-run with --apply to do it (every file it touches is backed up first).")
        return 0

    report = tr.apply_plan(root, plan, skip=set(args.skip), overrides=overrides, strict=args.strict)
    print("\n--- applied ---")
    for name, why, source in report.restored:
        print(f"restored      {name}  (why from {source})")
    for name in report.dropped:
        print(f"dropped       {name}  (added after the boundary, --strict)")
    for name in report.skipped:
        print(f"skipped       {name}")
    if report.backup:
        print(f"backup        {report.backup.relative_to(root)}")
    for note in report.notes:
        print(f"note          {note}")
    return 0 if report.restored or report.notes else 1


if __name__ == "__main__":
    raise SystemExit(main())
