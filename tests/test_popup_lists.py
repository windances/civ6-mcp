"""The two popup name lists must not drift apart.

There are two halves of one mechanism:

* ``spectator.PopupWatcher`` polls the InGame UI every 0.5s and, when a popup
  from ``_NONCRITICAL_POPUPS`` has been visible for a second, calls
  ``game_lifecycle.dismiss_popup`` to clear it;
* ``dismiss_popup`` knows how to clear a name only if that name is in
  ``POPUP_NAMES`` (hidden in the InGame context) or in
  ``EXCLUSIVE_POPUP_NAMES`` (closed in the popup's own Lua state).

A name the watcher detects but ``dismiss_popup`` does not know is the worst of
both worlds: it is spotted every half second, "dismissal" is attempted every
second, and the popup stays. That is not hypothetical - ``GreatWorkShowcase``
was in neither dismiss list and stayed on screen (docs/devlog/game_001, the
"Stubborn Popup Dismissal" fix), which is why it is pinned here.

The third list is a hard boundary rather than a gap: ``_CRITICAL_SCREENS``
(diplomacy and trade) must never be auto-dismissed. Closing a diplomacy session
from Lua bypasses the engine's session callbacks and hangs turn processing, and
dismissing ``DiplomacyDealView`` silently rejects an offer the agent never saw.
"""

import inspect

from civ_mcp import game_lifecycle as gl
from civ_mcp.spectator import _CRITICAL_SCREENS, _NONCRITICAL_POPUPS


def dismissible_names() -> set[str]:
    """Every popup name ``dismiss_popup`` can actually clear."""
    return set(gl.POPUP_NAMES) | set(gl.EXCLUSIVE_POPUP_NAMES)


class TestTheWatcherAndTheDismisserAgree:
    def test_every_watched_popup_is_dismissible(self):
        undismissible = sorted(set(_NONCRITICAL_POPUPS) - dismissible_names())
        assert not undismissible, (
            "PopupWatcher detects these but dismiss_popup cannot clear them, so "
            "they would be re-detected every 0.5s for ever: "
            f"{undismissible}. Add each name to GAME_LIFECYCLE.POPUP_NAMES or "
            "EXCLUSIVE_POPUP_NAMES (docs/devlog/game_001: GreatWorkShowcase)."
        )

    def test_the_check_is_not_vacuous(self):
        # Both halves must be non-empty, or the test above passes by accident.
        assert _NONCRITICAL_POPUPS
        assert gl.POPUP_NAMES
        assert gl.EXCLUSIVE_POPUP_NAMES


class TestCriticalScreensAreNeverAutoDismissed:
    def test_no_critical_screen_is_in_either_dismiss_list(self):
        overlap = sorted(set(_CRITICAL_SCREENS) & dismissible_names())
        assert not overlap, (
            "these are diplomacy/trade screens and must stay for the agent to "
            f"answer: {overlap}"
        )

    def test_the_two_named_critical_screens_are_the_documented_ones(self):
        # A rename here would silently move a session screen into the
        # dismissible set, so the names are pinned rather than assumed.
        assert set(_CRITICAL_SCREENS) == {"DiplomacyActionView", "DiplomacyDealView"}


class TestTheListsStayUsable:
    def test_no_list_repeats_a_name(self):
        for name, values in (
            ("_NONCRITICAL_POPUPS", _NONCRITICAL_POPUPS),
            ("_CRITICAL_SCREENS", _CRITICAL_SCREENS),
            ("POPUP_NAMES", gl.POPUP_NAMES),
            ("EXCLUSIVE_POPUP_NAMES", gl.EXCLUSIVE_POPUP_NAMES),
        ):
            assert len(values) == len(set(values)), f"{name} has a duplicate"

    def test_every_name_is_a_non_empty_control_name(self):
        for values in (_NONCRITICAL_POPUPS, gl.POPUP_NAMES, gl.EXCLUSIVE_POPUP_NAMES):
            for value in values:
                assert isinstance(value, str) and value.strip() == value and value

    def test_phase_2_keywords_can_find_every_exclusive_popup(self):
        # Phase 2 discovers popup states by name keyword, so a name that matches
        # none of them could only ever be reached by the explicit pre-check.
        for name in gl.EXCLUSIVE_POPUP_NAMES:
            assert any(kw in name for kw in gl.EXCLUSIVE_POPUP_KEYWORDS), (
                f"{name} matches no keyword in EXCLUSIVE_POPUP_KEYWORDS, so the "
                f"Phase 2 state scan cannot see its Lua state"
            )


class TestTheFunctionUsesTheSharedLists:
    """A copy inlined back into ``dismiss_popup`` would defeat the test above."""

    def test_dismiss_popup_reads_the_module_level_lists(self):
        source = inspect.getsource(gl.dismiss_popup)
        assert "POPUP_NAMES" in source
        assert "EXCLUSIVE_POPUP_NAMES" in source
        # The literals themselves must not be back in the body.
        assert '"InGamePopup"' not in source
        assert '"TechCivicCompletedPopup"' not in source
