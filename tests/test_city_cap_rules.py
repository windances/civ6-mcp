"""The four checks the Development section orders before choosing production, made measurable.

The directive tells the turn loop to look at what caps a city - housing, food, amenities, a pillaged
district - before it queues anything, and none of it was in the metric set: a rule could name `pop`
and `cities` and nothing else about a city at all. `unpowered_cities` could see the *symptom*
(measured T291: the power-shortage warning fired four times while Xi'an queued a project) and nothing
could see the cause.

Every number comes off `CityInfo`, which the existing city scan already fills, so this needed no new
Lua and no extra round trip. The amenities half needed one thing more: the scan computed the demand
(`amNeed`) and then printed only the gross figure (`amNeed + GetAmenities()`), which is meaningless
on its own because the demand scales with population. `amenities_needed` is that column, appended
after the power block so a log written before it existed parses exactly as before.

The three rules that read these metrics are staged in `prompts/checks/pending/` rather than live,
because `_CONTACT_METRIC_KEYS` is read at *import* time: a server process older than this commit
would report `un-evaluable` on every turn, which reads as a permanent failing streak.
"""

from __future__ import annotations

import pathlib
import sys
import types

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn  # noqa: E402
from civ_mcp.lua.cities import parse_cities_response  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PENDING = ROOT / "prompts" / "checks" / "pending"
LIVE = ROOT / "prompts" / "checks" / "turn-checks.md"

# One row in the shape `build_cities_query` prints: 37 fields, `amNeed` last.
#         0  1      2     3   4     5     6     7      8      9     10    11 12 13         14 15
XIAN_ROW = (
    "1|Xi'an|10,20|16|10.0|20.0|5.0|65.1|10.0|2.0|11.0|12|5|PRODUCING|1|47"
    # 16      17        18 19                        20            21     22     23    24
    "|200/200|400/400||DISTRICT_INDUSTRIAL_ZONE|CAMPUS@11,20|100.0|100.0|0.0|0"
    # 25    26     27 28                   29              30      31    32    33    34    35 36
    "|2.0|30.0|60|WORKSHOP;FACTORY|UNIT_SPEARMAN|STABLE|4.0|0.0|0.0|FULL|ok|4"
)

# Housing 12 against pop 12 is the hard stop; the amenity demand is 6 against 5 gross, which is the
# only reading in which `amenities` means anything at all.
CHANGSHA_ROW = (
    "2|Changsha|52,29|12|3.0|8.0|2.0|20.0|5.0|1.0|12.0|5|14|DISTRICT_AQUEDUCT|14|31"
    "|100/100|0/0||||100.0|100.0|0.0|0"
    "|0.0|12.0|40|||GAINING_LOYALTY|0.0|0.0|0.0|||6"
)

CAP_METRICS = (
    "pillaged_districts",
    "pillaged_buildings",
    "cities_pillaged",
    "housing_slack",
    "cities_housing_capped",
    "food_stalled",
    "amenities_floor",
    "cities_unhappy",
)

STAGED_RULES = (
    "repair-the-pillaged-district",
    "mind-the-housing-cap",
    "mind-the-amenities",
)


def _gs(*rows: str):
    """A GameState stub carrying only what `_city_health_metrics` reads."""
    cities, _ = parse_cities_response(list(rows))
    assert cities, "the fixture rows did not parse - the field layout in this test is wrong"
    snapshot = types.SimpleNamespace(cities={city.city_id: city for city in cities})
    return types.SimpleNamespace(_last_snapshot=snapshot)


def test_the_amenity_demand_column_parses_at_the_end_of_the_row():
    """The column is appended *after* the power block, so it must not shift an earlier field."""
    cities, _ = parse_cities_response([XIAN_ROW])
    city = cities[0]
    assert city.amenities == 12, "the gross figure moved"
    assert city.amenities_needed == 4
    assert city.power_fully_powered == "FULL", "the power block moved"
    assert city.garrison_unit == "UNIT_SPEARMAN"
    assert city.housing == 11.0
    assert city.population == 16


def test_a_row_without_the_column_reads_as_no_demand_rather_than_a_guess():
    """A log or a server older than the column must switch the amenity rule off, not fire it."""
    cities, _ = parse_cities_response(["|".join(XIAN_ROW.split("|")[:36])])
    assert cities[0].amenities_needed == 0
    metrics = end_turn._city_health_metrics(_gs("|".join(XIAN_ROW.split("|")[:36])))
    assert metrics["cities_unhappy"] == 0, "a missing demand column invented an unhappy city"
    assert metrics["amenities_floor"] >= 0


def test_the_cause_of_the_t291_power_shortage_is_counted_not_just_the_symptom():
    metrics = end_turn._city_health_metrics(_gs(XIAN_ROW))
    assert metrics["pillaged_districts"] == 1
    assert metrics["pillaged_buildings"] == 2
    assert metrics["cities_pillaged"] == 1
    assert metrics["housing_slack"] == -5.0, "the worst city's slack is the number a plan closes"
    assert metrics["food_stalled"] == 0, "2.0 food/t is not a stalled city"


def test_a_housing_cap_is_the_hard_stop_the_reference_says_it_is():
    metrics = end_turn._city_health_metrics(_gs(CHANGSHA_ROW))
    assert metrics["housing_slack"] == 0.0
    assert metrics["cities_housing_capped"] == 1
    assert metrics["food_stalled"] == 1
    assert metrics["amenities_floor"] == -1
    assert metrics["cities_unhappy"] == 1


def test_the_worst_city_reports_across_the_empire_not_the_last_one_read():
    """One stalled city that is also the science city is the whole empire's problem."""
    metrics = end_turn._city_health_metrics(_gs(XIAN_ROW, CHANGSHA_ROW))
    assert metrics["housing_slack"] == -5.0
    assert metrics["amenities_floor"] == -1
    assert metrics["cities_housing_capped"] == 2
    assert metrics["cities_pillaged"] == 1


def test_no_snapshot_turns_the_rules_off_instead_of_firing_them():
    bare = types.SimpleNamespace()
    assert end_turn._city_health_metrics(bare) == dict.fromkeys(CAP_METRICS, 0)
    empty = types.SimpleNamespace(_last_snapshot=types.SimpleNamespace(cities={}))
    assert end_turn._city_health_metrics(empty) == dict.fromkeys(CAP_METRICS, 0)


def test_every_cap_metric_is_in_the_import_time_tuple():
    """A metric absent from this tuple reports `un-evaluable` on a stored-row pass - which reads as
    a permanent failing streak and shifts the turn verdict, so the tuple is not decoration."""
    for name in CAP_METRICS:
        assert name in end_turn._CONTACT_METRIC_KEYS, f"{name} is computed but not registered"


@pytest.mark.parametrize("rule_id", STAGED_RULES)
def test_the_rule_is_staged_and_not_yet_live(rule_id: str):
    """Cutting one of these into `turn-checks.md` before a server computes its metric would put a
    rule in force that nobody can satisfy. Promotion is the two-file move `pending/README.md`
    describes; when it happens this assertion flips to `in live` and the staged file is deleted."""
    assert (PENDING / f"{rule_id}.md").exists(), f"{rule_id} is not staged"
    assert f"id: {rule_id}" not in LIVE.read_text(encoding="utf-8-sig"), (
        f"{rule_id} is live while its staged file still exists"
    )
