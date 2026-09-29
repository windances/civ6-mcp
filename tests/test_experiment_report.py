"""The experiment report's arithmetic, on synthetic rows.

The instrument decides whether an attempt held its hypothesis, so its two load-bearing functions are
pinned here: the role mapping (a unit type that is not mapped is silently invisible, which would
report a phantom shortfall) and the establishment scan (a table that fills on T47 must be found on
T47, not on the next ten-turn boundary).

The inputs are **diary-shaped rows**, because that is the tool's contract: a row carries the turn and
a `unit_composition` field. Handing it a bare composition dict is a mistake the tool cannot see, so
`frames()` builds the real shape and every test goes through it.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "experiment_report", ROOT / "scripts" / "experiment-report.py"
)
assert spec and spec.loader
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

FULL = {"CATAPULT": 2, "WARRIOR": 2, "BATTERING_RAM": 1, "ARCHER": 4, "HORSEMAN": 1}


def frames(by_turn: dict[int, dict]) -> dict[int, dict]:
    """A diary frame per turn: the shape `diary_rows()` hands the tool."""
    return {turn: {"turn": turn, "is_agent": True, "unit_composition": comp} for turn, comp in by_turn.items()}


def test_role_counts_maps_upgrade_lines_and_ignores_civilians():
    counts = report.role_counts(
        {
            "WARRIOR": 1,
            "SWORDSMAN": 1,
            "CATAPULT": 2,
            "BATTERING_RAM": 1,
            "ARCHER": 3,
            "SLINGER": 1,
            "HORSEMAN": 1,
            "BUILDER": 4,
            "TRADER": 2,
            "GREAT_ENGINEER": 1,
            "SCOUT": 2,
        }
    )
    assert counts["siege"] == 2
    assert counts["melee"] == 2
    assert counts["ram"] == 1
    assert counts["ranged"] == 4  # Archer 3 + Slinger 1, both members of the ranged line
    assert counts["cavalry"] == 1
    assert counts["recon"] == 2
    assert counts["anticav"] == 0
    # Civilians and great people are not anyone's role - they must not inflate a count.
    assert sum(counts.values()) == 2 + 2 + 1 + 4 + 1 + 2


def test_establishment_finds_the_exact_turn_not_the_next_boundary():
    est = report.establishment(
        frames(
            {
                10: {"WARRIOR": 2, "ARCHER": 2},
                45: {"WARRIOR": 2, "ARCHER": 4, "CATAPULT": 1, "BATTERING_RAM": 1},
                47: FULL,
                60: FULL,
            }
        )
    )
    assert est["turn"] == 47
    assert est["counts"]["siege"] == 2
    assert est["short"] == {}


def test_establishment_reports_the_shortfall_when_it_never_fills():
    est = report.establishment(
        frames(
            {
                10: {"WARRIOR": 1, "ARCHER": 1},
                40: {"WARRIOR": 2, "ARCHER": 4, "CATAPULT": 1, "HORSEMAN": 1},
            }
        )
    )
    assert est["turn"] is None
    assert est["last_turn"] == 40
    assert est["short"]["siege"] == (1, 2)  # one siege short
    assert est["short"]["ram"] == (0, 1)  # and no ram at all
    assert "melee" not in est["short"]  # two warriors fill the melee line


def test_first_role_turn_and_rule_turns_are_per_turn_and_deduplicated():
    by_turn = frames({5: {"SCOUT": 1}, 30: {"CATAPULT": 1, "WARRIOR": 1}})
    assert report.first_role_turn(by_turn, "siege") == 30
    assert report.first_role_turn(by_turn, "recon") == 5
    assert report.first_role_turn(by_turn, "ranged") is None

    rows = [
        {"turn": 7, "result": "CHECK FAILED [carrying-capacity] ... (require: ...)"},
        {"turn": 7, "result": "CHECK FAILED [carrying-capacity] again in the same turn"},
        {"turn": 8, "result": "CHECK FAILED [use-your-attacks]"},
        {"turn": 9, "result": "nothing red"},
    ]
    assert report.rule_turns(rows) == {"carrying-capacity": [7], "use-your-attacks": [8]}


def test_verdict_measures_the_attempt_against_its_own_limits():
    by_turn = frames(
        {1: {"WARRIOR": 1}, 20: {"CATAPULT": 1, "WARRIOR": 2}, 50: FULL, 80: FULL}
    )
    rows = [
        {"turn": 20, "result": "CHECK FAILED [carrying-capacity]"},
        {"turn": 60, "result": 'city_action -> "KEEP|City (pop 4, captured)"'},
        {"turn": 61, "result": "CHECK FAILED [carrying-capacity]"},
    ]
    got = {name.split()[0]: (status, detail) for name, status, detail in report.verdict(by_turn, rows)}
    assert got["P1"][0] == report.HELD  # a siege unit existed well before T45
    assert got["P2"][0] == report.HELD  # establishment complete at T50, inside the T60 limit
    assert got["P3"][0] == report.HELD  # first keep at T60, inside the T80 limit
    assert got["P4"][0] == report.HELD  # one red turn before the city fell, under the limit of ten
    assert "T60" in got["P3"][1]
    assert "T50" in got["P2"][1]


def test_a_prediction_whose_deadline_has_not_arrived_is_open_not_falsified():
    """A one-turn attempt must not read as a failed hypothesis - it is a window that has not closed."""
    by_turn = frames({1: {"WARRIOR": 1}})
    statuses = {name.split()[0]: status for name, status, _d in report.verdict(by_turn, [])}
    assert statuses["P1"] == report.OPEN   # T45 has not arrived
    assert statuses["P2"] == report.OPEN   # T60 has not arrived
    assert statuses["P3"] == report.OPEN   # T80 has not arrived
    assert statuses["P4"] == report.OPEN   # the gold-floor window is still running

    # Past the deadline with the condition unmet, the same prediction is falsified.
    late = frames({1: {"WARRIOR": 1}, 90: {"WARRIOR": 1}})
    statuses = {name.split()[0]: status for name, status, _d in report.verdict(late, [])}
    assert statuses["P1"] == report.FALSIFIED
    assert statuses["P2"] == report.FALSIFIED
    assert statuses["P3"] == report.FALSIFIED


def test_orders_read_the_log_and_the_queue_beats_the_inventory():
    """The doctrine is about asking order, so an ordered siege unit answers P1 before an owned one."""
    rows = [
        {"turn": 12, "tool": "set_city_production",
         "params": {"city_id": 1, "item_type": "BUILDING", "item_name": "BUILDING_MONUMENT"}},
        {"turn": 30, "tool": "set_city_production",
         "params": {"city_id": 1, "item_type": "UNIT", "item_name": "UNIT_ARCHER"}},
        {"turn": 38, "tool": "purchase_item",
         "params": {"city_id": 1, "item_type": "UNIT", "item_name": "UNIT_CATAPULT"}},
        {"turn": 40, "tool": "unit_action", "params": {"action": "move"}},
    ]
    got = report.orders(rows)
    assert (38, "UNIT_CATAPULT", "UNIT") in got
    assert len(got) == 3  # the move is not an order
    assert report.first_order_turn(rows, "siege") == 38
    assert report.first_order_turn(rows, "ranged") == 30
    assert report.first_order_turn(rows, "cavalry") is None
    summary = report.order_summary(rows)
    assert summary["total"] == 3
    assert summary["firsts"]["units"] == (30, "UNIT_ARCHER")
    assert summary["firsts"]["buildings"] == (12, "BUILDING_MONUMENT")

    # Ordered at T38, owned at T70: P1 must answer with the order and say so.
    by_turn = frames({70: FULL})
    p1 = report.verdict(by_turn, rows)[0]
    assert p1[1] == report.HELD
    assert "ordered T38" in p1[2] and p1[0].startswith("P1 a siege unit early (ordered")

    # With no order in the log, the inventory answers and the label admits it.
    p1_owned = report.verdict(by_turn, [])[0]
    assert "owned T70" in p1_owned[2]
    assert p1_owned[1] == report.FALSIFIED  # T70 is past the early threshold, and past T45


def test_orders_are_ordered_by_turn_not_by_log_position():
    """The log interleaves sessions, so a later row can carry an earlier turn."""
    rows = [
        {"turn": 60, "tool": "set_city_production",
         "params": {"item_type": "UNIT", "item_name": "UNIT_LINE_INFANTRY"}},
        {"turn": 25, "tool": "set_city_production",
         "params": {"item_type": "UNIT", "item_name": "UNIT_CATAPULT"}},
    ]
    assert [(t, n) for t, n, _ in report.orders(rows)] == [(25, "UNIT_CATAPULT"), (60, "UNIT_LINE_INFANTRY")]
    assert report.first_order_turn(rows, "siege") == 25
    summary = report.order_summary(rows)
    # Both are units, so the category's first is the earlier turn - not the earlier row.
    assert summary["firsts"]["units"] == (25, "UNIT_CATAPULT")


def test_doctrine_checks_answer_the_mechanical_claims():
    rows = [
        {"turn": 30, "tool": "set_city_production",
         "params": {"city_id": 11, "item_type": "UNIT", "item_name": "UNIT_ARCHER"}},
        {"turn": 34, "tool": "set_city_production",
         "params": {"city_id": 11, "item_type": "UNIT", "item_name": "UNIT_CATAPULT"}},
        {"turn": 36, "tool": "set_city_production",
         "params": {"city_id": 22, "item_type": "UNIT", "item_name": "UNIT_WARRIOR"}},
        {"turn": 40, "tool": "set_city_production",
         "params": {"city_id": 22, "item_type": "UNIT", "item_name": "UNIT_BATTERING_RAM"}},
        {"turn": 44, "tool": "upgrade_unit", "params": {"unit_id": 7}},
        {"turn": 46, "tool": "upgrade_unit", "params": {"unit_id": 9}},
    ]
    # H5: the ram is the violation, and it is named with its turn.
    assert report.forbidden_orders(rows) == [(40, "UNIT_BATTERING_RAM", "UNIT")]
    # H6: two cities were asked for military units, each with its own count.
    spread = report.military_city_spread(rows)
    assert spread["cities"] == 2
    assert spread["per_city"] == {"11": 2, "22": 2}
    # H4: both upgrades, in turn order.
    assert report.upgrades(rows) == [(44, "7"), (46, "9")]
    # H1/H2: what was asked for, and when, earliest first.
    assert report.role_order_sequence(rows) == [
        (30, "ranged", "UNIT_ARCHER"),
        (34, "siege", "UNIT_CATAPULT"),
        (36, "melee", "UNIT_WARRIOR"),
        (40, "ram", "UNIT_BATTERING_RAM"),
    ]


def test_self_report_mismatch_is_visible_and_agreement_is_quiet():
    """The diary's claim about itself is checked against the record, not believed."""
    honest = frames({40: {"CATAPULT": 2, "WARRIOR": 2, "ARCHER": 4, "HORSEMAN": 1, "BATTERING_RAM": 1}})
    honest[40]["reflections"] = {
        "strategic": "T40: cities 4, pop 12. ESTABLISHMENT: siege 2/2 melee 2/2 ram 1/1 "
                     "ranged 4/4 cavalry 1/1 at T40. WAR READY: T40"
    }
    got = report.self_reports(honest)
    assert len(got) == 1 and got[0]["turn"] == 40 and got[0]["mismatch"] == {}

    inflated = frames({40: {"CATAPULT": 1, "WARRIOR": 2, "ARCHER": 2, "HORSEMAN": 0, "BATTERING_RAM": 0}})
    inflated[40]["reflections"] = {
        "strategic": "ESTABLISHMENT: siege 2/2 melee 2/2 ram 1/1 ranged 4/4 cavalry 1/1 at T40"
    }
    got = report.self_reports(inflated)
    assert got[0]["claimed"]["siege"] == 2
    assert got[0]["actual"]["siege"] == 1
    assert got[0]["mismatch"] == {"siege": (2, 1), "ram": (1, 0), "ranged": (4, 2), "cavalry": (1, 0)}

    # A turn with no such line is simply not a report.
    assert report.self_reports(frames({1: {"WARRIOR": 1}})) == []


