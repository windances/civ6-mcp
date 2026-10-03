"""A live tool must not carry a fact about one match.

Three audits were needed to find the match state in `.tools/`, and the first two looked in the wrong
place: the grep tool skips ignored paths, and `.tools/` is ignored, so the directory holding the
tools that actually run was the one directory never searched. The second audit then found nine tools
with `china_-1894041591` written into them as a constant - and one of them,
`advance-turns.py`'s `WAR_ENEMY = 5`, decided *doctrine*: which civ is refused peace. A stale id
there refuses peace to a friend and accepts it from the enemy.

So the rule is checked rather than remembered. A **live tool** - one that takes live game input and
is expected to run again - must contain:

  * **no match key**: `<civ>_<seed>` or the pair `("<civ>", <seed>)`. That is the loaded match, and a
    rollback or a new game changes it.
  * **no CJK at all**. These are English tools; a CJK character in one is a city name, a unit
    type's localized name, or a message somebody left in the wrong language. The weakest form of
    this check - listing city names - goes stale the moment a new game renames them, which is the
    whole point. "No CJK" cannot go stale.

Anything that legitimately pins an identity is a **test double or a fixture**, and belongs in
`tests/` where the value is obviously synthetic - not in a tool. `_game.py` is the resolver: it reads
the run manifest, honours `CIV6_GAME` as an explicit override, and exits with a message rather than
guessing.
"""

from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The tools that take live game input and are expected to run again. Anchored to the repo root so
# the assertion names a real path. A tool added here is a tool somebody chose to keep running.
LIVE_TOOLS = (
    ".tools/advance-turns.py",
    ".tools/production-audit.py",
    ".tools/production-recovery.py",
    ".tools/turn-verify.py",
    ".tools/target-recon.py",
    ".tools/archive-branch.py",
    ".tools/compare-branches.py",
    ".tools/dev-curve.py",
    ".tools/kabul-map.py",
    ".tools/kabul-state.py",
    ".tools/siege-facts.py",
    ".tools/check-paths.py",
    ".tools/goal-status.py",
    ".tools/show-check-prune.py",
    ".tools/_game.py",
)

# `<civ>_<seed>`: a civ name, an underscore, and a seed with enough digits to be one. Matches
# `china_-1894041591` and `china_911679432`.
MATCH_KEY = re.compile(r"(?<![A-Za-z0-9])[a-z]{3,}_-?\d{6,}(?![A-Za-z0-9])")
# The pair form a few tools used instead: `("china", -1894041591)`.
MATCH_PAIR = re.compile(r'\(\s*"[a-z]{3,}"\s*,\s*-?\d{6,}\s*\)')
# Any CJK ideograph. An English tool has no business containing one.
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

# CJK that is the *game's* localization, not this match's state. Each entry states why, so the
# exemption is a decision on the record rather than a hole in the check.
LOCALIZATION_TOOLS = {
    ".tools/compare-branches.py": "maps the game's own column labels: 城/人口/科技/文化",
    ".tools/kabul-state.py": "matches a city-state's localized name; a city-state keeps its name",
    ".tools/siege-facts.py": "regex over the game's localized capture notifications",
    ".tools/production-recovery.py": "quotes the game's own power-shortage warning string",
}


def tool_path(name: str) -> pathlib.Path:
    return ROOT / name


@pytest.mark.parametrize("name", LIVE_TOOLS)
def test_a_live_tool_names_no_match(name: str):
    path = tool_path(name)
    if not path.exists():
        pytest.skip(f"{name} is not present in this checkout")
    text = path.read_text(encoding="utf-8-sig")
    found = MATCH_KEY.findall(text) + MATCH_PAIR.findall(text)
    assert not found, (
        f"{name} carries a match key ({found[:3]}). A rollback or a new game changes it; resolve "
        f"it with `.tools/_game.py` (require_game / require_game_pair) or take it as an argument."
    )


@pytest.mark.parametrize("name", LIVE_TOOLS)
def test_a_live_tool_carries_no_cjk(name: str):
    """No CJK, rather than no city names: a list of city names goes stale exactly when it matters.

    A line with a CJK character is reported with its number, because the realistic failure is one
    string left in a message, not a file rewritten in another language.
    """
    path = tool_path(name)
    if not path.exists():
        pytest.skip(f"{name} is not present in this checkout")
    if name in LOCALIZATION_TOOLS:
        pytest.skip(f"{name}: {LOCALIZATION_TOOLS[name]}")
    offenders = [
        f"{number}: {line.strip()[:90]}"
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1)
        if CJK.search(line)
    ]
    assert not offenders, (
        f"{name} contains CJK - in an English tool that is a city name or a localized unit type, "
        f"which is one match's state:\n  " + "\n  ".join(offenders[:5])
    )


def test_the_guard_is_not_vacuous():
    """Prove the patterns catch what they are for, so the guard cannot silently stop working."""
    assert MATCH_KEY.search('GAME = "china_-1894041591"')
    assert MATCH_KEY.search("log_china_911679432_x.jsonl"), "trailing _ must not defeat it"
    assert MATCH_KEY.search('log_china_911679432_x.jsonl')
    assert MATCH_PAIR.search('return ("china", -1894041591)')
    assert CJK.search('name = "西安"')
    assert not MATCH_KEY.search('GAME = require_game()')
    assert not CJK.search("name = require_game()")
