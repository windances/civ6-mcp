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

    def test_it_is_gated_on_no_diplomacy_session_opening(self):
        """The discriminator is the session's own outcome - not an accessor that does not exist.

        The first version of this fix asked `Players[target]:IsMinorCiv()` inside a `pcall`. That
        accessor is not available in the InGame state, so the pcall swallowed the error, the flag stayed
        false, and the branch below was **dead**: attempt A3 hit `WARN:WAR_UNCERTAIN` at T59 *and* T60
        after the "fix", and a move onto the ring answered `BLOCKED (city-state territory)`. The test
        that shipped with it asserted the presence of that string in the generated Lua, which is why it
        passed while the path it described could never run.
        """
        text = lua()
        assert "IsMinorCiv" not in text and "targetIsMinor" not in text
        assert "elseif sessionCompleted then" in text
        # The operation is reached only after the session machinery has had its chance.
        assert text.index("DiplomacyManager.RequestSession") < text.index("UI.RequestPlayerOperation")

    def test_the_uncertain_warning_is_kept_for_the_session_case_only(self):
        """`WARN:WAR_UNCERTAIN` is the benign major-civilization case and must not swallow a city-state.

        It is right when a session opened and completed (the engine commits the war next frame, so the
        same-frame read is stale), and wrong when nothing opened - which is what a city-state is.
        """
        text = lua()
        uncertain = text.index("WARN:WAR_UNCERTAIN")
        assert text.index("elseif sessionCompleted then") < uncertain
        assert uncertain < text.index("OK:WAR_REQUESTED|")
        # And when neither route works the reply says no war exists rather than that it is uncertain.
        assert "ERR:WAR_BLOCKED|" in text
        assert "so no war exists" in text

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
