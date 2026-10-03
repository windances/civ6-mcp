"""Build the localization table the tools use to print English names.

Two maps, from the game's own text files, written to ``<CIV_MCP_DATA_DIR>/loc-en-names.json``:

* **``by_type``** - ``UNIT_CROSSBOWMAN -> Crossbowman``. Built from the **English** files alone,
  using the naming convention ``LOC_<TYPE>_NAME`` that Civ 6 holds to (measured: 33/34 of the type
  codes the tools carry resolve, the one miss being a typo in the probe). A type code is unique by
  definition, so this map has no ambiguity, and because it never reads a localized file it keeps
  working whatever language the game is set to.
* **``by_zh``** - ``西安 -> Xi'an``, for the fields that have **no type sibling at all**. Measured
  across the whole turn-loop read surface, that is city names and two others; everything else has a
  code sitting beside it and is served by ``by_type``. Only strings that map to **exactly one**
  English text are kept: 28,847 of 29,408 distinct Chinese strings (98.09%) qualify, and the 561
  ambiguous ones are dropped rather than guessed - a wrong name is worse than a Chinese one.

Reads both the base game and every DLC ``Text`` directory. Reading only ``Base/`` looks complete
and is not: it misses expansion content (``散兵``/Skirmisher is an Expansion1 unit and was absent
until the DLC files were included).

    python scripts/build-loc-names.py            # build / refresh
    python scripts/build-loc-names.py --check    # report the current table without writing
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import sys
import time
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ.setdefault("CIV_MCP_DATA_DIR", str(ROOT / ".civ6-mcp-data"))

DEFAULT_GAME = pathlib.Path(
    r"D:\SteamLibrary\steamapps\common\Sid Meier's Civilization VI"
)

# The `LOC_<TYPE>_NAME` convention only makes sense for tags whose prefix is a type family, and
# restricting to them keeps the table small and free of accidental hits like a UI label.
TYPE_PREFIXES = (
    "UNIT_", "TECH_", "CIVIC_", "POLICY_", "GOVERNMENT_", "DISTRICT_", "BUILDING_",
    "RESOURCE_", "ERA_", "BELIEF_", "IMPROVEMENT_", "PROMOTION_", "PROJECT_",
    "GREAT_PERSON_", "RELIGION_", "LEADER_", "CIVILIZATION_", "TERRAIN_", "FEATURE_",
    "DISTRICT_", "UNIT_",
)

# City names are their own space; `by_zh` would otherwise have to take whatever the flat map says.
CITY_TAG = "LOC_CITY_NAME"

# Tag families whose Chinese text is worth keeping for the reverse lookup, keyed by the space name
# the runtime asks for. Uniqueness is judged **inside a space**, which is the whole point: judged
# globally, `毛利` (Maori) was dropped because some other tag renders it differently, and the same
# happened to `中世纪` (Medieval Era) and `大预言家` (Great Prophet) - three names the agent needs.
SPACES = (
    ("CITY", "LOC_CITY_NAME"),
    ("CIVILIZATION", "LOC_CIVILIZATION"),
    ("LEADER", "LOC_LEADER"),
    ("ERA", "LOC_ERA"),
    ("GREAT_PERSON_CLASS", "LOC_GREAT_PERSON_CLASS"),
    ("GREAT_PERSON_INDIVIDUAL", "LOC_GREAT_PERSON_INDIVIDUAL"),
    ("TECH", "LOC_TECH"),
    ("CIVIC", "LOC_CIVIC"),
    ("UNIT", "LOC_UNIT"),
    ("GOVERNMENT", "LOC_GOVERNMENT"),
    ("POLICY", "LOC_POLICY"),
    ("BELIEF", "LOC_BELIEF"),
    ("DISTRICT", "LOC_DISTRICT"),
    ("BUILDING", "LOC_BUILDING"),
    ("RESOURCE", "LOC_RESOURCE"),
    ("IMPROVEMENT", "LOC_IMPROVEMENT"),
    ("PROMOTION", "LOC_PROMOTION"),
    ("PROJECT", "LOC_PROJECT"),
    ("RELIGION", "LOC_RELIGION"),
)

# Only names and short labels. The corpus also holds civilopedia paragraphs, and one of those is a
# key nobody will ever look up: keeping them made the table 7.7 MB, almost all of it prose.
MAX_TEXT = 60


def space_of(tag: str) -> str | None:
    for name, prefix in SPACES:
        if tag.startswith(prefix):
            return name
    return None


def text_nodes(game: pathlib.Path):
    """(Tag, Language, Text) for every localization node in the install."""
    paths = sorted((game / "Base" / "Assets" / "Text").rglob("*.xml"))
    paths += sorted((game / "DLC").rglob("*.xml"))
    for path in paths:
        try:
            tree = ET.parse(path)
        except Exception:  # noqa: BLE001 - a malformed file must not stop the build
            continue
        for node in tree.iter():
            tag = node.get("Tag")
            if not tag:
                continue
            text = node.find("Text")
            if text is not None and text.text and text.text.strip():
                yield tag, node.get("Language"), text.text.strip()


def build(game: pathlib.Path) -> dict:
    en: dict[str, str] = {}
    zh: dict[str, str] = {}
    for tag, language, text in text_nodes(game):
        if language in (None, "en_US"):
            en.setdefault(tag, text)
        if language == "zh_Hans_CN":
            zh.setdefault(tag, text)

    by_type: dict[str, str] = {}
    for tag, name in en.items():
        if not tag.endswith("_NAME") or tag.startswith(CITY_TAG):
            continue
        code = tag[len("LOC_"):-len("_NAME")]
        if code.startswith(TYPE_PREFIXES):
            by_type.setdefault(code, name)

    reverse: dict[str, set[str]] = collections.defaultdict(set)
    per_space: dict[str, dict[str, set[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(set)
    )
    for tag, chinese in zh.items():
        english = en.get(tag)
        if not english or len(chinese) > MAX_TEXT:
            continue
        reverse[chinese].add(english)
        space = space_of(tag)
        if space:
            per_space[space][chinese].add(english)

    by_zh = {k: next(iter(v)) for k, v in reverse.items() if len(v) == 1}
    ambiguous = sum(1 for v in reverse.values() if len(v) > 1)
    by_space = {s: {k: next(iter(v)) for k, v in m.items() if len(v) == 1}
                for s, m in per_space.items()}

    # How much of the city-name space survived the filter - city names are the reason the reverse
    # map exists at all, so a collapse there would make the table useless even if it is large.
    city_strings = {zh[t] for t in zh if t.startswith(CITY_TAG) and len(zh[t]) <= MAX_TEXT}
    city_kept = len(by_space.get("CITY", {}))
    return {
        "source": str(game),
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "counts": {
            "en_tags": len(en),
            "zh_tags": len(zh),
            "by_type": len(by_type),
            "by_zh": len(by_zh),
            "by_zh_ambiguous_dropped": ambiguous,
            "by_space": len(by_space),
            "by_space_entries": sum(len(m) for m in by_space.values()),
            "city_names_total": len(city_strings),
            "city_names_resolvable": city_kept,
        },
        "by_type": by_type,
        "by_zh": by_zh,
        "by_space": by_space,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", default=str(DEFAULT_GAME), help="Civ 6 install root")
    ap.add_argument("--out", default=None, help="output path (default: data dir)")
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()

    game = pathlib.Path(args.game)
    if not game.exists():
        print(f"install not found: {game}")
        print("pass --game <path>, or leave the table absent - the tools fall back to type codes")
        return 1

    table = build(game)
    out = pathlib.Path(
        args.out
        or pathlib.Path(os.environ["CIV_MCP_DATA_DIR"]) / "loc-en-names.json"
    )
    print("built from", table["source"])
    for key, value in table["counts"].items():
        print(f"  {key:<28} {value}")

    if args.check:
        if out.exists():
            existing = json.loads(out.read_text(encoding="utf-8"))
            print("\ncurrent table:", out)
            for key, value in existing.get("counts", {}).items():
                print(f"  {key:<28} {value}  (built {existing.get('built')})")
        else:
            print("\nno table at", out)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    # `newline=""`: `write_text` in text mode rewrites every `\n` as `os.linesep` on Windows.
    tmp.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8", newline="")
    tmp.replace(out)
    print(f"\nwrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
