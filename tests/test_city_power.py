"""Power: the city fact that decided whether a building worked and that no tool could see.

Measured on this branch (T256-T272): coal sat at **70/70 with +12 a turn** and `end_turn` itself printed
`-- RESOURCE CAP: COAL 70/70 (+12/t) — excess is wasted`, oil read 0-4/70 and twice refused a unit
upgrade ("资源不足。该类型单位的升级需要1点 石油"), and a development task was putting a Research Lab
(**3 power**) into city after city - while nothing in the toolkit could say whether any city was
actually powered. The fact lived on the city banner only.

The numbers are the game's own (`DLC/Expansion2/Data/Expansion2_Buildings.xml`,
`Building_RequiredPower`; `Expansion2_Improvements.xml`; `LOC_PEDIA_CONCEPTS_PAGE_POWER_*`): Research Lab
3, Stock Exchange 3, Broadcast Center 3, Film Studio 3, Factory 2, Stadium 2, Aquatics Center 2, Food
Market 1, Shopping Mall 1, Airport 1; a Coal or Oil Power Plant turns 1 fuel into 4 power for every city
within 6 tiles, a Nuclear Plant 1 uranium into 16, a Hydroelectric Dam gives +6, a Geothermal Plant +4,
Solar/Wind/Offshore Wind +2 each. These tests hold the read, the parse, the rendering, the diary row and
the metric together, so the next time the load goes up the turn result says so.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import narrate  # noqa: E402
from civ_mcp.end_turn import _CONTACT_METRIC_KEYS, _loyalty_metrics  # noqa: E402
from civ_mcp.lua import cities as lc  # noqa: E402
from civ_mcp.lua import models as lm  # noqa: E402
from civ_mcp.lua import overview as lo  # noqa: E402

CITIES_LUA = lc.build_cities_query()
LOYALTY_LUA = lc.build_loyalty_check_query()
DIARY_LUA = lo.build_diary_full_query()


def _city_line(power: str = "5.0|4.0|0.0|no|queue a coal plant") -> str:
    """A modern CITY line: 31 legacy fields plus the five power fields the Lua appends."""
    legacy = [
        "65536", "西安", "54,27", "17",
        "1.0", "2.0", "3.0", "4.0", "5.0", "6.0",
        "7.0", "8", "9", "BUILDING_RESEARCH_LAB", "3",
        "40", "20/20", "10/10", "", "", "",
        "100.0", "100.0", "0.0", "0", "1.0", "2.0", "3",
        "", "WARRIOR", "STABLE",
    ]
    return "|".join(legacy + power.split("|"))


class TestTheLuaReadsPower:
    def test_the_city_query_reads_the_power_table(self):
        assert "c:GetPower()" in CITIES_LUA
        for call in ("GetRequiredPower", "GetFreePower", "GetTemporaryPower", "IsFullyPowered"):
            assert call in CITIES_LUA, f"the load and the sources both matter: {call} missing"
        assert "GetPowerAdvice" in CITIES_LUA, "the game's own advice is the cheapest fix to quote"

    def test_every_power_call_is_guarded(self):
        """A build without Gathering Storm has no `City:GetPower`; the read must degrade, not crash."""
        block = CITIES_LUA[CITIES_LUA.index("local pwReq, pwFree, pwTemp, pwFull") :]
        block = block[: block.index("GetPowerAdvice")]
        assert block.count("pcall(function()") >= 2
        assert "if pw ~= nil then" in block

    def test_the_city_line_carries_the_fields_last(self):
        """Appended after `loyOutcome`, which is the field the parser's index 30 ends on."""
        start = CITIES_LUA.index('print(c:GetID()')
        line = CITIES_LUA[start : CITIES_LUA.index("\n", start)]
        order = [
            line.index("loyOutcome"),
            line.index("pwReq, pwFree, pwTemp, pwFull"),
            line.index("pwAdvice"),
        ]
        assert order == sorted(order), "power must not be inserted into the middle of the line"

    def test_the_loyalty_scan_carries_power_too(self):
        """The metric has to cost no extra round trip: the loyalty scan is already one per turn."""
        for token in ("power_req:", "power_free:", "power_temp:", "powered:"):
            assert token in LOYALTY_LUA
        assert "c:GetPower()" in LOYALTY_LUA

    def test_the_diary_row_carries_power(self):
        assert "pwReq, pwAvail, pwFull" in DIARY_LUA
        assert '.. "|" .. string.format("%.1f|%.1f|%s", pwReq, pwAvail, pwFull)' in DIARY_LUA


