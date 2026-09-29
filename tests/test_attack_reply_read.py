"""An attack reply whose HP pair is unchanged is not evidence the hit missed.

Combat resolves asynchronously, so the post-attack read inside `build_attack_unit` can still return the
pre-attack damage and the reply prints `enemy HP:72 -> 72/100` for a hit that landed. Measured
2026-09-29 in attempt A2: two landed melee attacks both answered that pair, the read right after agreed
with it, and the target then went 72 -> 50 -> 20 -> dead over the next turns. The session read the
unchanged pair as a silent failure, the pending-attack gate would not let the turn close, and it closed
with `skip_remaining_units(force=True)` - discarding a legal attack.

`AGENTS.md` already warns that a post-combat *read* is an estimate; this is the same trap one layer
earlier, in the reply line itself. The fix is a label, not a new number: the tool cannot know the
post-attack value on the resolving turn.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import game_state as gs  # noqa: E402

NOTE = "unchanged on this read"


def lua() -> str:
    return lq.build_attack_unit(2359300, 54, 25)


class TestTheReplySaysWhichNumberItPrinted:
    def test_the_note_exists_and_says_why(self):
        text = lua()
        assert NOTE in text
        assert "combat resolves asynchronously" in text
        # It must point at the way out, not just at the uncertainty.
        assert "read the target again" in text

    def test_it_is_conditional_on_the_pair_being_equal(self):
        text = lua()
        guard = text.index("if enemyAfterHP == enemyHP then")
        assert guard < text.index(NOTE)
        # It belongs to the living-target branch, so it stops before the kill branch's own reply.
        assert text.index(NOTE) < text.index("-> KILLED")

    def test_it_is_added_after_the_pair_so_the_parsers_still_read_it(self):
        text = lua()
        pair = text.index('label .. enemyHP .. " -> " .. enemyAfterHP')
        assert pair < text.index(NOTE)


class TestThePythonLayerStillReadsTheReply:
    def test_pre_hp_extraction_survives_the_note(self):
        reply = (
            "OK:MELEE_ATTACK|target:UNIT_WARRIOR at (54,25)|enemy HP:72 -> 72/100 "
            f"({NOTE} - combat resolves asynchronously, so the hit may still have landed; "
            "read the target again before concluding it missed)|your HP:100 -> 100 CS:20"
        )
        assert gs._extract_pre_hp(reply) == 72

    def test_a_real_hit_still_reads_as_one(self):
        reply = "OK:MELEE_ATTACK|target:UNIT_WARRIOR at (54,25)|enemy HP:72 -> 50/100|your HP:100 -> 100"
        assert gs._extract_pre_hp(reply) == 72
        assert NOTE not in reply
