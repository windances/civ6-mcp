"""Upgrade rules: which classes are watched, and what the treasury loses with the discount card.

Two measured gaps this file covers, both from the T194-T217 window:

* `match-their-melee` watches melee and anti-cavalry, `upgrade-the-siege` watches siege - so the
  offers that sat unbought were exactly the classes with **no rule at all**: a Knight -> Cuirassier
  at 230g and two Crossbowman -> Field Cannon at 310g each, while the treasury went 621 -> 768 over
  twelve turns. At T216-T217 two of them were bought anyway, at the doubled price.
* T201 traded `POLICY_PROFESSIONAL_ARMY` - the game's own text is "50% discount on all unit
  upgrades" - for `POLICY_MEDINA_QUARTER` (housing) in the free policy window, and every pending
  price doubled with it (115 -> 230, 155 -> 310, 190 -> 380). Nothing said so.

The rule that closes the first gap was **staged** until a server computing its metric was running:
`prompts/checks/turn-checks.md` is re-read every turn by a process whose metric set lives in memory,
and a rule naming a metric no running server computes reports `un-evaluable` for ever
(`prompts/checks/pending/README.md`). The code shipped in `cb24e58`, the session that started at T218
ran it, and the rule was cut into `turn-checks.md` at T220. `TestTheRuleIsLive` drives the shipped
expression through the engine, which is what makes "the server can compute it" a check rather than an
assumption.
"""

from __future__ import annotations

import inspect
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PENDING = ROOT / "prompts" / "checks" / "pending" / "upgrade-the-unwatched.md"
PENDING_DISCOUNT = ROOT / "prompts" / "checks" / "pending" / "keep-the-upgrade-discount.md"
LIVE = ROOT / "prompts" / "checks" / "turn-checks.md"


def unit(kind: str, can_upgrade: bool = True, cost: int = 0, cs: int = 0):
    return types.SimpleNamespace(
        unit_type=kind, can_upgrade=can_upgrade, upgrade_cost=cost, combat_strength=cs
    )


def context(**metrics) -> turn_checks.CheckContext:
    """A context carrying exactly the metrics a rule names, and nothing else."""
    return turn_checks.CheckContext(turn=220, units={}, metrics=dict(metrics), researched=frozenset())


def _live_rule(check_id: str) -> turn_checks.TurnCheck:
    """One rule, read out of the shipped file rather than restated in this file."""
    checks = turn_checks.parse_checks(LIVE.read_text(encoding="utf-8-sig"))
    found = [check for check in checks if check.check_id == check_id]
    assert len(found) == 1, f"{check_id!r} is not exactly one rule in {LIVE.name}"
    return found[0]


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


class TestTheRuleIsLive:
    def test_the_staged_file_is_gone(self):
        # The staging directory is empty in the normal state, and the same line is held for the two
        # rules promoted before this one in tests/test_camp_rules.py.
        assert not PENDING.exists(), (
            "the rule moved up to turn-checks.md; a staged copy left behind is one fact in two places"
        )

    def test_it_is_in_the_live_file_with_its_measured_evidence(self):
        live = LIVE.read_text(encoding="utf-8-sig")
        assert "id: upgrade-the-unwatched" in live
        for measured in ("621 -> 768", "230g", "310g", "540g", "270g"):
            assert measured in live, f"the rule's message lost the measurement {measured!r}"
        assert "upgrade_unit" in live

    def test_the_engine_evaluates_it_in_this_build(self):
        # The reason it was staged at all: a metric the running process does not carry makes this
        # raise CheckError, which end_turn reports as `un-evaluable`. Driving the shipped expression
        # from the shipped file is what proves the promotion was safe.
        rule = _live_rule("upgrade-the-unwatched")
        rich = context(at_war=1, uncovered_upgrades_available=2, gold=600, min_uncovered_upgrade_cost=230)
        assert bool(turn_checks.evaluate(rule.when, rich)) is True, "the war gate did not open"
        assert bool(turn_checks.evaluate(rule.require, rich)) is False, "two offers must fail it"
        clear = context(at_war=1, uncovered_upgrades_available=0, gold=600, min_uncovered_upgrade_cost=0)
        assert bool(turn_checks.evaluate(rule.require, clear)) is True, "a clear class must pass it"

    def test_it_asks_only_when_the_treasury_can_pay_twice(self):
        # The gate is what keeps the rule from nagging a treasury that can barely afford one upgrade:
        # it is about gold that is *sitting*, not about gold that could be spent.
        rule = _live_rule("upgrade-the-unwatched")
        thin = context(at_war=1, uncovered_upgrades_available=1, gold=240, min_uncovered_upgrade_cost=230)
        assert bool(turn_checks.evaluate(rule.when, thin)) is False
        at_peace = context(at_war=0, uncovered_upgrades_available=1, gold=600, min_uncovered_upgrade_cost=230)
        assert bool(turn_checks.evaluate(rule.when, at_peace)) is False

    def test_the_two_watched_classes_keep_their_rules(self):
        # The new rule reports what the other two do not, so they must still be there.
        live = LIVE.read_text(encoding="utf-8-sig")
        assert "id: match-their-melee" in live
        assert "id: upgrade-the-siege" in live


