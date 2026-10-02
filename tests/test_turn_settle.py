"""The frame is not settled the instant the turn number moves.

Measured live T96-T97 on the running branch: the first unit read after `end_turn` answered with the
*previous* turn's values - a Warrior at 42, a Spearman at 70 and a Skirmisher at 72 where the turn's
own event lines had just said 52 / 80 / 20 - a Scout read one tile behind where it stood, and a move
issued from that read "walked" to the tile it already occupied while spending its movement points.
Minutes later every one of those reads was correct again.

`execute_end_turn` now waits for two consecutive identical unit fingerprints before it takes the
post-turn snapshot whose diff becomes the turn result's events, and says so in the result when the
board never settles. These are the pure parts of that rule, plus the wait itself against a fake
game.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp.end_turn import _settle_after_turn, unit_signature  # noqa: E402


class FakeUnit:
    def __init__(self, unit_id, x, y, health, moves):
        self.unit_id = unit_id
        self.x = x
        self.y = y
        self.health = health
        self.moves_remaining = moves


class FakeGS:
    """Hands out one reading per call, then repeats the last one."""

    def __init__(self, readings, fail_after=None):
        self.readings = list(readings)
        self.calls = 0
        self._fail_after = fail_after

    async def get_units(self):
        self.calls += 1
        if self._fail_after is not None and self.calls > self._fail_after:
            raise RuntimeError("read exploded")
        if len(self.readings) > 1:
            return self.readings.pop(0)
        return self.readings[0]


STALE = [FakeUnit(7, 51, 20, 42, 2.0), FakeUnit(17, 50, 19, 70, 2.0)]
CURRENT = [FakeUnit(7, 50, 21, 42, 2.0), FakeUnit(17, 50, 20, 70, 2.0)]


class TestTheSignature:
    def test_it_is_order_independent(self):
        assert unit_signature(CURRENT) == unit_signature(list(reversed(CURRENT)))

    def test_it_sees_the_three_fields_a_stale_frame_gets_wrong(self):
        # Position (the Scout one tile behind), health (the three HP values) and movement (the
        # restored points after a blocked transition) are each enough to make it differ.
        assert unit_signature(STALE) != unit_signature(CURRENT)
        moved = [FakeUnit(7, 51, 20, 42, 2.0)]
        assert unit_signature(moved) != unit_signature([FakeUnit(7, 51, 21, 42, 2.0)])
        assert unit_signature(moved) != unit_signature([FakeUnit(7, 51, 20, 52, 2.0)])
        assert unit_signature(moved) != unit_signature([FakeUnit(7, 51, 20, 42, 1.0)])

    def test_no_units_is_a_signature_not_an_error(self):
        assert unit_signature([]) == () and unit_signature(None) == ()


class TestTheWait:
    def test_a_settled_board_adds_nothing_to_the_result(self):
        gs = FakeGS([CURRENT])
        assert asyncio.run(_settle_after_turn(gs, pause=0.0)) == ""
        assert gs.calls == 2, "one read to establish the baseline, one to compare"

    def test_a_board_that_moves_once_is_waited_out(self):
        gs = FakeGS([STALE, CURRENT, CURRENT])
        assert asyncio.run(_settle_after_turn(gs, pause=0.0)) == ""
        assert gs.calls == 3

    def test_a_board_that_never_settles_says_so(self):
        readings = [[FakeUnit(1, x, 1, 100, 2.0)] for x in range(0, 12)]
        gs = FakeGS(readings)
        note = asyncio.run(_settle_after_turn(gs, attempts=3, pause=0.0))
        assert "still changing" in note
        assert "get_units" in note, "the note has to name the read to repeat"

    def test_a_failing_read_does_not_take_the_turn_result_with_it(self):
        gs = FakeGS([CURRENT], fail_after=0)
        assert asyncio.run(_settle_after_turn(gs, pause=0.0)) == ""
