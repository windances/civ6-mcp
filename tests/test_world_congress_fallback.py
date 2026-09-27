"""Tests for the World Congress free-vote fallback.

The fallback exists so a WC session can never cast *nothing*: when the agent has
not registered vote preferences, ``end_turn`` registers one free vote per
resolution, which costs zero favor.

Which option that vote takes, and which target it names, is decided by
``WC_FREE_VOTE_OPTION_BY_TYPE`` / ``WC_FREE_VOTE_TARGET_BY_TYPE`` - both read
from the game's own ``Expansion2_Congress.xml``. The old behaviour (always
option A, always target 0) was wrong for the four resolutions whose option A is
the ban, and for a "chosen player gains X" resolution aimed at a rival. Those
cases are pinned here.

The "costs zero favor" part is not enforced in Python - it follows from the vote
handler in ``lua/congress.py`` starting at one vote with cost 0 and only walking
``for v = 2, ...``. If that loop ever starts at 1, the "free" vote silently
starts spending favor, so it is pinned here.
"""

from types import SimpleNamespace

from civ_mcp.end_turn import (
    WC_FREE_VOTE_OPTION,
    WC_FREE_VOTE_OPTION_BY_TYPE,
    WC_FREE_VOTE_TARGET,
    WC_FREE_VOTE_TARGET_BY_TYPE,
    build_free_vote_fallback,
    free_vote_choice,
)
from civ_mcp.lua.congress import build_register_wc_voter


def _res(hash_value: int, resolution_type: str = "", **extra):
    """A resolution stub. With no ``resolution_type`` it takes the defaults."""
    fields = {"resolution_hash": hash_value, "resolution_type": resolution_type}
    fields.update(extra)
    return SimpleNamespace(**fields)


class TestFreeVoteFallback:
    def test_one_entry_per_resolution(self):
        fallback = build_free_vote_fallback([_res(11), _res(22), _res(33)])
        assert len(fallback) == 3
        assert [f["hash"] for f in fallback] == [11, 22, 33]

    def test_each_entry_asks_for_exactly_one_vote(self):
        for entry in build_free_vote_fallback([_res(11)]):
            assert entry["votes"] == 1, "more than one vote would spend favor"

    def test_an_unknown_resolution_keeps_the_old_defaults(self):
        entry = build_free_vote_fallback([_res(11)])[0]
        assert entry["option"] == WC_FREE_VOTE_OPTION == 1
        assert entry["target"] == WC_FREE_VOTE_TARGET == 0

    def test_empty_and_none_are_safe(self):
        assert build_free_vote_fallback([]) == []
        assert build_free_vote_fallback(None) == []

    def test_local_player_id_defaults_to_the_single_player_human(self):
        # Not passed = player 0, which is the human in single-player.
        assert free_vote_choice(_res(1)) == (WC_FREE_VOTE_OPTION, WC_FREE_VOTE_TARGET)


class TestOptionIsChosenPerResolution:
    """Option A is the buff side of most resolutions - not of these."""

    def test_the_resolutions_whose_ban_is_on_a_take_option_b(self):
        for resolution_type in (
            "WC_RES_MERCENARY_COMPANIES",
            "WC_RES_GLOBAL_ENERGY_TREATY",
            "WC_RES_DEFORESTATION_TREATY",
            "WC_RES_ESPIONAGE_PACT",
        ):
            option, _target = free_vote_choice(_res(7, resolution_type))
            assert option == 2, (
                f"{resolution_type} has its ban/dead option on A "
                f"(Expansion2_Congress.xml), so the free vote must be B"
            )

    def test_the_punish_resolutions_take_b_on_someone_else(self):
        # These two only become B once a target that is not us is on the ballot.
        for resolution_type in ("WC_RES_ARMS_CONTROL", "WC_RES_BORDER_CONTROL"):
            res = _res(
                7,
                resolution_type,
                target_kind="PLAYER",
                possible_targets=["0:Us", "2:Rival"],
            )
            assert free_vote_choice(res, local_player_id=0) == (2, 2)

    def test_every_mapped_type_is_a_resolution_type_and_an_option(self):
        for resolution_type, option in WC_FREE_VOTE_OPTION_BY_TYPE.items():
            assert resolution_type.startswith("WC_RES_")
            assert option in (1, 2)

    def test_an_unmapped_known_resolution_stays_on_a(self):
        option, _target = free_vote_choice(_res(7, "WC_RES_SOVEREIGNTY"))
        assert option == 1


