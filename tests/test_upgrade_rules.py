"""Upgrade rules: which classes are watched, and what the treasury loses with the discount card.

Two measured gaps this file covers, both from the T194-T217 window:

* `match-their-melee` watches melee and anti-cavalry, `upgrade-the-siege` watches siege - so the
  offers that sat unbought were exactly the classes with **no rule at all**: a Knight -> Cuirassier
  at 230g and two Crossbowman -> Field Cannon at 310g each, while the treasury went 621 -> 768 over
  twelve turns. At T216-T217 two of them were bought anyway, at the doubled price.
* T201 traded `POLICY_PROFESSIONAL_ARMY` - the game's own text is "50% discount on all unit
  upgrades" - for `POLICY_MEDINA_QUARTER` (housing) in the free policy window, and every pending
  price doubled with it (115 -> 230, 155 -> 310, 190 -> 380). Nothing said so.

The rule that closes the first gap is **staged**, not live: `prompts/checks/turn-checks.md` is
re-read every turn by a process whose metric set lives in memory, so a rule naming a metric no
running server computes reports `un-evaluable` for ever. See `prompts/checks/pending/README.md`.
"""

from __future__ import annotations

import inspect
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PENDING = ROOT / "prompts" / "checks" / "pending" / "upgrade-the-unwatched.md"
LIVE = ROOT / "prompts" / "checks" / "turn-checks.md"


def unit(kind: str, can_upgrade: bool = True, cost: int = 0, cs: int = 0):
    return types.SimpleNamespace(
        unit_type=kind, can_upgrade=can_upgrade, upgrade_cost=cost, combat_strength=cs
    )


class TestTheUnwatchedClasses:
    def test_ranged_and_cavalry_are_counted(self):
        metrics = et._uncovered_upgrade_metrics(
            {1: unit("UNIT_CROSSBOWMAN", cost=310), 2: unit("UNIT_KNIGHT", cost=230)}
        )
        assert metrics["uncovered_upgrades_available"] == 2
        assert metrics["min_uncovered_upgrade_cost"] == 230, "the cheapest is the one to act on"

    def test_the_watched_classes_are_not_counted_twice(self):
        # Melee/anti-cavalry belong to match-their-melee, siege to upgrade-the-siege: reporting
        # them here as well would put two rules on one fact.
        metrics = et._uncovered_upgrade_metrics(
            {
                1: unit("UNIT_LINE_INFANTRY", cost=200),
                2: unit("UNIT_SPEARMAN", cost=380),
                3: unit("UNIT_BOMBARD", cost=200),
                4: unit("UNIT_PIKEMAN", cost=300),
            }
        )
        assert metrics["uncovered_upgrades_available"] == 0

    def test_recon_is_left_out_on_purpose(self):
        # A Scout -> Skirmisher is not what a stalled front is waiting for, and a rule that nags
        # about one is a rule that gets ignored.
        metrics = et._uncovered_upgrade_metrics(
            {1: unit("UNIT_SCOUT", cost=125), 2: unit("UNIT_RANGER", cost=200)}
        )
        assert metrics["uncovered_upgrades_available"] == 0

    def test_a_unit_that_cannot_upgrade_is_not_counted(self):
        metrics = et._uncovered_upgrade_metrics({1: unit("UNIT_CROSSBOWMAN", can_upgrade=False)})
        assert metrics["uncovered_upgrades_available"] == 0
        assert metrics["min_uncovered_upgrade_cost"] == 0

    def test_no_units_is_zero_not_an_error(self):
        assert et._uncovered_upgrade_metrics(None)["uncovered_upgrades_available"] == 0
        assert et._uncovered_upgrade_metrics({})["min_uncovered_upgrade_cost"] == 0

    def test_the_check_context_carries_both_keys(self):
        # A rule cannot name a metric the context does not carry: turn_checks raises on one it
        # does not know, and _CONTACT_METRIC_KEYS is what a historical row is zero-filled from.
        assert "uncovered_upgrades_available" in et._CONTACT_METRIC_KEYS
        assert "min_uncovered_upgrade_cost" in et._CONTACT_METRIC_KEYS


class TestTheRuleIsStagedNotLive:
    def test_the_pending_file_names_the_metric_and_the_code(self):
        text = PENDING.read_text(encoding="utf-8-sig")
        assert "uncovered_upgrades_available" in text
        assert "_uncovered_upgrade_metrics" in text, "the staged file names the code that must ship first"
        assert "id: upgrade-the-unwatched" in text, "it carries the rule in the live file's shape"

    def test_it_is_not_in_the_live_file_yet(self):
        # Cutting it in before a server computes the metric gives a rule that reports itself
        # un-evaluable every turn - alive-looking and unsatisfiable.
        assert "upgrade-the-unwatched" not in LIVE.read_text(encoding="utf-8-sig")

    def test_the_staged_rule_does_not_duplicate_the_two_live_ones(self):
        live = LIVE.read_text(encoding="utf-8-sig")
        assert "id: match-their-melee" in live
        assert "id: upgrade-the-siege" in live


class TestTheDiscountNote:
    def test_dropping_the_card_warns_with_the_measured_cost(self):
        note = GameState(connection=None)._upgrade_discount_note(
            {"POLICY_PROFESSIONAL_ARMY", "POLICY_NATURAL_PHILOSOPHY"},
            {"POLICY_MEDINA_QUARTER", "POLICY_NATURAL_PHILOSOPHY"},
        )
        assert "UPGRADE_DISCOUNT_LOST" in note
        assert "POLICY_PROFESSIONAL_ARMY" in note
        assert "double" in note
        assert "115 -> 230" in note, "the warning carries the measured price, not a guess"

    def test_keeping_the_card_is_silent(self):
        assert (
            GameState(connection=None)._upgrade_discount_note(
                {"POLICY_PROFESSIONAL_ARMY"}, {"POLICY_PROFESSIONAL_ARMY"}
            )
            == ""
        )

    def test_moving_the_card_to_another_slot_is_silent(self):
        # The note is about losing it, not about which slot holds it.
        assert (
            GameState(connection=None)._upgrade_discount_note(
                {"POLICY_PROFESSIONAL_ARMY"}, {"POLICY_PROFESSIONAL_ARMY", "POLICY_LIBERALISM"}
            )
            == ""
        )

    def test_a_government_that_never_had_it_is_silent(self):
        assert (
            GameState(connection=None)._upgrade_discount_note(
                {"POLICY_CONSCRIPTION"}, {"POLICY_MEDINA_QUARTER"}
            )
            == ""
        )

    def test_set_policies_actually_appends_it(self):
        source = inspect.getsource(GameState.set_policies)
        assert "_upgrade_discount_note" in source
        assert "before" in source, "the pre-change read is what makes the comparison possible"
