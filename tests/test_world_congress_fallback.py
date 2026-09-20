"""Tests for the World Congress free-vote fallback.

The fallback exists so a WC session can never cast *nothing*: when the agent has
not registered vote preferences, ``end_turn`` registers one vote per resolution
on option A / first target, which costs zero favor.

The "costs zero favor" part is not enforced in Python - it follows from the vote
handler in ``lua/congress.py`` starting at one vote with cost 0 and only walking
``for v = 2, ...``. If that loop ever starts at 1, the "free" vote silently
starts spending favor, so it is pinned here.
"""

from types import SimpleNamespace

from civ_mcp.end_turn import (
    WC_FREE_VOTE_OPTION,
    WC_FREE_VOTE_TARGET,
    build_free_vote_fallback,
)
from civ_mcp.lua.congress import build_register_wc_voter


def _res(hash_value: int):
    return SimpleNamespace(resolution_hash=hash_value)


class TestFreeVoteFallback:
    def test_one_entry_per_resolution(self):
        fallback = build_free_vote_fallback([_res(11), _res(22), _res(33)])
        assert len(fallback) == 3
        assert [f["hash"] for f in fallback] == [11, 22, 33]

    def test_each_entry_asks_for_exactly_one_vote(self):
        for entry in build_free_vote_fallback([_res(11)]):
            assert entry["votes"] == 1, "more than one vote would spend favor"

    def test_uses_option_a_and_first_target(self):
        entry = build_free_vote_fallback([_res(11)])[0]
        assert entry["option"] == WC_FREE_VOTE_OPTION == 1
        assert entry["target"] == WC_FREE_VOTE_TARGET == 0

    def test_empty_and_none_are_safe(self):
        assert build_free_vote_fallback([]) == []
        assert build_free_vote_fallback(None) == []


class TestFreeVoteStaysFree:
    """Pin the Lua invariant that makes one vote cost nothing."""

    def test_handler_starts_at_one_vote_with_zero_cost(self):
        lua = build_register_wc_voter(build_free_vote_fallback([_res(11)]))
        assert "local votesForThis = 1" in lua
        assert "local costForThis = 0" in lua

    def test_favor_is_only_budgeted_from_the_second_vote(self):
        lua = build_register_wc_voter(build_free_vote_fallback([_res(11)]))
        assert "for v = 2, math.min(maxWanted, maxV) do" in lua
        # The unregistered default path must also start at 2, or the fallback
        # would be the only free path and the default would quietly spend.
        assert "for v = 2, maxV do" in lua

    def test_unregistered_default_cannot_spend_favor(self):
        # Regression: the no-preference branch used to budget
        # floor(favor / (resLeft + 1)) per resolution, so a bare
        # queue_wc_votes([]) spent the entire favour stock blindly. It must now
        # budget nothing.
        lua = build_register_wc_voter(None)
        assert "local budgetPerRes = 0" in lua
        assert "math.floor(favor / (resLeft + 1))" not in lua
        assert "resLeft" not in lua

    def test_preference_key_is_the_stringified_hash(self):
        # The handler looks up prefs[tostring(rHash)]; a numeric key would miss.
        lua = build_register_wc_voter(build_free_vote_fallback([_res(4242)]))
        assert '["4242"] = {o=1, t=0, v=1}' in lua

    def test_no_preferences_still_registers_a_handler(self):
        # The gate's HANDLER_SET probe must be true after registration, else
        # end_turn would block for ever.
        lua = build_register_wc_voter(None)
        assert "__civmcp_wc_handler = handler" in lua
        assert "Events.WorldCongressStage1.Add(handler)" in lua
