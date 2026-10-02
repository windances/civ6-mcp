"""A siege unit is not offered a *unit* target, because the action refuses one.

`build_unused_attack_query` excludes siege units from unit targets and its docstring claims the two
legality tests "mirror each other exactly, so this report can never contradict the `CAN ATTACK` hints".
They did not: the hint scanner in `build_units_query` admitted any unit with `bomb > 0`, so attempt A2
was shown `CAN ATTACK: UNIT_ARCHER@58,23(...)` for a Catapult at T55, ordered it, and got
`ERR:SIEGE_CANNOT_ATTACK_UNITS` - one turn spent on an attack the tool itself had advertised (and the
same list offered a Catapult two Archers and a Heavy Chariot again at T66).

The action path already refuses by name (`build_attack_unit`, `attBombard > 0 and attRS == 0`); this
pins the hint to the same predicate.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import lua as lq  # noqa: E402


def units_lua() -> str:
    return lq.build_units_query()


def attack_lua() -> str:
    return lq.build_attack_unit(1310723, 50, 22)


class TestTheHintHasTheSiegeExclusion:
    def test_the_predicate_matches_the_action_path(self):
        hint = units_lua()
        action = attack_lua()
        assert "siegeNoRanged = (bomb > 0 and rs == 0)" in hint
        assert "attBombard > 0 and attRS == 0" in action
        # Same shape of test in both places: bombard, and no ranged combat to fall back on.
        assert "bomb > 0" in hint and "attBombard > 0" in action

    def test_the_scan_is_gated_on_it(self):
        hint = units_lua()
        scan = hint.index("-- Scan for attackable enemies")
        guard = hint.index("and not siegeNoRanged then", scan)
        # The gate is on the scan itself, before any target is collected.
        assert guard < hint.index("table.insert(tgtList", scan)

    def test_an_ordinary_unit_still_scans(self):
        hint = units_lua()
        # The guard must not be a blanket off-switch: the scan still requires moves and some strength.
        assert "u:GetMovesRemaining() > 0 and (cs > 0 or rs > 0 or bomb > 0)" in hint

    def test_the_reason_is_recorded_where_it_is_fixed(self):
        hint = units_lua()
        assert "SIEGE_CANNOT_ATTACK_UNITS" in hint  # the predicate's name in the comment
        assert "attack cities and districts only" in hint


class TestTheHintAlsoDropsTargetsAtSea:
    """The second contradiction of the same claim, found live T95-T97.

    `build_units_query`'s hint listed a Barbarian Galley in our own harbour as `CAN ATTACK` for the
    Heavy Chariot and the Warrior standing beside it, and `build_unused_attack_query` listed the same
    pair to the end-turn guard - while the action path refuses that order by name
    (`ERR:MELEE_CANNOT_ATTACK_AT_SEA`, manual:723). The guard could not be satisfied, so the only way
    to end a turn was `--force`, which discards the real attacks too.
    """

    def test_the_hint_applies_the_same_domain_test(self):
        hint = units_lua()
        action = attack_lua()
        assert 'iAmLandMelee = (rs == 0) and entry ~= nil and entry.Domain == "DOMAIN_LAND"' in hint
        assert "attackerIsLand" in action and 'Domain == "DOMAIN_LAND"' in action
        assert 'Domain == "DOMAIN_SEA"' in hint and "enemyIsSea" in action

    def test_the_exclusion_sits_where_the_hit_is_recorded(self):
        hint = units_lua()
        scan = hint.index("-- Scan for attackable enemies")
        exclusion = hint.index("if iAmLandMelee and targetAtSea then losOK = false end", scan)
        # It clears the same flag the LOS check uses, so the target is dropped by the existing gate
        # rather than by a second `continue` that could drift from it.
        assert exclusion < hint.index("if losOK then", scan)
        assert hint.index("if losOK then", scan) < hint.index("table.insert(tgtList", scan)

    def test_a_ranged_unit_is_not_affected(self):
        # A shooter adjacent to a ship *can* fire at it (manual:725), so the exclusion is melee-only.
        hint = units_lua()
        assert "(rs == 0) and entry ~= nil" in hint