def test_attempt_rows_compare_two_snapshots_on_the_same_columns():
    """`--compare` reads what `--save` wrote, because the diary will belong to the next attempt."""
    payload = {
        "game": "china_911679432",
        "run": "run-a",
        "first_turn": 1,
        "last_turn": 40,
        "economy": [{"turn": 20, "science": 21.4, "gold_per_turn": 9.0},
                    {"turn": 40, "science": 38.9, "gold_per_turn": 14.2}],
        "establishment": {"turn": 47},
        "captures": [[61, '"KEEP|City"']],
        "rules": {"carrying-capacity": 3},
        "doctrine": {
            "first_military_order": [22, "UNIT_ARCHER"],
            "role_order_sequence": [[22, "ranged", "UNIT_ARCHER"], [35, "siege", "UNIT_CATAPULT"]],
            "forbidden_orders": [[30, "UNIT_BATTERING_RAM", "UNIT"]],
            "self_reports": [{"turn": 40, "mismatch": {"siege": (2, 1)}}],
        },
    }
    row = report.attempt_row("A1", payload)
    assert row["establishment"] == "T47"
    assert row["army_start"] == "T22"
    assert row["siege_order"] == "T35"
    assert row["first_keep"] == "T61"
    assert row["sci_T20"] == 21.4 and row["gpt_T40"] == 14.2
    assert row["h5"] == 1  # the forbidden ram was ordered
    assert row["self_mismatch"] == 1
    assert row["rules_red"] == 1

    empty = report.attempt_row("A2", {"game": "g", "first_turn": 1, "last_turn": 12})
    assert empty["establishment"] == "not reached"
    assert empty["army_start"] == "-" and empty["siege_order"] == "never" and empty["first_keep"] == "none"
    assert empty["h5"] == 0 and empty["self_mismatch"] == 0
    # Every compared column is present on both rows, so the table cannot go ragged.
    for key in report.COMPARE_COLUMNS:
        assert key in row and key in empty