class TestTargetIsChosenPerResolution:
    """A gain goes to us; a loss never does."""

    def _players(self, *ids):
        # lua/congress.py prints PLAYER-kind targets as "<player id>:<name>".
        return [f"{pid}:Player {pid}" for pid in ids]

    def test_a_gain_aims_at_us(self):
        res = _res(
            7,
            "WC_RES_DIPLOVICTORY",
            target_kind="PLAYER",
            possible_targets=self._players(2, 0, 7),
        )
        option, target = free_vote_choice(res, local_player_id=0)
        assert option == 1, "A is 'Chosen Player gains 2 Diplomatic Victory points'"
        assert target == 0, "the gain must be aimed at our own player id"

    def test_a_gain_we_cannot_take_becomes_a_loss_for_someone_else(self):
        # A grants the target +2 DVP and B takes 2 away, so with us off the
        # ballot the useful vote is B on a rival, not A on a rival.
        res = _res(
            7,
            "WC_RES_DIPLOVICTORY",
            target_kind="PLAYER",
            possible_targets=self._players(2, 7),
        )
        assert free_vote_choice(res, local_player_id=0) == (2, 2)

    def test_a_loss_never_aims_at_us(self):
        res = _res(
            7,
            "WC_RES_ARMS_CONTROL",
            target_kind="PLAYER",
            possible_targets=self._players(0, 2, 7),
        )
        option, target = free_vote_choice(res, local_player_id=0)
        assert option == 2, "B strips the target's weapons of mass destruction"
        assert target == 2, "the first target that is not us"

    def test_a_loss_with_only_us_on_the_ballot_keeps_the_default_side(self):
        # B would disarm us; the untouched default (A on index 0) at least
        # cannot hurt us, because A is the additive side of this resolution.
        res = _res(
            7,
            "WC_RES_BORDER_CONTROL",
            target_kind="PLAYER",
            possible_targets=self._players(0),
        )
        assert free_vote_choice(res, local_player_id=0) == (
            WC_FREE_VOTE_OPTION,
            WC_FREE_VOTE_TARGET,
        )

    def test_a_non_player_kind_never_gets_a_player_target(self):
        # Its list entries are 0-based indexes into resources/districts/etc, so
        # "not us" is meaningless and the index-0 default has to stand.
        res = _res(
            7,
            "WC_RES_ARMS_CONTROL",
            target_kind="RESOURCE",
            possible_targets=["0:Diamonds", "1:Silk"],
        )
        assert free_vote_choice(res, local_player_id=0) == (
            WC_FREE_VOTE_OPTION,
            WC_FREE_VOTE_TARGET,
        )

    def test_a_missing_target_list_is_safe(self):
        res = _res(7, "WC_RES_DIPLOVICTORY", target_kind="PLAYER")
        assert free_vote_choice(res, local_player_id=0) == (1, 0)

    def test_every_mapped_target_rule_is_known(self):
        for resolution_type, rule in WC_FREE_VOTE_TARGET_BY_TYPE.items():
            assert resolution_type.startswith("WC_RES_")
            assert rule in ("self", "not_self", "first")

    def test_every_not_self_type_declares_its_own_option(self):
        # A "not_self" type aims the option table's side at someone else and
        # falls back to option A when it cannot, so that side has to have been
        # chosen for that resolution on purpose - an implicit A would silently
        # hand the benefit of a "punish" resolution to a rival.
        for resolution_type, rule in WC_FREE_VOTE_TARGET_BY_TYPE.items():
            if rule == "not_self":
                assert resolution_type in WC_FREE_VOTE_OPTION_BY_TYPE, (
                    f"{resolution_type} needs an explicit option, because its "
                    f"target rule is {rule!r}"
                )


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
