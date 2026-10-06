"""`get_builder_tasks` must not send a builder to a tile with an improvement it cannot build.

Measured on this match, T353-T361: the scan proposed `build MINE` at (61,35) - a FORESTED hill -
for eight consecutive turns, with a builder walking seven tiles to reach it. When the builder
finally stood on the tile the engine answered

    CANNOT_IMPROVE|unknown reason. tile has FEATURE_FOREST (use remove_feature first).
    can build here: IMPROVEMENT_LUMBER_MILL.

twice (T359 from (61,34), T361 from (61,35)), and the session recovered by ordering the Lumber Mill
the engine named. Four `improve` calls went into an improvement the tile could never take.

The cause was branch order in the empty-tile heuristic: `plot:IsHills()` was tested before the
feature, so a forested hill fell into the mine branch. These tests pin the decision order, because
the query is a Lua string and nothing else in the suite would notice a reorder.
"""

from __future__ import annotations

from civ_mcp.lua.units import build_builder_tasks_query

EMPTY_TILE_BRANCH = "elseif impIdx < 0 and resIdx < 0 and normalCount < maxNormal then"
NORMAL_TASK_PRINT = 'print("TASK|normal|'


def _empty_tile_block() -> str:
    query = build_builder_tasks_query()
    assert EMPTY_TILE_BRANCH in query, "the empty-tile branch moved; update this test with it"
    block = query.split(EMPTY_TILE_BRANCH, 1)[1]
    return block.split(NORMAL_TASK_PRINT, 1)[0]


def test_the_feature_is_read_before_the_terrain():
    block = _empty_tile_block()
    assert "featureIdx >= 0" in block and "plot:IsHills()" in block
    assert block.index("featureIdx >= 0") < block.index("plot:IsHills()"), (
        "a forested hill is a Lumber Mill tile: testing IsHills() first recommends IMPROVEMENT_MINE, "
        "which the engine refuses while the forest stands (measured T353-T361 at (61,35))"
    )


def test_a_forest_becomes_a_lumber_mill_and_a_bare_hill_a_mine():
    block = _empty_tile_block()
    assert 'fName == "FEATURE_FOREST"' in block
    assert 'bestImp = "IMPROVEMENT_LUMBER_MILL"' in block
    assert 'bestImp = "IMPROVEMENT_MINE"' in block
    forest = block.index('bestImp = "IMPROVEMENT_LUMBER_MILL"')
    mine = block.index('bestImp = "IMPROVEMENT_MINE"')
    assert forest < mine, "the forest answer has to be reached before the hill answer"


def test_jungle_and_marsh_stay_skipped():
    """They need `remove_feature` first, so the scan must not name an improvement for them."""
    block = _empty_tile_block()
    assert "Jungle/marsh need removal first, skip" in block
    # The `else` that follows the feature branch is the one that must not fire for a feature tile.
    feature_branch = block.split("if featureIdx >= 0 then", 1)[1].split("elseif plot:IsHills()", 1)[0]
    assert "IMPROVEMENT_FARM" not in feature_branch
