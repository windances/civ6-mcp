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

# Kept as the record of which tools were checked by hand before the scan covered the directory.
# Both checks now run over every top-level script, so this list is documentation rather than
# scope - the reason it is still here is that the scan cannot tell a tool from a one-off, and
# this is the list a human drew.
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
    ".tools/analyze-mojibake.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/audit-md-language.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/check-normalize.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/click-continue.py": "finds a control by the game's localized label, by OCR",
    ".tools/click-text.py": "finds a control by the game's localized label, by OCR",
    ".tools/compare-branches.py": "quotes a localized string the game itself prints",
    ".tools/diag-trade-commit.py": "finds a control by the game's localized label, by OCR",
    ".tools/drive-load.py": "finds a control by the game's localized label, by OCR",
    ".tools/e2e-real-ocr.py": "finds a control by the game's localized label, by OCR",
    ".tools/enter-game.py": "finds a control by the game's localized label, by OCR",
    ".tools/grab-screen.py": "finds a control by the game's localized label, by OCR",
    ".tools/kabul-state.py": "quotes a localized string the game itself prints",
    ".tools/kb.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/loc-debug.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/loc-lookup.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/mojibake-extent.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/mojibake-scan.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/ocr-region.py": "finds a control by the game's localized label, by OCR",
    ".tools/probe-captured-city.py": "quotes a localized string the game itself prints",
    ".tools/probe-menu-click.py": "finds a control by the game's localized label, by OCR",
    ".tools/production-recovery.py": "finds a control by the game's localized label, by OCR",
    ".tools/recover.py": "finds a control by the game's localized label, by OCR",
    ".tools/repair-mojibake.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/residual-scan.py": "quotes a localized string the game itself prints",
    ".tools/rollback-load.py": "quotes a localized string the game itself prints",
    ".tools/show-lines.py": "quotes a localized string the game itself prints",
    ".tools/show-mojibake.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/show-runs.py": "quotes a localized string the game itself prints",
    ".tools/siege-facts.py": "quotes a localized string the game itself prints",
    ".tools/state.py": "quotes a localized string the game itself prints",
    ".tools/tmp-handoff-parse.py": "quotes a localized string the game itself prints",
    ".tools/verify-loc-fix.py": "its subject is the game's localized strings, so CJK is the data",
    ".tools/watch-session.py": "finds a control by the game's localized label, by OCR",
}


def tool_path(name: str) -> pathlib.Path:
    return ROOT / name


SCRIPT_SUFFIXES = {".py", ".mjs", ".sh", ".ps1", ".cmd", ".lua"}


def top_level_scripts() -> list[pathlib.Path]:
    """Every script at the top level of `.tools/`, not a hand-picked list.

    The match-key rule is universal, so the check is too. Auditing a chosen list is what let nine
    pinned tools survive two sweeps: the list was as incomplete as the attention that wrote it.
    """
    tools = ROOT / ".tools"
    if not tools.is_dir():
        return []
    return sorted(
        p for p in tools.glob("*") if p.is_file() and p.suffix in SCRIPT_SUFFIXES
    )


def test_every_top_level_script_names_no_match():
    """A match key anywhere in `.tools/` top level is this match's state in a thing that runs again.

    Reported as one assertion over the whole directory rather than one test per file, because the
    output is a work list and a parametrized failure buries it.
    """
    offenders: list[str] = []
    for path in top_level_scripts():
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        found = MATCH_KEY.findall(text) + MATCH_PAIR.findall(text)
        if found:
            offenders.append(f"{path.name}: {sorted(set(found))[:3]}")
    assert not offenders, (
        "a match key is this match's state - a rollback or a new game changes it. Either archive "
        "the script as a one-off, or resolve the key with `.tools/_game.py` "
        "(require_game / require_game_pair), or take it as an argument:\n  "
        + "\n  ".join(offenders)
    )


def test_every_top_level_script_carries_no_cjk():
    """CJK is a proxy for a city name, and it is not universal - so it is universal **minus a list**.

    A large class of tools here is *about* CJK: `repair-mojibake.py` repairs it, `loc-lookup.py`
    looks up the game's localized names, `click-text.py` finds a button by the label the game prints
    in Chinese. For those, CJK is the subject, and a rule that forbade it would either be ignored or
    force a worse tool. For everything else it is a city name or a localized entity, which is one
    match's state.

    The exemptions are written down with a reason each, and the test checks that each still exists -
    an exemption list that outlives its files is how a check quietly stops covering anything.
    """
    missing = [name for name in LOCALIZATION_TOOLS if not (ROOT / name).exists()]
    assert not missing, f"exempted but gone - drop them: {missing}"

    offenders: list[str] = []
    for path in top_level_scripts():
        rel = f".tools/{path.name}"
        if rel in LOCALIZATION_TOOLS:
            continue
        hits = [
            f"  {rel}:{number}: {line.strip()[:80]}"
            for number, line in enumerate(
                path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1
            )
            if CJK.search(line)
        ]
        offenders.extend(hits)
    assert not offenders, (
        "CJK in a tool that is not about CJK is a city name or a localized entity, and that is one "
        "match's state:\n" + "\n".join(offenders[:12])
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