def test_h6_measures_concentration_not_the_city_count():
    """`tactics/08` claims one war city: a count of cities cannot tell that from one stray order."""
    rows = [
        {"turn": 30, "tool": "set_city_production",
         "params": {"city_id": 11, "item_type": "UNIT", "item_name": "UNIT_WARRIOR"}},
        {"turn": 32, "tool": "set_city_production",
         "params": {"city_id": 11, "item_type": "UNIT", "item_name": "UNIT_SLINGER"}},
        {"turn": 34, "tool": "set_city_production",
         "params": {"city_id": 11, "item_type": "UNIT", "item_name": "UNIT_CATAPULT"}},
        {"turn": 36, "tool": "set_city_production",
         "params": {"city_id": 11, "item_type": "BUILDING", "item_name": "BUILDING_GRANARY"}},
        # A single stray order in the second city, and no army order there since.
        {"turn": 38, "tool": "set_city_production",
         "params": {"city_id": 22, "item_type": "UNIT", "item_name": "UNIT_WARRIOR"}},
        {"turn": 40, "tool": "set_city_production",
         "params": {"city_id": 22, "item_type": "BUILDING", "item_name": "BUILDING_MONUMENT"}},
        # A Scout is recon, not the army, and must not count as a war order.
        {"turn": 41, "tool": "set_city_production",
         "params": {"city_id": 22, "item_type": "UNIT", "item_name": "UNIT_SCOUT"}},
    ]
    spread = report.military_city_spread(rows)
    assert spread["cities"] == 2  # the old blunt count, kept for comparability
    assert spread["total_army_orders"] == 4  # the Scout is not one of them
    assert spread["busiest_city"] == "11"
    assert spread["busiest_share"] == 0.75  # 3 of the 4 army orders
    assert spread["war_cities"] == ["11"]  # 3 army orders against 1 building; city 22 is 1 against 3
    assert spread["all_orders_per_city"] == {"11": 4, "22": 3}

