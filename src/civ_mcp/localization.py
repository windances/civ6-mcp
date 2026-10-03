"""English names for what the game returns localized.

The game can be running in Chinese, and a good part of what the tools read then comes back in
Chinese: city names, unit names, tech and civic display names, Great People, notification prose.
The agent reads English, so this module turns what it can back into English - and, just as
importantly, leaves alone what it cannot.

**Two sources, in this order.**

1. **A sibling type code on the same record.** ``UnitInfo`` carries both ``unit_type='UNIT_ARCHER'``
   and a localized ``name``; ``PolicyInfo`` carries ``policy_type``; ``PantheonStatus`` carries
   ``current_belief``. The type code is language-independent and unique, so ``LOC_<TYPE>_NAME`` out
   of the *English* text files gives the right name with no guessing and no dependence on the
   language the game is set to. Measured over the whole turn-loop read surface: 111 of 119
   localized fields have such a sibling.
2. **A unique reverse map**, for the fields that have none - city names above all, plus the few
   display strings with no code beside them (``current_research``, ``current_civic``). Built from
   the game's own two text sets and keeping only the Chinese strings that map to **exactly one**
   English text: 28,847 of 29,408 (98.09%). The 561 ambiguous ones are dropped, not guessed.

**What it deliberately does not do.** A string it cannot resolve is returned unchanged. Interpolated
prose ("3 turns", "5 tiles", a sentence with a number in it) will not match a text entry and stays
as the game wrote it - which is honest, and much better than a plausible wrong name. Ambiguity is
never resolved by preference order.

The table is derived data: build it with ``scripts/build-loc-names.py``. With no table present every
function here is a no-op and the tools print exactly what they printed before, so a checkout without
the game install - and every test - behaves the way it always did.
"""

from __future__ import annotations

import dataclasses
import functools
import json
import logging
import os
import pathlib

log = logging.getLogger(__name__)

_TABLE_ENV = "CIV_MCP_DATA_DIR"
_TABLE_NAME = "loc-en-names.json"
_table: dict | None = None


def table_path() -> pathlib.Path:
    return (
        pathlib.Path(os.environ.get(_TABLE_ENV, pathlib.Path.home() / ".civ6-mcp"))
        / _TABLE_NAME
    )


def _tables() -> tuple[dict[str, str], dict[str, str], dict[str, dict[str, str]]]:
    """``(by_type, by_zh, by_space)``, loaded once. Missing or unreadable means empty maps."""
    global _table
    if _table is None:
        by_type: dict[str, str] = {}
        by_zh: dict[str, str] = {}
        by_space: dict[str, dict[str, str]] = {}
        path = table_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                by_type = data.get("by_type") or {}
                by_zh = data.get("by_zh") or {}
                by_space = data.get("by_space") or {}
            except Exception:  # noqa: BLE001 - a corrupt table must not break a turn
                log.warning("localization table unreadable at %s", path, exc_info=True)
        _table = {"by_type": by_type, "by_zh": by_zh, "by_space": by_space}
    return _table["by_type"], _table["by_zh"], _table["by_space"]


def reset_cache() -> None:
    """Forget the loaded table. For tests, and for a long session that rebuilds it."""
    global _table
    _table = None