class TestTheParse:
    def test_a_city_line_with_power_parses(self):
        cities, _ = lc.parse_cities_response([_city_line()])
        assert len(cities) == 1
        city = cities[0]
        assert city.power_required == 5.0
        assert city.power_free == 4.0
        assert city.power_temporary == 0.0
        assert city.power_fully_powered == "no"
        assert city.power_advice == "queue a coal plant"
        assert city.power_reported is True
        assert city.unpowered is True
        assert city.power_available == 4.0

    def test_a_powered_city_is_not_unpowered(self):
        cities, _ = lc.parse_cities_response([_city_line("5.0|5.0|0.0|yes|")])
        assert cities[0].unpowered is False
        assert cities[0].power_reported is True

    def test_a_city_that_needs_no_power_is_not_unpowered(self):
        cities, _ = lc.parse_cities_response([_city_line("0.0|0.0|0.0|yes|")])
        assert cities[0].unpowered is False

    def test_a_line_from_a_server_without_power_reads_as_unreported(self):
        """Back-compat: an old log line, or a pre-expansion build, must not invent a deficit."""
        legacy = _city_line().split("|")[:31]
        cities, _ = lc.parse_cities_response(["|".join(legacy)])
        assert cities[0].power_required == -1.0
        assert cities[0].power_fully_powered == ""
        assert cities[0].power_reported is False
        assert cities[0].unpowered is False

    def test_the_loyalty_parser_reads_the_power_tokens(self):
        line = (
            "CITY_LOYALTY|65536|西安|54,27|pop:17|loyalty:100.0|max:100.0|per_turn:0.00"
            "|flip:0|governor:|garrison:1|hold the line|outcome:STABLE|transfer:-1"
            "|transfer_name:|power_req:5.0|power_free:2.0|power_temp:1.0|powered:no"
        )
        rows = lc.parse_loyalty_response([line])
        assert len(rows) == 1
        assert rows[0].power_required == 5.0
        assert rows[0].power_available == 3.0
        assert rows[0].powered is False
        assert rows[0].unpowered is True

    def test_a_loyalty_line_without_power_stays_powered(self):
        line = (
            "CITY_LOYALTY|65536|西安|54,27|pop:17|loyalty:100.0|max:100.0|per_turn:0.00"
            "|flip:0|governor:|garrison:0|hold the line|outcome:STABLE|transfer:-1|transfer_name:"
        )
        rows = lc.parse_loyalty_response([line])
        assert rows[0].power_required == 0.0
        assert rows[0].powered is True
        assert rows[0].unpowered is False

    def test_the_diary_parser_reads_the_power_columns(self):
        line = (
            "PCITY|0|65536|西安|17|47.0|40.0|48.0|72.0|22.0|5.0|18.0|16|8"
            "|CAMPUS,WONDER|BUILDING_RESEARCH_LAB|100.0|0.0|5.0|4.0|no"
        )
        snapshot = lo.parse_diary_full_response([line])
        row = snapshot.cities[0]
        assert row.power_required == 5.0
        assert row.power_available == 4.0
        assert row.powered is False

    def test_a_diary_row_without_power_defaults_to_powered(self):
        line = (
            "PCITY|0|65536|西安|17|47.0|40.0|48.0|72.0|22.0|5.0|18.0|16|8"
            "|CAMPUS|BUILDING_RESEARCH_LAB|100.0|0.0"
        )
        snapshot = lo.parse_diary_full_response([line])
        row = snapshot.cities[0]
        assert row.power_required == 0.0
        assert row.powered is True


