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
import pathlib

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
    assert row["sci_T20"] == 21.4 and row["gold_T40"] == 14.2
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
