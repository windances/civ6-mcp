"""A staged rule must be promotable, and one shape of it is not.

`prompts/checks/pending/` exists because a rule cannot go live before a server computes its metric -
a rule naming a metric the engine does not know reports `un-evaluable` on every turn and nobody can
satisfy it. Promotion is documented as a **file move**: copy the block into `../turn-checks.md`, delete
the staged file.

**Measured 2026-09-30, while promoting `concentrate-the-siege`**: both staged files then in the
directory had been written *without* a `message:`, and `turn_checks.parse_checks` skips a block that has
no `require` **or** no `message` - silently, at `log.debug` level, because the parser cannot tell such a
block from an example written inside prose. Promoting either one exactly as its own "Cut it in"
instructions say would have put a rule into `turn-checks.md` that reads as in force and never fires.
That is the failure this directory exists to prevent, reintroduced by the staging format itself.

So every staged rule is held here to the shape that survives the move: a fenced yaml block with an
`id`, a `require` and a **`message`**.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import turn_checks  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PENDING = ROOT / "prompts" / "checks" / "pending"
LIVE = ROOT / "prompts" / "checks" / "turn-checks.md"

FENCED_YAML = re.compile(r"```yaml\n(.*?)\n```", re.S)


def staged_files() -> list[pathlib.Path]:
    return sorted(p for p in PENDING.glob("*.md") if p.name != "README.md")


def fields_of_text(text: str) -> dict[str, str]:
    match = FENCED_YAML.search(text)
    if not match:
        return {}
    found: dict[str, str] = {}
    current: str | None = None
    for line in match.group(1).splitlines():
        keyed = re.match(r"^([a-z-]+):\s*(.*)$", line.strip())
        if keyed:
            current = keyed.group(1)
            found[current] = keyed.group(2).strip()
        elif current and line.strip():
            found[current] = f"{found[current]} {line.strip()}".strip()
    return found


def fields_of(path: pathlib.Path) -> dict[str, str]:
    return fields_of_text(path.read_text(encoding="utf-8-sig"))


def test_the_guard_is_not_vacuous_when_nothing_is_staged():
    """`pending/` is **empty in the normal state** (`README.md`), so the shape guard must be
    provable without a file to look at - otherwise it silently stops checking anything the day the
    last staged rule is promoted, which is exactly when the next one gets written."""
    good = "```yaml\nid: sample\nwhen: metric(x) >= 1\nrequire: metric(x) == 0\nmessage: text\n```\n"
    bad = "```yaml\nid: sample\nwhen: metric(x) >= 1\nrequire: metric(x) == 0\n```\n"
    assert fields_of_text(good).get("message")
    assert not fields_of_text(bad).get("message")
    assert fields_of_text("no fence here") == {}


def test_every_staged_rule_carries_what_the_parser_requires():
    problems: list[str] = []
    for path in staged_files():
        fields = fields_of(path)
        for required in ("id", "require", "message"):
            if not fields.get(required):
                problems.append(
                    f"{path.name}: no `{required}:` - parse_checks skips a block without one, so "
                    f"promoting it as written would add a rule that never fires"
                )
    assert not problems, problems


def test_a_block_of_that_shape_really_is_accepted_by_the_parser():
    """The guard above is only worth having if the shape it demands is the shape that parses."""
    for path in staged_files():
        fields = fields_of(path)
        # The live file's shape, not the staged file's fence: the parser reads `<!-- check -->`.
        block = "\n".join(f"{key}: {fields[key]}" for key in ("id", "require", "message") if key in fields)
        text = f"<!-- check\n{block}\n-->\n"
        parsed = turn_checks.parse_checks(text)
        assert [check.check_id for check in parsed] == [fields["id"]], (
            f"{path.name}: a block with this shape does not survive the promotion move"
        )
        assert parsed[0].message == fields["message"]


def test_no_staged_rule_is_already_live():
    """The other half of the move: a rule cut in must leave the directory."""
    live = LIVE.read_text(encoding="utf-8-sig")
    duplicated = [p.name for p in staged_files() if f"id: {fields_of(p).get('id')}" in live]
    assert not duplicated, (
        f"{duplicated} are staged and live at once: promoting a rule is the two-file move "
        "pending/README.md describes, and the staged file goes in the same commit"
    )
