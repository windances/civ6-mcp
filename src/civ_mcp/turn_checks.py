"""Turn checks: rules written in a markdown file, evaluated by end_turn every turn.

The strategy directive states rules that are objectively checkable - "the assault needs 1-3 siege by
the arithmetic (one is enough when the ground and the ranged line cover the wall pool), 2 melee, 4
ranged, 1 cavalry", "districts <= floor(pop/3)", "gold/turn stays about +10 with the army counted".
Prose in a prompt relies on the agent remembering at the right moment; the same rules in a file the
MCP evaluates every turn do not. **The siege number is a band, not a quota** (human instruction
2026-09-30): the example below shows the shape of the *expression*, and the number it carries is the
live floor, which is 1.

The file is markdown: prose for a human reader, plus machine-checked blocks::

    <!-- check
    id: siege-train
    when: turn() >= 90
    require: units(CATAPULT, TREBUCHET, BOMBARD, ARTILLERY) >= 1
    message: No siege unit at all ...
    -->

Expressions are parsed with ``ast`` and evaluated against a whitelist of node types and
function names - never ``eval`` - so a check file is data, not code. Available functions:

    researched(NAME)          a technology or civic is completed
    units(T1, T2, ...)        how many of our units match those types (suffix match)
    metric(NAME)              a diary field: science, culture, gold_per_turn, military,
                              pop, cities, districts, improvements, wonders, territory,
                              techs_completed, civics_completed
    turn()                    the current turn

Operators: + - * / // % , comparisons, and/or/not, parentheses.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_CHECKS_PATH = Path("prompts/checks/turn-checks.md")

# The rule file is **read** as ``utf-8-sig`` - a plain ``utf-8`` read would leave a BOM in the parsed
# text on a file that had one, and ``utf-8-sig`` reads a BOM-less file exactly like ``utf-8`` - and
# **written** as plain ``utf-8``, because it is one of the documents the English-only bar covers
# (``text_encoding.ASCII_ONLY_DELIVERED``) and that bar is also a no-BOM rule: a BOM on a pure-ASCII
# English file is a stray one, and both the pre-commit gate and `tests/test_text_encoding.py` fail on
# it. Measured on the live branch at T116: the first turn a ``once: true`` goal was achieved, the
# prune rewrote this file through ``utf-8-sig`` and the suite went red on a file the agent had done
# nothing to. The archive copies are ordinary documents and still round-trip through
# ``_TEXT_ENCODING``; they are copies of a BOM-less file, so they are BOM-less too.
_TEXT_ENCODING = "utf-8-sig"
_WRITE_ENCODING = "utf-8"
_BLOCK = re.compile(r"<!--\s*check\b(.*?)-->", re.DOTALL | re.IGNORECASE)
_KEY = re.compile(r"^([a-z_]+)\s*:\s*(.*)$")

_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Call,
    ast.Name,
    ast.Constant,
    ast.Load,
)


class CheckError(ValueError):
    """A malformed check file. Reported, never fatal to a turn."""


@dataclass
class TurnCheck:
    check_id: str
    require: str
    message: str
    when: str | None = None
    level: str = "warn"
    once: bool = False
    source: str = ""


@dataclass
class CheckRun:
    """The outcome of evaluating a whole file once.

    ``passed`` is kept apart from ``skipped`` on purpose: a rule whose ``when`` gate is false
    never applied, and must not be mistaken for a goal that has been achieved.
    """

    checks: list[TurnCheck]
    failures: list[tuple[TurnCheck, str]]
    passed: set[str] = field(default_factory=set)
    skipped: set[str] = field(default_factory=set)

    @property
    def failing_ids(self) -> set[str]:
        return {check.check_id for check, _ in self.failures}


@dataclass
class CheckContext:
    """What an expression can see."""

    turn: int
    units: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    researched: frozenset[str] = frozenset()

    def call(self, name: str, args: list):
        if name == "turn":
            if args:
                raise CheckError("turn() takes no arguments")
            return self.turn
        if name == "researched":
            if len(args) != 1:
                raise CheckError("researched() takes one argument")
            return str(args[0]).upper() in self.researched
        if name == "units":
            wanted = [str(a).upper() for a in args]
            return sum(
                1
                for unit in (self.units or {}).values()
                if any((unit.unit_type or "").upper().endswith(t) for t in wanted)
            )
        if name == "metric":
            if len(args) != 1:
                raise CheckError("metric() takes one argument")
            # Dotted names reach into a sub-field: metric(trade_routes.active).
            value = self.metrics
            path = str(args[0]).split(".")
            for step in path:
                if isinstance(value, dict) and step in value:
                    value = value[step]
                else:
                    raise CheckError(f"metric({args[0]!r}) is not available this turn")
            if not isinstance(value, (int, float)):
                raise CheckError(f"metric({args[0]!r}) is not a number: {value!r}")
            return value
        raise CheckError(f"unknown function {name}()")


def parse_checks(text: str) -> list[TurnCheck]:
    """Every complete ``<!-- check ... -->`` block in a markdown file, in order.

    A block without a ``require:`` line is skipped rather than rejected: the file documents
    its own format, so an example written inside prose looks exactly like a rule. A block
    that *has* a requirement but cannot be evaluated is a different thing - that is
    reported as a failure, because a rule that silently stops working is worse than no rule.
    """
    checks: list[TurnCheck] = []
    for match in _BLOCK.finditer(text):
        fields: dict[str, str] = {}
        current: str | None = None
        for line in match.group(1).splitlines():
            key = _KEY.match(line.strip())
            if key:
                current = key.group(1).lower()
                fields[current] = key.group(2).strip()
            elif current and line.strip():
                fields[current] = f"{fields[current]} {line.strip()}".strip()
        if not fields.get("require") or not fields.get("message"):
            log.debug("skipping an incomplete check block (an example in prose): %r",
                      match.group(1).strip()[:60])
            continue
        checks.append(
            TurnCheck(
                check_id=fields.get("id") or f"check-{len(checks) + 1}",
                require=fields["require"],
                message=fields["message"],
                when=fields.get("when") or None,
                level=(fields.get("level") or "warn").lower(),
                once=(fields.get("once") or "").strip().lower() in ("1", "true", "yes", "on"),
                source=match.group(0),
            )
        )
    return checks


def evaluate(expression: str, context: CheckContext):
    """Evaluate a check expression. Only the whitelisted grammar is accepted."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CheckError(f"cannot parse {expression!r}: {exc.msg}") from exc

    def walk(node):
        if not isinstance(node, _ALLOWED_NODES):
            raise CheckError(f"{type(node).__name__} is not allowed in a check expression")
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, bool, str)):
                return node.value
            raise CheckError("only numbers, strings and booleans are allowed")
        if isinstance(node, ast.Name):
            if node.id in ("True", "False"):
                return node.id == "True"
            raise CheckError(f"bare name {node.id!r}; use a function or a number")
        if isinstance(node, ast.BoolOp):
            values = [walk(v) for v in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.UnaryOp):
            operand = walk(node.operand)
            if isinstance(node.op, ast.Not):
                return not operand
            if isinstance(node.op, ast.USub):
                return -operand
            return +operand
        if isinstance(node, ast.BinOp):
            left, right = walk(node.left), walk(node.right)
            for op, fn in (
                (ast.Add, lambda a, b: a + b),
                (ast.Sub, lambda a, b: a - b),
                (ast.Mult, lambda a, b: a * b),
                (ast.Mod, lambda a, b: a % b),
                (ast.FloorDiv, lambda a, b: a // b),
                (ast.Div, lambda a, b: a / b),
            ):
                if isinstance(node.op, op):
                    return fn(left, right)
            raise CheckError("unsupported arithmetic operator")
        if isinstance(node, ast.Compare):
            left = walk(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = walk(comparator)
                outcomes = {
                    ast.Eq: left == right,
                    ast.NotEq: left != right,
                    ast.Lt: left < right,
                    ast.LtE: left <= right,
                    ast.Gt: left > right,
                    ast.GtE: left >= right,
                }
                matched = next((v for k, v in outcomes.items() if isinstance(op, k)), None)
                if matched is None or not matched:
                    return False
                left = right
            return True
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise CheckError("only plain function calls are allowed")
            if node.keywords:
                raise CheckError("keyword arguments are not allowed")
            # A bare name as an argument is the natural way to write a type or a field -
            # units(ARCHER), metric(pop), researched(CIVIC_CIVIL_ENGINEERING) - so it is
            # read as a string there, and a dotted name (trade_routes.active) as its
            # dotted string. Anywhere else a bare name stays an error, so the grammar
            # cannot smuggle a variable in.
            def arg_value(arg):
                if isinstance(arg, ast.Name):
                    return arg.id
                if isinstance(arg, ast.Attribute):
                    parts = []
                    node = arg
                    while isinstance(node, ast.Attribute):
                        parts.append(node.attr)
                        node = node.value
                    if not isinstance(node, ast.Name):
                        raise CheckError("only a plain dotted name is allowed here")
                    parts.append(node.id)
                    return ".".join(reversed(parts))
                return walk(arg)

            return context.call(node.func.id, [arg_value(a) for a in node.args])
        raise CheckError(f"{type(node).__name__} is not allowed")

    return walk(tree)


def run_checks(text: str, context: CheckContext) -> CheckRun:
    """Evaluate every check once. Returns what failed, what passed, and what was skipped."""
    checks = parse_checks(text)
    failures: list[tuple[TurnCheck, str]] = []
    passed: set[str] = set()
    skipped: set[str] = set()
    for check in checks:
        try:
            if check.when is not None and not evaluate(check.when, context):
                skipped.add(check.check_id)
                continue
            if evaluate(check.require, context):
                passed.add(check.check_id)
            else:
                failures.append((check, check.require))
        except CheckError as exc:
            # A broken rule must not silently disappear, and must not stop the turn.
            failures.append((check, f"un-evaluable: {exc}"))
    return CheckRun(checks=checks, failures=failures, passed=passed, skipped=skipped)


# ---------------------------------------------------------------------------
# Goals that retire themselves
# ---------------------------------------------------------------------------
#
# A rule marked ``once: true`` is a *goal*: the first turn its requirement holds it is
# finished, and it is recorded here so it never nags again. Left in the file for the human,
# out of the way for the agent. The record is keyed by game - a new game starts with every
# goal open - and lives beside the diary in the data directory.


def state_path() -> Path:
    import os

    from civ_mcp import run_manifest

    # Resolved at call time: `CIV_MCP_DATA_DIR` names the data root, and the retired goals belong to
    # one playthrough. A driver that already resolved gets its own directory back unchanged.
    base = Path(os.environ.get("CIV_MCP_DATA_DIR", Path.home() / ".civ6-mcp"))
    return run_manifest.resolve_data_dir(base) / "turn-checks-state.json"


def load_retired(game_key: str) -> dict[str, int]:
    """check_id -> the turn it was achieved, for one game."""
    try:
        data = json.loads(state_path().read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - no state yet, or unreadable: nothing is retired
        return {}
    per_game = data.get(game_key)
    if not isinstance(per_game, dict):
        return {}
    return {str(k): int(v) for k, v in per_game.items() if isinstance(v, (int, float))}


def retire(game_key: str, achieved: dict[str, int]) -> None:
    """Record achieved goals, merging with whatever is already there."""
    path = state_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except Exception:  # noqa: BLE001
        data = {}
    per_game = data.get(game_key)
    if not isinstance(per_game, dict):
        per_game = {}
    per_game.update(achieved)
    data[game_key] = per_game
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        log.debug("could not record retired checks at %s", path, exc_info=True)


def remove_achieved(
    text: str,
    achieved: dict[str, int],
    stamp: str,
    archive_note: str = "",
    game_key: str = "",
) -> tuple[str, list[str]]:
    """Take achieved goals out of the file, leaving one short trace line each.

    Only the rule blocks are removed - the prose around them is hand-written documentation
    and is not this function's to delete; the backup keeps the original either way. The trace
    line is there so a reader who remembers the rule can see it was done rather than wonder
    whether the check broke.

    **The trace carries the key of the match that achieved it** (added 2026-10-02), because the
    file is shared by every match played from this checkout and a goal match A achieved was
    therefore gone for match B as well - see `restore_foreign_games`. Without a key the trace is
    ambiguous, and an ambiguous trace is left alone rather than guessed at.

    Pure on purpose: the caller owns the reading, the backup and the writing.
    """
    removed: list[str] = []
    out = text
    for check in parse_checks(text):
        if check.check_id not in achieved:
            continue
        when = achieved[check.check_id]
        trace = (
            f"<!-- achieved T{when}: {check.check_id}"
            + (f" (game: {game_key})" if game_key else "")
            + (f" (original in {archive_note})" if archive_note else "")
            + " -->"
        )
        if check.source in out:
            out = out.replace(check.source, trace, 1)
            removed.append(check.check_id)
    if removed:
        out = re.sub(r"\n{3,}", "\n\n", out)
    return out, removed


def archive_path(path: Path, stamp: str) -> Path:
    """Where a pre-edit copy of the check file goes."""
    return path.parent / "archive" / f"{path.stem}-{stamp}{path.suffix}"


# Two shapes: the current one names the match that achieved the goal, and the older one (before
# 2026-10-02) does not. Both parse, and a missing key means "unknown match", which
# `restore_foreign_games` treats as this match's - it never re-arms a goal it cannot attribute.
_ACHIEVED_TRACE = re.compile(
    r"^<!-- achieved T(?P<turn>\d+): (?P<id>[\w-]+)"
    r"(?: \(game: (?P<game>[^)]+)\))?"
    r" \(original in (?P<archive>archive/[^)]+)\) -->$"
)


def archived_goal_block(archive: Path, goal_id: str) -> str | None:
    """The ``<!-- check ... -->`` block for one goal, as an archived copy holds it."""
    try:
        text = archive.read_text(encoding=_TEXT_ENCODING)
    except OSError:
        return None
    start = text.find("<!-- check")
    while start != -1:
        end = text.find("-->", start)
        if end == -1:
            return None
        block = text[start : end + 3]
        if f"id: {goal_id}" in block.splitlines():
            return block
        start = text.find("<!-- check", end)
    return None


def restore_achieved(text: str, archive_dir: Path | None = None) -> str:
    """The inverse of :func:`remove_achieved`: put every retired goal back into ``text``.

    The trace line names the archived copy the sweep wrote, so the block is recoverable exactly.
    The live file is a moving target - a `once: true` goal leaves it the moment the game achieves
    it - and two callers need the rule set as it was *before* that happened: the test suite, whose
    fixtures must not depend on which goals this playthrough has retired, and a rollback, which
    lands the game behind the achievement. Measured 2026-09-25: the ram/tower goal retired at T100
    on one branch, went back in for a rollback to T99, and retired again at T100 of the replay; the
    five tests that read the shipped file went red both times.
    """
    if archive_dir is None:
        archive_dir = Path(__file__).resolve().parents[2] / "prompts" / "checks"
    out = text
    for line in text.splitlines():
        match = _ACHIEVED_TRACE.match(line.strip())
        if not match:
            continue
        original = archive_dir / "archive" / Path(match.group("archive")).name
        block = archived_goal_block(original, match.group("id"))
        if block is None:
            continue
        marker = line + "\n" if line + "\n" in out else line
        out = out.replace(marker, block + "\n", 1)
    return out


def restore_foreign_games(
    text: str, game_key: str, archive_dir: Path | None = None
) -> tuple[str, list[str]]:
    """Put back the goals **another match** achieved, and leave this match's own alone.

    The check file is shared state: one file in the repository, evaluated by every match played from
    this checkout. A `once: true` goal is pruned from it the turn it is achieved - that is what
    makes "an achieved goal stops being reported" true - but the *file* is not per match, so a goal
    match A achieved was gone for match B too. Measured: the A3-A7 military-production experiment
    ran its whole ~340 turns with `dynasty-cycle-wonder` - China's entire civilisation ability
    obligation - absent from the loop, and all eight runs ordered zero wonders.

    The fix is the match key in the trace line: a trace naming a different match is restored from
    the archive it cites, a trace naming this match is left alone because the goal is done, and a
    trace in the old format (no key) is left alone too - re-arming a goal this match has already
    achieved would be worse than the drift, and the ambiguity is not worth guessing at.

    Returns the new text and the ids it restored. Idempotent: a restored block replaces its trace,
    so a second call finds nothing to do.
    """
    if not game_key:
        return text, []
    if archive_dir is None:
        archive_dir = Path(__file__).resolve().parents[2] / "prompts" / "checks"
    out = text
    restored: list[str] = []
    for line in text.splitlines():
        match = _ACHIEVED_TRACE.match(line.strip())
        if not match:
            continue
        other = match.group("game")
        if other is None or other == game_key:
            continue
        original = archive_dir / "archive" / Path(match.group("archive")).name
        block = archived_goal_block(original, match.group("id"))
        if block is None:
            continue
        marker = line + "\n" if line + "\n" in out else line
        out = out.replace(marker, block + "\n", 1)
        restored.append(match.group("id"))
    return out, restored


def write_checks(path: Path, text: str) -> bool:
    """Replace the check file, copy-last: never leave a state its backup cannot explain."""
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")
        # `newline=""`: without it `Path.write_text` opens in text mode and translates every ``\n``
        # to ``os.linesep``, so on Windows one prune rewrote all 397 lines of this file as CRLF and
        # the diff became the whole document. The file is LF in the repository; a writer that
        # silently changes every line ending destroys `git blame` on the one file the rules live in.
        tmp.write_text(text, encoding=_WRITE_ENCODING, newline="")
        tmp.replace(path)
    except OSError:
        log.warning("could not write %s", path, exc_info=True)
        return False
    return True


def sweep_achieved(
    path: Path, achieved: dict[str, int], stamp: str, game_key: str = ""
) -> tuple[list[str], Path | None]:
    """Back the file up, then drop the goals in ``achieved`` from it. Idempotent.

    Called at the end of a turn: whatever has been achieved - by this turn's evaluation or an
    earlier one - is taken out of the live file so what remains is only what still needs
    doing. A second call finds nothing to remove and writes nothing. The trace it leaves names
    ``game_key``, so a *different* match can put the goal back (`restore_foreign_games`).
    """
    try:
        text = path.read_text(encoding=_TEXT_ENCODING)
    except OSError:
        log.debug("no check file to prune at %s", path)
        return [], None

    if not achieved:
        return [], None

    backup = archive_path(path, stamp)
    try:
        backup.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        log.debug("could not create the archive directory for %s", path, exc_info=True)
    note = f"{backup.parent.name}/{backup.name}"

    pruned, removed = remove_achieved(text, achieved, stamp, note, game_key)
    if not removed:
        return [], None

    try:
        # Copy first, then edit: the file is never left in a state its backup cannot explain.
        # `newline=""` for the same reason as `write_checks`: the archive is a copy of an LF file.
        backup.write_text(text, encoding=_TEXT_ENCODING, newline="")
    except OSError:
        log.warning("could not back up %s (backup at %s)", path, backup, exc_info=True)
        return [], backup if backup.exists() else None
    if not write_checks(path, pruned):
        return [], backup if backup.exists() else None
    return removed, backup


def load_checks(path: Path | None = None) -> tuple[str | None, Path]:
    """The check file's text, or None when it is absent."""
    import os

    target = path or Path(os.environ.get("CIV_MCP_TURN_CHECKS") or DEFAULT_CHECKS_PATH)
    try:
        return target.read_text(encoding=_TEXT_ENCODING), target
    except OSError:
        return None, target
