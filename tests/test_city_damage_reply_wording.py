"""A city-attack reply must not claim "damage dealt: none" when it only means "this read did not move".

Measured in attempt A2 at T66-T67: both shots of the first war turn printed
`damage dealt:none read (city still 200/200)`, and the next `SIEGE PROGRESS` block read
`耶路撒冷: city hp 130/200 (-70 over 2 turn(s))` - the damage had landed (two Catapults, Bombard 35)
and the read was a whole turn behind it. The string had already been recorded as misleading three
times (`docs/task-history.md:377`, the naval no-op retrospective, task 021's table), and it misled this
session's own orchestrator into writing "the pool has not moved" into the attempt's record.

The fix is a claim narrow enough to be true: this read did not move, and a later read is the fact.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SOURCE = (ROOT / "src" / "civ_mcp" / "game_state.py").read_text(encoding="utf-8")


class TestTheReplyDoesNotAssertNothingHappened:
    def test_the_word_none_is_gone_from_the_city_no_read_branch(self):
        # The emitted claim is an f-string; the comment above it quotes the old string on purpose, so
        # the assertion is about what the code can print, not about the words in the file.
        assert 'f"|damage dealt:none' not in SOURCE
        assert "|damage not visible in this read (city still {city_hp}/{city_max}" in SOURCE

    def test_it_says_what_it_actually_knows(self):
        assert "damage not visible in this read" in SOURCE
        assert "a later read is the fact" in SOURCE
        assert "judge from SIEGE PROGRESS" in SOURCE

    def test_the_other_damage_branches_are_untouched(self):
        # A real delta still reports the delta, a kill still says killed, an estimate still estimates.
        assert 'f"|damage dealt:{pre_hp - city_hp}"' in SOURCE
        assert 'f"|damage dealt:{pre_hp} (killed)"' in SOURCE
        assert 'f"|est damage dealt:~{capped}"' in SOURCE

    def test_the_measurement_that_found_it_is_in_the_comment(self):
        block = SOURCE[SOURCE.index("Do NOT say") : SOURCE.index("Do NOT say") + 900]
        assert "130/200" in block and "-70 over 2 turn(s)" in block
        # And it names the earlier records, so the next reader can see it was not new.
        assert "task-history.md:377" in block
