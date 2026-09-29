"""Every generated Lua query is checked for the string-literal bug that broke `get_cities`.

The Lua lives inside Python triple-quoted strings, so a written `\\r\\n` reaches the game as two real
control characters and ends the Lua string literal on the spot. That is what happened to
`cities.build_cities_query` (commit 8353672, found 2026-09-29): every call answered
`ERR:Syntax Error: unfinished string near '['`, which meant **no session could take the first turn of
a new game**, and nothing in this suite could see it because nothing here compiles Lua.

A Lua parser is not available, so the guard is the shape of the text: in this codebase every Lua string
literal is single-line, so a line that ends *inside* a string is broken. Comments are skipped, because
the prose in them quotes English freely - the first version of this check flagged three comments and
missed nothing else.

This is a lint, not proof. It sees a broken literal and a missing quote; it cannot see an unbalanced
`function`/`end` or a bad pattern.
"""

from __future__ import annotations

import importlib
import inspect
import pathlib
import pkgutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import lua  # noqa: E402

# Enough to build a query for every builder in the package; none of these calls reach the game.
DUMMY = {
    "action": "skip",
    "alliance_type": "ALLIANCE_MILITARY",
    "belief": "BELIEF_GODDESS_OF_FESTIVALS",
    "choice": "DEDICATION_EXPLORATION",
    "civic": "CIVIC_CODE_OF_LAWS",
    "district_type": "DISTRICT_CAMPUS",
    "governor_type": "GOVERNOR_THE_EDUCATOR",
    "individual_id": 1,
    "item_name": "UNIT_WARRIOR",
    "item_type": "UNIT",
    "leader_type": "LEADER_QIN_ALT",
    "offer_items": [],
    "option": 1,
    "other_player_id": 1,
    "player_id": 1,
    "policy": "POLICY_DISCIPLINE",
    "production_type": "UNIT",
    "promotion_type": "PROMOTION_PINGALA_RESEARCHER",
    "request_items": [],
    "resolution_hash": 1,
    "response": "POSITIVE",
    "tech": "TECH_POTTERY",
    "trade_type": "TRADE_ROUTE",
    "unit_index": 0,
    "votes": [],
    "wonder_type": "BUILDING_PYRAMIDS",
    "yield_type": "YIELD_GOLD",
}


def ends_inside_string(line: str) -> bool:
    """True when the line closes inside a double-quoted literal that it never closed.

    Walks the line, honouring backslash escapes, and stops at a `--` comment that begins **outside** a
    string (a `--` inside one is part of the text).
    """
    in_string = False
    index = 0
    while index < len(line):
        char = line[index]
        if in_string and char == "\\":
            index += 2
            continue
        if char == '"':
            in_string = not in_string
        elif char == "-" and not in_string and line.startswith("--", index):
            break
        index += 1
    return in_string


def builders() -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    for info in sorted(pkgutil.iter_modules(lua.__path__), key=lambda m: m.name):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"civ_mcp.lua.{info.name}")
        for name, func in sorted(vars(module).items()):
            if name.startswith("build_") and inspect.isfunction(func) and func.__module__ == module.__name__:
                found.append((f"{info.name}.{name}", func))
    return found


def test_no_generated_query_leaves_a_string_open():
    checked = 0
    skipped: list[str] = []
    broken: list[str] = []
    for label, func in builders():
        kwargs = {}
        unusable = False
        for name, param in inspect.signature(func).parameters.items():
            if param.default is not inspect.Parameter.empty:
                continue
            if name in DUMMY:
                kwargs[name] = DUMMY[name]
            elif "id" in name or "x" in name or "y" in name or "index" in name or "hash" in name:
                kwargs[name] = 1
            else:
                unusable = True
                break
        if unusable:
            skipped.append(label)
            continue
        try:
            text = func(**kwargs)
        except Exception as exc:  # noqa: BLE001 - a builder that refuses dummy input is skipped, loudly
            skipped.append(f"{label} ({type(exc).__name__}: {exc})")
            continue
        if not isinstance(text, str):
            skipped.append(f"{label} (returned {type(text).__name__})")
            continue
        checked += 1
        for number, line in enumerate(text.splitlines(), start=1):
            if ends_inside_string(line):
                broken.append(f"{label} line {number}: {line.strip()[:120]}")

    assert checked > 40, f"only {checked} builders were checked; the walk is not finding them"
    assert not broken, "generated Lua with an unterminated string literal:\n  " + "\n  ".join(broken)
    # A skip list is allowed to shrink, never to hide the builders this exists for.
    assert not [s for s in skipped if s.startswith("cities.build_cities_query")], skipped
