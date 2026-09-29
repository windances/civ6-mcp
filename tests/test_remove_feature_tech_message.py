"""A refused chop must say which technology it is waiting for.

Measured on attempt A5, 2026-09-30. `remove_feature` answered
`Error: CANNOT_REMOVE|Cannot remove FEATURE_JUNGLE at (60,21)` and the attempt recorded that as a
central mechanical finding - "`remove_feature` accepts FOREST and refuses JUNGLE and MARSH on this map"
- with A2 having recorded the same thing at its T26. **It was the tech line, not the tool.** The game
gates each feature on its own `RemoveTech` (`Base/Assets/Gameplay/Data/Features.xml`):
`FEATURE_FOREST` -> `TECH_MINING`, `FEATURE_JUNGLE` -> `TECH_BRONZE_WORKING`, `FEATURE_MARSH` ->
`TECH_IRRIGATION`. A5 held Mining from T8 and chopped forest twice (T40, T44); its jungle attempts at
T39 and T42 were both **before** Bronze Working (owned T45), and marsh needs Irrigation, which it never
researched. Every refusal is explained by that column.

So the refusal names the technology: a bare refusal was read as a tool defect twice.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp.lua import units  # noqa: E402


def _lua() -> str:
    return units.build_remove_feature(5)


def test_the_refusal_reads_the_features_own_remove_tech():
    lua = _lua()
    assert "RemoveTech" in lua, (
        "the feature row carries RemoveTech (Features.xml) - that column is the whole reason the "
        "engine refuses, so the message has to read it rather than guess"
    )
    assert "GameInfo.Technologies[reqTech]" in lua
    assert "HasTech" in lua, "whether the empire holds that tech is what separates the two branches"


def test_the_message_names_the_technology_and_the_two_cases():
    lua = _lua()
    assert "needs " in lua and "has not researched" in lua, (
        "the missing-tech case must name what is missing, or the refusal reads as a tool defect"
    )
    assert "IS researched" in lua, (
        "and when the tech IS held the message must say so, so the next reader looks at moves, "
        "terrain or an enemy instead of re-recording this finding"
    )


def test_the_existing_refusal_prefix_is_unchanged():
    """Callers (and the running session) match `ERR:CANNOT_REMOVE|Cannot remove ...` as a prefix."""
    lua = _lua()
    assert 'print("ERR:CANNOT_REMOVE|Cannot remove " .. fName .. " at (" .. unit:GetX() .. "," .. unit:GetY() .. ")" .. reason)' in lua, (
        "the reason is appended after the original message so every existing match still fires"
    )