def test_contacts_report_first_contact_from_the_diary():
    """A conquest attempt with no contacts has no target, and the diary records contact itself."""
    by_turn = frames({1: {"WARRIOR": 1}, 20: {"WARRIOR": 1}, 40: {"WARRIOR": 1}})
    by_turn[40]["diplo_states"] = {"Rome": {"state": 2}, "Egypt": {"state": 2}}
    by_turn[20]["diplo_states"] = {}
    assert report.contacts(by_turn) == [(40, "Egypt"), (40, "Rome")]

    # A rival already met stays out of the list on later turns, and a new one is added when it appears.
    later = frames({40: {"WARRIOR": 1}, 60: {"WARRIOR": 1}})
    later[40]["diplo_states"] = {"Rome": {"state": 2}}
    later[60]["diplo_states"] = {"Rome": {"state": 2}, "Egypt": {"state": 3}}
    assert report.contacts(later) == [(40, "Rome"), (60, "Egypt")]

    assert report.contacts(frames({1: {"WARRIOR": 1}})) == []


def test_boundaries_survive_a_diary_with_gaps():
    """A turn nobody played must not be asked for - the boundaries are recorded turns, not multiples."""
    by_turn = frames({1: {"WARRIOR": 1}, 9: {"WARRIOR": 1}, 21: {"WARRIOR": 1}, 41: {"WARRIOR": 1}})
    got = report.boundaries(by_turn, 10)
    # T10, T20 and T30 were never played: T21 answers for T10 and T20, T41 for T30 and T40. T9 is not
    # a boundary - it precedes the first multiple of the step and is neither the first nor the last row.
    assert got == [1, 21, 41]
    assert all(turn in by_turn for turn in got)
    # The economy table reads only turns it was given, so it cannot raise.
    table = report.economy_table(by_turn, 10)
    assert [entry["turn"] for entry in table] == got
    assert report.boundaries({}, 10) == []
    # A diary with no gaps is the ordinary case: exactly the multiples, plus the first and last row.
    dense = frames({turn: {"WARRIOR": 1} for turn in range(1, 42)})
    assert report.boundaries(dense, 10) == [1, 10, 20, 30, 40, 41]