class TestTheDiscountGate:
    """T201 traded Professional Army for housing and every price doubled; nothing said so.

    The change-time warning covers the moment the card is dropped. This covers the *state*: the card
    is absent and an upgrade is one policy change away from being affordable - which is the case
    `UPGRADE AVAILABLE` used to answer by saying nothing at all (measured T224: 208 gold against a
    310g offer).
    """

    def test_only_the_offers_the_card_would_make_affordable_are_counted(self):
        units = {
            1: unit("UNIT_CROSSBOWMAN", cost=310),  # 155 affordable at 208 gold, 310 is not
            2: unit("UNIT_BOMBARD", cost=200),  # affordable either way: the card is not the obstacle
            3: unit("UNIT_SPEARMAN", cost=900),  # affordable neither way: gold is the obstacle
        }
        gated = et._gated_by_discount(units, gold=208.0, policies=["POLICY_MEDINA_QUARTER"])
        assert [row[0] for row in gated] == ["UNIT_CROSSBOWMAN"]

    def test_the_card_in_the_government_switches_it_off(self):
        units = {1: unit("UNIT_CROSSBOWMAN", cost=310)}
        assert et._gated_by_discount(units, 208.0, ["POLICY_PROFESSIONAL_ARMY"]) == []

    def test_a_snapshot_without_policies_claims_nothing(self):
        units = {1: unit("UNIT_CROSSBOWMAN", cost=310)}
        assert et._gated_by_discount(units, 208.0, None) == []

    def test_the_constant_is_the_one_the_change_warning_uses(self):
        assert et._UPGRADE_DISCOUNT_POLICY == GameState.UPGRADE_DISCOUNT_POLICY

    def test_the_block_reports_an_upgrade_nobody_can_afford_yet(self):
        text = et._upgrade_event(
            {1: unit("UNIT_CROSSBOWMAN", cost=310)}, 208.0, 224, ["POLICY_MEDINA_QUARTER"]
        )
        assert text, "the silent case is exactly the one the block has to speak about"
        assert "nothing is affordable at the quoted price" in text
        assert "155g" in text and "POLICY_PROFESSIONAL_ARMY" in text

    def test_the_block_stays_quiet_with_the_card_in_the_government(self):
        text = et._upgrade_event(
            {1: unit("UNIT_CROSSBOWMAN", cost=310)}, 208.0, 224, ["POLICY_PROFESSIONAL_ARMY"]
        )
        assert text is None, "with the discount slotted the offer is simply not affordable yet"

    def test_a_listed_offer_needs_no_note(self):
        # The note is for the silent case; a price that is on the page is its own signal, and the
        # class rules (`upgrade-the-unwatched`, `upgrade-the-siege`) nag about buying it.
        text = et._upgrade_event(
            {1: unit("UNIT_CROSSBOWMAN", cost=310)}, 400.0, 224, ["POLICY_MEDINA_QUARTER"]
        )
        assert text and "cost 310g" in text
        assert "NOTE:" not in text


class TestTheUpgradeMetricsAreWired:
    def test_every_upgrade_metric_family_is_computed(self):
        # A key listed in `_CONTACT_METRIC_KEYS` and never computed is worse than an unknown one: a
        # historical row zero-fills it, so a rule naming it would be silently always-zero instead of
        # loudly un-evaluable - which is the failure the staging convention exists to prevent. All
        # three families are wired: siege and the uncovered classes from the unit list, melee from
        # `_matchup_metrics` (it also needs the threat scan).
        contact = inspect.getsource(et._contact_metrics)
        assert "_siege_upgrade_metrics(units)" in contact
        assert "_uncovered_upgrade_metrics(units)" in contact
        assert "_matchup_metrics(threats, units)" in contact, "the melee family has to be called"
        assert '"upgrades_gated_by_discount"' in contact
        assert "melee_upgrades_available" in inspect.getsource(et._matchup_metrics)


class TestTheDiscountRuleIsLive:
    """Cut in at T220: the session playing the T218 save runs the code that computes the metric."""

    def test_the_staged_file_is_gone(self):
        assert not PENDING_DISCOUNT.exists(), (
            "the rule moved up to turn-checks.md; a staged copy left behind is one fact in two places"
        )

    def test_it_is_in_the_live_file_with_its_measured_evidence(self):
        live = LIVE.read_text(encoding="utf-8-sig")
        assert "id: keep-the-upgrade-discount" in live
        for measured in ("115 -> 230", "155 -> 310", "190 -> 380", "540g", "270g"):
            assert measured in live, f"the rule's message lost the measurement {measured!r}"

    def test_the_engine_evaluates_it_in_this_build(self):
        rule = _live_rule("keep-the-upgrade-discount")
        fired = context(upgrades_gated_by_discount=1)
        quiet = context(upgrades_gated_by_discount=0)
        assert bool(turn_checks.evaluate(rule.when, fired)) is True
        assert bool(turn_checks.evaluate(rule.require, fired)) is False
        assert bool(turn_checks.evaluate(rule.require, quiet)) is True


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