def has_cjk(text: object) -> bool:
    """True when the string holds a CJK character, which is the only case worth touching."""
    return any("\u3400" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff" for ch in str(text))


def by_type(code: object) -> str | None:
    if not isinstance(code, str) or not code:
        return None
    return _tables()[0].get(code.upper())


def by_text(text: object) -> str | None:
    if not isinstance(text, str) or not text:
        return None
    return _tables()[1].get(text)


def by_space(space: str | None, text: object) -> str | None:
    """The English text for ``text`` inside one tag space, which is how ambiguity is beaten.

    `毛利` has no single English form across the whole corpus - which is why a global uniqueness
    filter dropped it - but inside the civilization space it is unambiguously `Māori`. The same
    holds for `中世纪` (Medieval Era) and `大预言家` (Great Prophet). The caller knows which space a
    field belongs to, so it says so instead of taking a corpus-wide guess.
    """
    if not space or not isinstance(text, str) or not text:
        return None
    return (_tables()[2].get(space) or {}).get(text)


# Which tag space each name-only field belongs to. Only the fields with **no usable type sibling**
# need an entry: everything else is settled by the code beside it, which is exact.
FIELD_SPACES: dict[str, dict[str, str]] = {
    "GameOverview": {
        "civ_name": "CIVILIZATION", "leader_name": "LEADER", "era_name": "ERA",
        "current_research": "TECH", "current_civic": "CIVIC", "difficulty": "DIFFICULTY",
        "unit_breakdown": "UNIT",
    },
    "CivInfo": {"civ_name": "CIVILIZATION", "leader_name": "LEADER"},
    "ScoreEntry": {"civ_name": "CIVILIZATION"},
    "CityInfo": {"name": "CITY"},
    "CityStateInfo": {"name": "CITY", "suzerain_name": "CIVILIZATION"},
    "CityReligionInfo": {"civ_name": "CIVILIZATION", "city_name": "CITY"},
    "VictoryPlayerProgress": {"name": "CIVILIZATION"},
    "ReligionSummary": {"religion_name": "RELIGION"},
    "GreatPersonInfo": {
        "class_name": "GREAT_PERSON_CLASS",
        "individual_name": "GREAT_PERSON_INDIVIDUAL",
        "era_name": "ERA",
    },
    "SpaceProject": {"name": "PROJECT"},
    "LockedCivic": {"missing_prereqs": "CIVIC"},
    "LockedTech": {"missing_prereqs": "TECH"},
    "PantheonStatus": {"current_belief_name": "BELIEF"},
    "GovernmentStatus": {"government_name": "GOVERNMENT"},
    "TechCivicStatus": {"current_research": "TECH", "current_civic": "CIVIC"},
}


def english(value: object, *codes: object, space: str | None = None) -> object:
    """The English form of ``value``: by a sibling code, then the field's own space, then the map.

    Returns ``value`` itself whenever it is already English or cannot be resolved - callers rely on
    that, so a miss can never turn into a wrong name or a crash.
    """
    if not isinstance(value, str) or not has_cjk(value):
        return value
    for code in codes:
        found = by_type(code)
        if found:
            return found
    return by_space(space, value) or by_text(value) or value


def englishify(record: object) -> object:
    """Resolve every localized string in one record, using the codes that sit beside them.

    The pairing is generic rather than a table of field names: for a datum with a CJK string, any
    other string field on the same record is tried as a type code. That is what makes it work for
    ``UnitInfo`` (``unit_type``), ``PolicyInfo`` (``policy_type``), ``PantheonStatus``
    (``current_belief``) and the great-person rows without naming any of them - and it is why a new
    dataclass that follows the same convention needs no change here.

    ``FIELD_SPACES`` supplies the tag space for the handful of fields that have no code at all, and
    a list of CJK strings (``LockedCivic.missing_prereqs``) is resolved element by element.
    """
    if not (dataclasses.is_dataclass(record) and not isinstance(record, type)):
        return record
    spaces = FIELD_SPACES.get(type(record).__name__, {})
    codes: list[object] = []
    targets: list[tuple[str, object]] = []
    for f in dataclasses.fields(record):
        value = getattr(record, f.name, None)
        if isinstance(value, str) and value and not has_cjk(value):
            codes.append(value)
        elif isinstance(value, str) and has_cjk(value):
            targets.append((f.name, False))
        elif isinstance(value, list) and value and all(isinstance(v, str) for v in value):
            if any(has_cjk(v) for v in value):
                targets.append((f.name, True))
        elif isinstance(value, dict) and value and any(
            isinstance(k, str) and has_cjk(k) for k in value
        ):
            targets.append((f.name, "keys"))

    for field_name, is_list in targets:
        space = spaces.get(field_name)
        current = getattr(record, field_name)
        # A sibling code is only evidence for a field that *is* a name. Without this, any code on the
        # record would be tried for every unresolved string - and the first one that happened to
        # resolve would be stamped onto all of them, which is a wrong name rather than a missing one.
        usable = codes if (field_name == "name" or field_name.endswith("_name")) else ()
        if is_list == "keys":
            # `unit_breakdown` is `{localized unit name: count}`; the keys are the data here, and
            # leaving them meant the one line printed every turn still carried Chinese.
            replaced = {
                english(k, *usable, space=space) if isinstance(k, str) else k: v
                for k, v in current.items()
            }
            if replaced != current:
                object.__setattr__(record, field_name, replaced)
            continue
        if is_list:
            replaced = [english(item, *usable, space=space) for item in current]
            if replaced != current:
                object.__setattr__(record, field_name, replaced)
            continue
        resolved = english(current, *usable, space=space)
        if resolved is not current:
            object.__setattr__(record, field_name, resolved)
    return record


def englishify_tree(value: object) -> object:
    """``englishify`` over a whole return value: records, their nested fields, lists, tuples, dicts.

    Tuples matter: several reads return ``(rows, notes)`` and a walk that only unwrapped lists would
    silently skip cities and empire resources - the exact shape of the first leak inventory probe.
    Nesting matters just as much: a first version stopped at the outer record, so every sub-record
    (``VictoryPlayerProgress``, ``CityReligionInfo``, ``SpaceProject``) kept its Chinese while the
    top-level fields came back English - which read as "mostly fixed" and was not.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        englishify(value)
        for f in dataclasses.fields(value):
            nested = getattr(value, f.name, None)
            if isinstance(nested, (list, tuple, dict)) or (
                dataclasses.is_dataclass(nested) and not isinstance(nested, type)
            ):
                englishify_tree(nested)
        return value
    if isinstance(value, list):
        for item in value:
            englishify_tree(item)
        return value
    if isinstance(value, tuple):
        for item in value:
            englishify_tree(item)
        return value
    if isinstance(value, dict):
        for item in value.values():
            englishify_tree(item)
        return value
    return value


def english_output(fn):
    """Wrap a read so everything it returns comes back English where a name is resolvable.

    Applied to the ``GameState`` readers, which is the one place that sees every parsed result -
    doing it per parser would be the same edit a dozen times, and the next parser added would forget
    it. A read that fails still raises: this only rewrites the value on the way out.
    """

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        return englishify_tree(await fn(*args, **kwargs))

    return wrapper
