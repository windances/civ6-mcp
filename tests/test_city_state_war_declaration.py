"""The city-state war path: the game's own player operation, not a diplomacy session.

Attempt A2 staged its army on 耶路撒冷's ring at T57 and then spent T60-T65 declaring war with no
effect: `send_diplomatic_action` opens a **diplomacy session** (`diplomacy.py:414-427`), a city-state
has none to open, so `FindOpenSessionID` returns nil and the code falls through to the
`WARN:WAR_UNCERTAIN` message written for the benign "not synced yet" case. The border diagnostic
(`BLOCKED (city-state territory - need suzerainty or Open Borders)`) and `attack` answering
`NOT_AT_WAR` confirmed independently that no war existed, and the attempt's capture half was blocked by
the tool rather than by the map, the doctrine or the production.

The fix is the branch the game's own popup takes when there is no casus belli
(`Base/Assets/UI/Popups/DeclareWarPopup.lua:76-82`), which is the branch a city-state always takes.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import lua as lq  # noqa: E402


def lua(action: str = "DECLARE_SURPRISE_WAR") -> str:
    return lq.build_send_diplo_action(6, action)


class TestTheMinorCivBranchExists:
    def test_it_uses_the_player_operation_the_game_uses(self):
        text = lua()
        assert "PlayerOperations.DIPLOMACY_DECLARE_WAR" in text
        assert "UI.RequestPlayerOperation" in text
        assert "parameters[PlayerOperations.PARAM_PLAYER_ONE] = me" in text
        assert "parameters[PlayerOperations.PARAM_PLAYER_TWO] = target" in text

    def test_it_is_gated_on_the_target_being_a_city_state(self):
        text = lua()
        assert "Players[target]:IsMinorCiv()" in text
        # It runs before the session machinery, so a city-state never reaches RequestSession.
        assert text.index("targetIsMinor") < text.index("DiplomacyManager.RequestSession")

    def test_it_returns_before_the_session_path(self):
        text = lua()
        minor = text.index("if targetIsMinor then")
        early = text[minor : text.index("DiplomacyManager.RequestSession")]
        assert "return" in early
        # The early path emits the sentinel the collector stops at, so the caller never waits for the
        # session machinery it skipped.
        assert f'print("{lq.SENTINEL}")' in text
        assert early.index(f'print("{lq.SENTINEL}")') < early.index("return")

    def test_the_reply_says_what_was_done_rather_than_that_it_is_uncertain(self):
        text = lua()
        assert "OK:WAR_REQUESTED|" in text
        assert "confirm it with get_diplomacy" in text

    def test_it_does_not_touch_non_war_actions(self):
        for action in ("DIPLOMATIC_DELEGATION", "DECLARE_FRIENDSHIP", "DENOUNCE"):
            text = lua(action)
            assert "targetIsMinor" not in text, action
            assert "DiplomacyManager.RequestSession" in text, action

    def test_the_war_action_still_validates_before_declaring(self):
        text = lua()
        # CanDeclareWarOn must still be consulted, and before the operation is requested.
        assert "CanDeclareWarOn" in text
        assert text.index("CanDeclareWarOn") < text.index("UI.RequestPlayerOperation")
