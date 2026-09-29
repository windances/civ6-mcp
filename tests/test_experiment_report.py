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
    got = {name.split()[0]: (held, detail) for name, held, detail in report.verdict(by_turn, rows)}
    assert got["P1"][0] is True  # a siege unit existed well before T45
    assert got["P2"][0] is True  # establishment complete at T50, inside the T60 limit
    assert got["P3"][0] is True  # first keep at T60, inside the T80 limit
    assert got["P4"][0] is True  # one red turn before the city fell, under the limit of ten
    assert "T60" in got["P3"][1]
    assert "T50" in got["P2"][1]


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
    assert p1[1] is True
    assert "ordered T38" in p1[2] and p1[0].startswith("P1 a siege unit early (ordered")

    # With no order in the log, the inventory answers and the label admits it.
    p1_owned = report.verdict(by_turn, [])[0]
    assert "owned T70" in p1_owned[2]
    assert p1_owned[1] is False  # T70 is past the early threshold


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