def _diary_row(turn: int, stamp: str, **fields) -> dict:
    """An agent diary row: the only two fields the attribution reads, plus whatever it is carrying."""
    return {"turn": turn, "is_agent": True, "timestamp": stamp, **fields}


def test_attribute_diary_recovers_the_earlier_attempt_by_time():
    """A1's T10 read 34 military until A2 overwrote the shared diary with its own T10 row.

    The rows carry no session, so the session's own log window is what separates them - the two
    attempts cannot overlap in time because FireTuner serves one connection at a time.
    """
    candidates = {
        10: [
            _diary_row(10, "2026-09-29T05:24:30+00:00", military=34, tourism=8, era_score=2),
            _diary_row(10, "2026-09-29T06:16:05+00:00", military=31, tourism=0, era_score=4),
        ]
    }
    windows = {10: (report._epoch("2026-09-29T05:24:00+00:00"), report._epoch("2026-09-29T05:24:40+00:00"))}
    by_turn, ambiguous = report.attribute_diary(candidates, windows)
    assert ambiguous == []
    assert by_turn[10]["military"] == 34  # A1's row, not the last write
    assert by_turn[10]["tourism"] == 8

    # The recovery is scoped to the run: plain last-write over the same rows still answers A2's.
    assert candidates[10][-1]["military"] == 31


def test_attribute_diary_names_a_turn_it_cannot_tell_apart():
    """Two rows written inside the same session window are not guessed at - the turn is named."""
    windows = {4: (report._epoch("2026-09-29T06:00:00+00:00"), report._epoch("2026-09-29T06:05:00+00:00"))}
    both_inside = {
        4: [
            _diary_row(4, "2026-09-29T06:01:00+00:00", military=20),
            _diary_row(4, "2026-09-29T06:02:00+00:00", military=21),
        ]
    }
    by_turn, unattributed = report.attribute_diary(both_inside, windows)
    assert by_turn == {} and unattributed == [4]

    # A turn the session's log never covered is not attributed either: no window, no answer.
    by_turn, unattributed = report.attribute_diary({9: [_diary_row(9, "2026-09-29T06:01:00+00:00")]}, windows)
    assert by_turn == {} and unattributed == [9]

    # A single row inside its window is the ordinary case.
    by_turn, unattributed = report.attribute_diary({4: [both_inside[4][0]]}, windows)
    assert unattributed == [] and by_turn[4]["military"] == 20


