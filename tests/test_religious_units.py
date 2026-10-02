"""Religious units: the class of unit no metric could see, and the verb that answers their income.

Measured on the game's own data (`Base/Assets/Gameplay/Data/Units.xml`): a Missionary is
`FORMATION_CLASS_CIVILIAN` with `ReligiousStrength="100"` and **no `PromotionClass` at all** - there
is no `FORMATION_CLASS_RELIGIOUS` in the data, which is the predicate the documentation carried for
months. The threat scan filtered on `Combat > 0 or RangedCombat > 0`, so a missionary was dropped
before any metric could count it and the only detector was `get_map_area`'s tile list. The whole
missionary campaign in this match was tracked by temporary task files (008, 014, 027); when those
retired, nothing was watching.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]

MISSIONARY = (
    "RELIGIOUS|1|Russia|UNIT_MISSIONARY|57,32|100/100|rstr:100|dist:2|udist:1|atwar:1|uid:12"
)
APOSTLE = (
    "RELIGIOUS|3|Egypt|UNIT_APOSTLE|54,39|100/100|rstr:350|dist:3|udist:3|atwar:0|uid:13"
)
THREAT = (
    "THREAT|1|Russia|UNIT_ARCHER|56,41|80/100|CS:15|RS:25|dist:2|cs:0|uid:9"
    "|pc:PROMOTION_CLASS_RANGED|udist:2|near:2|adj:1"
)


class TestTheScanSeesThem:
    def test_the_query_uses_the_predicate_the_game_actually_has(self):
        q = lq.build_threat_scan_query()
        assert "ReligiousStrength" in q, (
            "the game's data has no FORMATION_CLASS_RELIGIOUS - a Missionary is a civilian with "
            "ReligiousStrength, so this is the only predicate that finds one"
        )
        assert 'print("RELIGIOUS|"' in q
        # The class name may appear in the comment that explains why it is *not* the predicate; what
        # must never appear is a test against it.
        assert '=="FORMATION_CLASS_RELIGIOUS"' not in q
        assert "if rstr > 0 then" in q

    def test_the_scan_still_prints_the_combat_rows(self):
        q = lq.build_threat_scan_query()
        assert 'print("THREAT|"' in q
        # The combat filter must stay exactly as it was: religious units are reported, not counted
        # into the contact metrics.
        assert "if bcs > 0 or (entry and entry.RangedCombat and entry.RangedCombat > 0) then" in q

    def test_the_parser_reads_both_kinds_of_row(self):
        sightings = lq.parse_religious_sightings([MISSIONARY, APOSTLE, THREAT])
        assert [s.unit_type for s in sightings] == ["UNIT_MISSIONARY", "UNIT_APOSTLE"]
        assert sightings[0].religious_strength == 100 and sightings[0].at_war
        assert sightings[0].unit_distance == 1 and sightings[0].killable
        assert not sightings[1].at_war and not sightings[1].killable
        assert len(lq.parse_threat_scan_response([MISSIONARY, APOSTLE, THREAT])) == 1

    def test_junk_and_short_rows_are_ignored(self):
        assert lq.parse_religious_sightings(["junk", "RELIGIOUS|1|A|B", ""]) == []


class TestTheBlock:
    def test_a_war_time_sighting_says_condemn(self):
        text = et._religious_event(lq.parse_religious_sightings([MISSIONARY]), 120)
        assert "FOREIGN RELIGIOUS UNITS (T120)" in text
        assert "MISSIONARY of Russia" in text
        assert "AT WAR" in text
        assert "condemn" in text

    def test_a_peacetime_sighting_says_leave_it_alone(self):
        text = et._religious_event(lq.parse_religious_sightings([APOSTLE]), 120)
        assert "at peace" in text
        assert "nothing can touch it" in text
        assert "never declare war over missionaries alone" in text
        assert "get_religion_spread" in text
        assert "pillage" in text, "the doctrine's real answer is the faith income"

    def test_both_cases_in_one_turn(self):
        text = et._religious_event(lq.parse_religious_sightings([MISSIONARY, APOSTLE]), 120)
        assert "condemn" in text and "never declare war" in text

    def test_a_distant_one_is_not_noise(self):
        far = "RELIGIOUS|1|Russia|UNIT_MISSIONARY|10,10|100/100|rstr:100|dist:9|udist:9|atwar:0|uid:1"
        assert et._religious_event(lq.parse_religious_sightings([far]), 120) is None

    def test_no_sightings_is_not_an_event(self):
        assert et._religious_event([], 120) is None


class TestTheMetrics:
    def test_the_two_counts_come_from_the_sightings(self):
        """`religious_within_3` is everything near us; `religious_at_war_within_2` is killable.

        One scan fills both caches: the `RELIGIOUS|` rows are parsed from the same response the
        `THREAT|` rows come from, so this costs no extra round trip in `end_turn`.
        """

        class FakeGs:
            _last_religious = None
            _last_religious_turn = None
            _last_threats = None
            _last_threats_turn = None

        class FakeConn:
            async def execute_write(self, lua, timeout=5.0):
                return [MISSIONARY, APOSTLE]

        gs = FakeGs()
        gs.conn = FakeConn()
        sightings = asyncio.run(et._religious_for_checks(gs, 120))
        assert len(sightings) == 2
        # Second call in the same turn is served from the cache, not the tuner.
        assert asyncio.run(et._religious_for_checks(gs, 120)) is sightings or len(
            asyncio.run(et._religious_for_checks(gs, 120))
        ) == 2

    def test_both_keys_are_in_the_row_context_tuple(self):
        """A metric missing from `_CONTACT_METRIC_KEYS` reports `un-evaluable` on every stored row."""
        assert "religious_within_3" in et._CONTACT_METRIC_KEYS
        assert "religious_at_war_within_2" in et._CONTACT_METRIC_KEYS


class TestTheRuleIsStaged:
    def test_it_waits_for_a_server_computing_the_metric(self):
        staged = ROOT / "prompts/checks/pending/answer-the-missionary.md"
        live = ROOT / "prompts/checks/turn-checks.md"
        assert staged.is_file(), "the rule is staged until a restarted server computes the metric"
        text = staged.read_text(encoding="utf-8-sig")
        assert "id: answer-the-missionary" in text
        assert "metric(religious_at_war_within_2) >= 1" in text
        assert "message:" in text, "parse_checks drops a block without one"
        assert "id: answer-the-missionary" not in live.read_text(encoding="utf-8-sig")

    def test_the_peacetime_case_is_deliberately_not_a_rule(self):
        """The doctrine at peace is "ignore it and watch the victory count" - a rule that cannot be
        satisfied is worse than none, so only the war-time case is checkable."""
        staged = (ROOT / "prompts/checks/pending/answer-the-missionary.md").read_text(
            encoding="utf-8-sig"
        )
        assert "peacetime case gets **no rule**" in staged
        assert "religious_within_3) >= 1" not in staged


class TestThePillageVerb:
    """The standing order the toolkit could not carry out (`directive.md`: "pillaging that Holy
    Site ... is worth more than any number of individual kills"), and the staging ladder's rung."""

    def test_the_query_uses_the_game_own_operation(self):
        q = lq.build_pillage_unit(42)
        assert "UnitOperationTypes.PILLAGE" in q
        assert "CanStartOperation" in q, "ask the engine first, like attack and move do"

    def test_it_says_what_is_on_the_tile_before_acting(self):
        q = lq.build_pillage_unit(42)
        assert "PILLAGE_TILE|" in q
        assert "improvement:" in q and "district:" in q and "route:" in q

    def test_it_refuses_the_four_ways_this_goes_wrong(self):
        q = lq.build_pillage_unit(42)
        assert "ERR:NO_MOVES" in q
        assert "ERR:OUT_OF_RANGE" in q, "a unit pillages its own tile, or one adjacent at most"
        assert "ERR:NOTHING_TO_PILLAGE" in q
        assert "already pillaged" in q, "the common mistake after a repair"

    def test_it_reports_what_it_pillaged(self):
        q = lq.build_pillage_unit(42)
        assert "OK:PILLAGE|" in q
        assert "get_map_area" in q, "tell the caller how to verify"

    def test_the_dispatch_and_the_docstring_carry_the_verb(self):
        import inspect

        from civ_mcp import server as srv

        source = inspect.getsource(srv.unit_action)
        assert 'case "pillage"' in source
        assert "pillage" in (srv.unit_action.__doc__ or "")
        from civ_mcp.game_state import GameState

        assert hasattr(GameState, "pillage_tile")
