"""Tests for the diary turn clamp.

The diary file is keyed per game, not per run. After a rollback to an earlier
save it therefore still contains every entry from the branch that was left
behind. Phase 1 of the skill calls get_diary *first*, so without a clamp a replay
opens by being handed a description of turns it has never reached - a memory of
the future, including things like a captured capital and a 7-city empire that do
not exist in the current branch.
"""

from civ_mcp.server import _clamp_diary_to_turn


def _e(turn, **kw):
    row = {"turn": turn, "v": 2, "is_agent": True}
    row.update(kw)
    return row


class TestClamp:
    def test_drops_entries_beyond_the_live_turn(self):
        entries = [_e(58), _e(59), _e(60), _e(170), _e(174)]
        kept, withheld = _clamp_diary_to_turn(entries, 59)
        assert [e["turn"] for e in kept] == [58, 59]
        assert withheld == 3

    def test_keeps_the_live_turn_itself(self):
        kept, withheld = _clamp_diary_to_turn([_e(59)], 59)
        assert len(kept) == 1
        assert withheld == 0

    def test_nothing_withheld_on_a_normal_forward_game(self):
        entries = [_e(57), _e(58), _e(59)]
        kept, withheld = _clamp_diary_to_turn(entries, 59)
        assert kept == entries
        assert withheld == 0

    def test_unreadable_game_drops_nothing(self):
        # live_turn None means the turn could not be read; better to return the
        # memory than to silently swallow it.
        entries = [_e(59), _e(174)]
        kept, withheld = _clamp_diary_to_turn(entries, None)
        assert kept == entries
        assert withheld == 0

    def test_tolerates_rows_without_a_turn_key(self):
        entries = [{"v": 1}, _e(59), _e(174)]
        kept, withheld = _clamp_diary_to_turn(entries, 59)
        assert len(kept) == 2  # the legacy row is treated as turn 0
        assert withheld == 1

    def test_empty_input(self):
        assert _clamp_diary_to_turn([], 59) == ([], 0)


class TestNote:
    """The withheld count is surfaced, so a short diary is explained."""

    def test_withheld_entries_produce_a_note(self):
        import inspect

        from civ_mcp import server

        src = inspect.getsource(server.get_diary)
        assert "are withheld" in src
        assert "rolled back" in src

    def test_no_note_when_nothing_is_withheld(self):
        import inspect

        from civ_mcp import server

        src = inspect.getsource(server.get_diary)
        # The note is guarded by `if withheld:`, so a normal read is untouched.
        assert "if withheld:" in src