def test_attribute_diary_rejects_the_nearest_row_when_it_is_another_session_s():
    """A2's first T40 snapshot: A2's own row was not written yet, so the nearest row was A1's.

    The window was A2's T40 (06:45:04-06:45:06, three calls) and the rows in the file were A1's T40 at
    05:54:36 and nothing else, so "nearest" read A1's science 7.9 / military 139 / faith 185 into A2's
    record - where A2's own row, written 22s later, says 5.9 / 156 / 53.8. Distance is not evidence:
    a row minutes from the window belongs to another session, whatever else the file holds.
    """
    windows = {40: (report._epoch("2026-09-29T06:45:04+00:00"), report._epoch("2026-09-29T06:45:06+00:00"))}
    a1_only = {40: [_diary_row(40, "2026-09-29T05:54:36+00:00", science=7.9, military=139, faith=185.2)]}
    by_turn, unattributed = report.attribute_diary(a1_only, windows)
    assert by_turn == {} and unattributed == [40]  # named and left out, not filled with A1's numbers

    # The session's own row, written just after its last call of that turn, is inside the slack.
    a2_row = _diary_row(40, "2026-09-29T06:45:28+00:00", science=5.9, military=156, faith=53.8)
    by_turn, unattributed = report.attribute_diary(
        {40: a1_only[40] + [a2_row]}, windows
    )
    assert unattributed == []
    assert (by_turn[40]["science"], by_turn[40]["military"]) == (5.9, 156)


def test_attribute_diary_falls_back_to_the_session_span():
    """A session resumed after another played the same turns has no per-turn window left to use."""
    span = (report._epoch("2026-09-29T07:00:00+00:00"), report._epoch("2026-09-29T07:30:00+00:00"))
    candidates = {
        20: [
            _diary_row(20, "2026-09-29T05:40:00+00:00", military=99),  # another session's row
            _diary_row(20, "2026-09-29T07:04:00+00:00", military=44),
        ]
    }
    by_turn, ambiguous = report.attribute_diary(candidates, {}, span)
    assert ambiguous == [] and by_turn[20]["military"] == 44
    # Without the span there is nothing to attribute against, so the turn is reported, not invented.
    by_turn, ambiguous = report.attribute_diary(candidates, {}, None)
    assert by_turn == {} and ambiguous == [20]


def test_the_cavalry_role_carries_the_game_s_cavalry_tag():
    """A2 built a Heavy Chariot the role map could not see, so its establishment cavalry slot read 0/1.

    The authority is the game's own `UNITTYPE_CAVALRY` rows in `Units.xml` (its `FormationClass` column
    is too coarse). The same table tags those units `MELEE` as well, so melee cannot be "everything
    tagged melee" - it stays the curated upgrade chain, and a cavalry unit must count **once**.
    """
    counts = report.role_counts({"HEAVY_CHARIOT": 1, "WARRIOR": 2})
    assert counts.get("cavalry") == 1
    assert counts.get("melee") == 2  # the Chariot is not also a melee unit
    assert sum(counts.values()) == 3  # every unit lands in exactly one role
    # The generic cavalry line the game tags CAVALRY, as of this checkout's role map.
    for unit in ("HORSEMAN", "COURSER", "KNIGHT", "CUIRASSIER", "CAVALRY", "TANK", "MODERN_ARMOR"):
        assert report.role_counts({unit: 1}).get("cavalry") == 1, unit
    # The anti-cavalry line upgrades into two more names than it had.
    for unit in ("SPEARMAN", "PIKEMAN", "PIKE_AND_SHOT", "AT_CREW", "MODERN_AT"):
        assert report.role_counts({unit: 1}).get("anticav") == 1, unit


def test_verdict_prints_the_attempt_s_own_prediction_ids():
    """A1 called its predictions P1-P4 and A2 called its own Q1-Q4.

    Printing the first attempt's ids over the second attempt's record puts two names on one
    prediction, and the A2 review is written against Q1-Q4 - so the labels are passed in, and a caller
    that passes the wrong number of them is told instead of getting a short list.
    """
    by_turn = frames({1: {"WARRIOR": 1}, 40: {"WARRIOR": 1}})
    default = report.verdict(by_turn, [])
    assert [name.split()[0] for name, _s, _d in default] == ["P1", "P2", "P3", "P4"]
    mine = report.verdict(by_turn, [], ids=("Q1", "Q2", "Q3", "Q4"))
    assert [name.split()[0] for name, _s, _d in mine] == ["Q1", "Q2", "Q3", "Q4"]
    # The same four predictions, measured the same way: only the label moved.
    assert [d for _n, _s, d in default] == [d for _n, _s, d in mine]
    with pytest.raises(ValueError):
        report.verdict(by_turn, [], ids=("Q1", "Q2"))


