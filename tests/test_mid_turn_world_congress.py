"""Tests for the mid-turn World Congress probe.

A *special session* (an emergency) can open during ACTION_ENDTURN, after the gate
in execute_end_turn has already run, so no vote handler is registered and the game
waits for submissions nobody makes. Observed live on 2026-09-20 T169: capturing
Russia's original capital convened a special session, the turn burned the full
593s poll budget, and only a manual vote in the game UI let it advance.

The probe votes and submits directly. The one rule that must never break: it
spends **no** favour - every vote it casts is the free one.
"""

import asyncio

import pytest

from civ_mcp.end_turn import (
    WC_FREE_VOTE_OPTION,
    WC_FREE_VOTE_TARGET,
    _check_mid_turn_world_congress,
)


class _Res:
    def __init__(self, h):
        self.resolution_hash = h


class _Status:
    def __init__(self, in_session, resolutions=()):
        self.is_in_session = in_session
        self.resolutions = list(resolutions)


class FakeGS:
    """Records everything the probe does to the game."""

    def __init__(self, status=None, fail_query=False, fail_submit=False, fail_vote_on=()):
        self._status = status
        self._fail_query = fail_query
        self._fail_submit = fail_submit
        self._fail_vote_on = set(fail_vote_on)
        self.votes: list[tuple] = []
        self.submits = 0

    async def get_world_congress(self):
        if self._fail_query:
            raise RuntimeError("query exploded")
        return self._status

    async def vote_world_congress(self, resolution_hash, option, target_index, num_votes):
        if resolution_hash in self._fail_vote_on:
            raise RuntimeError("vote rejected")
        self.votes.append((resolution_hash, option, target_index, num_votes))
        return "OK:VOTED"

    async def submit_congress(self):
        if self._fail_submit:
            raise RuntimeError("submit exploded")
        self.submits += 1
        return "OK:CONGRESS_SUBMITTED"


def run(gs):
    return asyncio.run(_check_mid_turn_world_congress(gs))


class TestNoSession:
    def test_not_in_session_does_nothing(self):
        gs = FakeGS(_Status(False, [_Res(1)]))
        assert run(gs) is None
        assert gs.votes == []
        assert gs.submits == 0

    def test_query_failure_is_swallowed(self):
        gs = FakeGS(_Status(True, [_Res(1)]), fail_query=True)
        assert run(gs) is None
        assert gs.votes == []
        assert gs.submits == 0


class TestOpenSession:
    def test_votes_once_per_resolution_then_submits(self):
        gs = FakeGS(_Status(True, [_Res(11), _Res(22)]))
        note = run(gs)
        assert note is not None
        assert len(gs.votes) == 2
        assert [v[0] for v in gs.votes] == [11, 22]
        assert gs.submits == 1
        assert "2" in note

    def test_session_with_no_resolutions_still_submits(self):
        # Nothing to vote on, but the session still has to be submitted or the
        # turn stays stuck.
        gs = FakeGS(_Status(True, []))
        note = run(gs)
        assert note is not None
        assert gs.votes == []
        assert gs.submits == 1

    def test_a_failing_vote_does_not_stop_the_others(self):
        gs = FakeGS(_Status(True, [_Res(11), _Res(22), _Res(33)]), fail_vote_on={22})
        note = run(gs)
        assert note is not None
        assert [v[0] for v in gs.votes] == [11, 33]
        assert gs.submits == 1
        assert "2" in note  # only the two that succeeded are reported


class TestNeverSpendsFavour:
    def test_every_vote_is_the_single_free_one(self):
        gs = FakeGS(_Status(True, [_Res(1), _Res(2), _Res(3)]))
        run(gs)
        assert gs.votes, "expected votes"
        for _hash, option, target, num_votes in gs.votes:
            assert num_votes == 1, "more than one vote would spend diplomatic favour"
            assert option == WC_FREE_VOTE_OPTION == 1
            assert target == WC_FREE_VOTE_TARGET == 0

    def test_submit_failure_reports_nothing_rather_than_claiming_success(self):
        gs = FakeGS(_Status(True, [_Res(1)]), fail_submit=True)
        assert run(gs) is None
        assert gs.submits == 0


@pytest.mark.parametrize("count", [1, 4])
def test_reported_count_matches_votes_cast(count):
    gs = FakeGS(_Status(True, [_Res(i) for i in range(count)]))
    note = run(gs)
    assert note is not None
    assert str(count) in note