class TestTheCityLineSaysIt:
    def _city(self, **kw) -> lm.CityInfo:
        base = dict(
            city_id=65536, name="西安", x=54, y=27, population=17, food=47.0, production=40.0,
            gold=48.0, science=72.0, culture=22.0, faith=5.0, housing=18.0, amenities=16,
            turns_to_grow=3, currently_building="BUILDING_RESEARCH_LAB", production_turns_left=4,
        )
        base.update(kw)
        return lm.CityInfo(**base)

    def test_an_unpowered_city_says_so_on_its_line(self):
        text = narrate.narrate_cities(
            [self._city(power_required=5.0, power_free=2.0, power_fully_powered="no",
                        power_advice="build a power plant")]
        )
        assert "Power 2/5" in text
        assert "!! UNPOWERED" in text
        assert "build a power plant" in text

    def test_a_powered_city_reads_plain(self):
        text = narrate.narrate_cities(
            [self._city(power_required=5.0, power_free=8.0, power_fully_powered="yes")]
        )
        assert "Power 8/5" in text
        assert "UNPOWERED" not in text

    def test_an_unreported_city_says_nothing_about_power(self):
        text = narrate.narrate_cities([self._city()])
        assert "Power" not in text


class TestTheMetricAndTheStagedRule:
    def test_the_metric_counts_unpowered_cities_and_the_worst_gap(self):
        rows = [
            lm.CityLoyalty(65536, "西安", 54, 27, power_required=5.0, power_available=4.0,
                           powered=False),
            lm.CityLoyalty(131073, "北京", 57, 29, power_required=3.0, power_available=3.0,
                           powered=True),
            lm.CityLoyalty(196610, "上海", 52, 24, power_required=5.0, power_available=0.0,
                           powered=False),
        ]
        metrics = _loyalty_metrics(rows)
        assert metrics["unpowered_cities"] == 2
        assert metrics["unpowered_power_gap"] == 5.0

    def test_a_city_that_needs_nothing_is_not_counted(self):
        metrics = _loyalty_metrics([lm.CityLoyalty(1, "胶东", 54, 21)])
        assert metrics["unpowered_cities"] == 0
        assert metrics["unpowered_power_gap"] == 0.0

    def test_the_row_context_zeroes_the_metric(self):
        """A stored diary row cannot be asked about power; zero means 'not applicable', not 'zero'."""
        assert "unpowered_cities" in _CONTACT_METRIC_KEYS
        assert "unpowered_power_gap" in _CONTACT_METRIC_KEYS

    def test_the_rule_waits_for_a_server_whose_tuple_has_the_metric(self):
        staged = ROOT / "prompts/checks/pending/power-the-cities.md"
        live = ROOT / "prompts/checks/turn-checks.md"
        assert staged.exists(), "the rule is staged until a server computes the metric"
        assert "id: power-the-cities" in staged.read_text(encoding="utf-8")
        assert "metric(unpowered_cities) >= 1" in staged.read_text(encoding="utf-8")
        assert "id: power-the-cities" not in live.read_text(encoding="utf-8"), (
            "promoting it is the two-file move pending/README.md describes, and only once a "
            "server started after the _CONTACT_METRIC_KEYS change is running"
        )

class TestTheAdviceFieldIsText:
    """`GetPowerAdvice()` returns the localisation token [NEWLINE], not real line breaks.

    Measured 2026-09-29 at T1 with a freshly founded capital (西安): the advice arrived as
    "...发电：[NEWLINE][NEWLINE]在此城或附近城市中建造1座发电厂..." and reached the tool's output with
    the token intact, because the query only collapsed real control characters - so the cleanup that
    looked right did nothing. Both are collapsed now, and this asserts the token, because a regression
    here is invisible until a city exists to ask.
    """

    def test_the_query_collapses_the_newline_token(self):
        assert "%[NEWLINE%]" in CITIES_LUA, (
            "the game returns the literal [NEWLINE] markup in the power advice; the query must replace it"
        )

    def test_the_control_character_pattern_is_built_with_string_char(self):
        # A Lua escape written inside this Python string would reach the game as a real control
        # character and end the Lua literal: the unfinished-string syntax error of the same day,
        # which broke every get_cities call for as long as no session ran.
        assert "string.char(9) .. string.char(10) .. string.char(13)" in CITIES_LUA