def test_attribute_diary_multi_recovers_both_halves_of_a_resumed_attempt():
    """An attempt can span a resume: A2's first half is one session, its second half another.

    Each session keeps its own windows, so widening the search to two sessions does not widen any
    single window - a turn no named session covers is still named rather than guessed.
    """
    first_window = (
        report._epoch("2026-09-29T05:20:00+00:00"),
        report._epoch("2026-09-29T05:25:00+00:00"),
    )
    second_window = (
        report._epoch("2026-09-29T07:00:00+00:00"),
        report._epoch("2026-09-29T07:05:00+00:00"),
    )
    sessions = [({10: first_window}, first_window), ({41: second_window}, second_window)]
    candidates = {
        10: [_diary_row(10, "2026-09-29T05:24:30+00:00", science=5.9)],
        41: [_diary_row(41, "2026-09-29T07:01:00+00:00", science=5.4)],
        60: [_diary_row(60, "2026-09-29T09:00:00+00:00", science=9.9)],  # no named session covers T60
    }
    by_turn, unattributed = report.attribute_diary_multi(candidates, sessions)
    assert sorted(by_turn) == [10, 41]
    assert unattributed == [60]
    assert (by_turn[10]["science"], by_turn[41]["science"]) == (5.9, 5.4)


def test_diary_rows_for_run_takes_a_comma_separated_list(tmp_path, monkeypatch):
    """The CLI passes what the record needs: `--run first,second` for an attempt that was resumed.

    Read end to end here - the diary rows and the two runs' logs on disk - because the failure this
    guards against is silent: with one run named, the other half's turns are dropped and the report
    simply starts at the resume.
    """
    data = tmp_path
    rows = [
        _diary_row(10, "2026-09-29T05:24:30+00:00", science=5.9),
        _diary_row(41, "2026-09-29T07:01:00+00:00", science=5.4),
    ]
    (data / "diary_china_test.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    logs = {
        # A session's log row for a turn and the diary row it writes land within seconds of each
        # other (measured: 22s at A2's T40), which is the window the attribution exists for.
        "first-half": (10, report._epoch("2026-09-29T05:23:40+00:00")),
        "second-half": (41, report._epoch("2026-09-29T07:00:30+00:00")),
    }
    for name, (turn, ts) in logs.items():
        (data / f"log_china_test_{name}.jsonl").write_text(
            json.dumps({"turn": turn, "ts": ts, "session": name, "tool": "end_turn"}) + "\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(report, "DATA", data)

    by_turn, unattributed = report.diary_rows_for_run("china_test", "first-half,second-half")
    assert unattributed == []
    assert sorted(by_turn) == [10, 41]
    # One run alone still answers for its own half only - which is why the list exists.
    only_second, _ = report.diary_rows_for_run("china_test", "second-half")
    assert sorted(only_second) == [41]
    # And the log family is filtered the same way, so both halves' calls are one attempt's.
    assert len(report.log_rows("china_test", "first-half,second-half")) == 2
    assert [row["turn"] for row in report.log_rows("china_test", "second-half")] == [41]


def test_compare_header_names_income_not_the_treasury(tmp_path, capsys):
    """A1's T40 read `gold_T40 6.0` beside a treasury of 236 - the column was gold **per turn**.

    The columns that hold a yield are named for it (`gpt_T40`), so a reader cannot quote the income
    as the balance, and the legend says which is which.
    """
    snapshot = {
        "game": "china_test",
        "first_turn": 1,
        "last_turn": 40,
        "economy": [{"turn": 40, "science": 7.9, "gold": 236.0, "gold_per_turn": 6.0}],
    }
    first = tmp_path / "A1-T40.json"
    second = tmp_path / "A2-T40.json"
    for path, science in ((first, 7.9), (second, 12.0)):
        snapshot["economy"] = [{"turn": 40, "science": science, "gold": 236.0, "gold_per_turn": 6.0}]
        path.write_text(json.dumps(snapshot), encoding="utf-8")

    assert report.print_compare([first, second]) == 0
    out = capsys.readouterr().out
    header = out.splitlines()[0]
    assert "gpt_T40" in header
    assert "gold_T40" not in out  # the ambiguous name is gone, not merely documented
    # The two rows carry their own values, so the table is a compare and not one row twice.
    rows = [line for line in out.splitlines()[1:] if line.startswith(("A1-T40", "A2-T40"))]
    assert len(rows) == 2 and rows[0] != rows[1]
    assert "per turn" in out  # the legend disambiguates the yield columns from the treasury
