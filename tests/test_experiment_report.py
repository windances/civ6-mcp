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

# The required table as corrected after the A2 experiment (2026-09-29): the ram left it (the doctrine
# forbids buying one) and recon and anti-cavalry entered it (Gate 0 needs a city seen, and a Heavy
# Chariot parked next to the train needs an answer).
FULL = {"CATAPULT": 2, "WARRIOR": 2, "SPEARMAN": 1, "ARCHER": 4, "HORSEMAN": 1, "SCOUT": 1}


def frames(by_turn: dict[int, dict], techs_from: int | None = None) -> dict[int, dict]:
    """A diary frame per turn: the shape `diary_rows()` hands the tool.

    `techs_from` marks `TECH_ENGINEERING` complete from that turn on, which is what
    `engineering_gate` reads. A5's Q3 is measured **after** the gate, so its fixtures need one: a
    fixture without it makes the gate unaskable and every Q3 answer meaningless.
    """
    out: dict[int, dict] = {}
    for turn, comp in by_turn.items():
        row = {"turn": turn, "is_agent": True, "unit_composition": comp}
        if techs_from is not None and turn >= techs_from:
            row["techs"] = ["TECH_THE_WHEEL", "TECH_ENGINEERING"]
        out[turn] = row
    return out


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
                45: {
                    "WARRIOR": 2,
                    "ARCHER": 4,
                    "CATAPULT": 1,
                    "SPEARMAN": 1,
                    "HORSEMAN": 1,
                },  # one Catapult and no scout: still short two slots
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
    assert est["short"]["recon"] == (0, 1)  # no scout, and Gate 0 needs one
    assert est["short"]["anticav"] == (0, 1)  # nothing to answer a Heavy Chariot with
    assert "ram" not in est["short"]  # the ram left the table: the doctrine forbids buying one
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
    # H6: two cities were asked for military units, each with its own count - and the ram is not one of
    # them under the corrected table (H5 counts it separately, as a forbidden order).
    spread = report.military_city_spread(rows)
    assert spread["cities"] == 2
    assert spread["per_city"] == {"11": 2, "22": 1}
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


def test_the_self_report_reader_takes_the_corrected_tables_shape_too():
    """The correction made the ram conditional and added `anticav`/`recon`; the reader has to follow.

    Measured cause: the old regex required the `ram` token, so a line written to the corrected table
    parsed as **nothing at all** - the one cross-check that caught all eleven of A2's mismatches was
    blind to exactly the two rows the correction introduced, and the briefs worked around it by pinning
    the pre-correction shape and reporting the new rows as unscored.
    """
    full = frames({50: {"CATAPULT": 2, "WARRIOR": 2, "ARCHER": 4, "HORSEMAN": 1, "SPEARMAN": 1, "SCOUT": 1}})
    full[50]["reflections"] = {
        "strategic": "ESTABLISHMENT: siege 2/2 melee 2/2 ranged 4/4 cavalry 1/1 "
                     "(anticav 1/1, recon 1/1) at T50"
    }
    got = report.self_reports(full)
    assert len(got) == 1
    assert got[0]["claimed"] == {
        "siege": 2, "melee": 2, "ranged": 4, "cavalry": 1, "anticav": 1, "recon": 1
    }
    assert got[0]["mismatch"] == {}

    # The hyphenated spelling is the same role, the ram slot may simply be absent, and a wrong count in
    # either new row is a mismatch like any other.
    hyphenated = frames({50: {"CATAPULT": 2, "WARRIOR": 2, "ARCHER": 4, "HORSEMAN": 1, "SPEARMAN": 0, "SCOUT": 0}})
    hyphenated[50]["reflections"] = {
        "strategic": "ESTABLISHMENT: siege 2/2 melee 2/2 ranged 4/4 cavalry 1/1, "
                     "anti-cavalry 1/1, recon 1/1 at T50"
    }
    got = report.self_reports(hyphenated)
    assert got[0]["claimed"]["anticav"] == 1 and "ram" not in got[0]["claimed"]
    assert got[0]["mismatch"] == {"anticav": (1, 0), "recon": (1, 0)}

    # A line that names no role at all is still not a report.
    empty = frames({50: {"WARRIOR": 1}})
    empty[50]["reflections"] = {"strategic": "ESTABLISHMENT: nothing to report at T50"}
    assert report.self_reports(empty) == []


def test_the_self_report_reader_reads_through_emphasis_and_takes_the_first_claim():
    """Two measured traps in the same line, both found by running it against A2's real diary.

    (1) The sessions **bold the slots they have filled** (`melee **2/2**`), which is why the old
    strict regex missed whole lines - and a token scan that does not tolerate the emphasis reads only
    the unbolded roles and silently drops the rest. (2) The sentence after the report quotes the
    *target* table (`the plan is siege 2/2`), so a reader that keeps the last occurrence turns A2's
    T11 report of `siege 0/2` into a claim of 2. First occurrence wins, and the scan stops at the next
    field (`WAR READY:` / `ENEMY SEEN:`).
    """
    bolded = frames({7: {"WARRIOR": 2, "CATAPULT": 0, "SLINGER": 0, "HORSEMAN": 0, "BATTERING_RAM": 0}})
    bolded[7]["reflections"] = {
        "strategic": "ESTABLISHMENT: siege 0/2 melee **2/2** ram 0/1 ranged 0/4 cavalry 0/1 at T7. "
                     "WAR READY: not yet."
    }
    got = report.self_reports(bolded)
    assert got[0]["claimed"] == {"siege": 0, "melee": 2, "ram": 0, "ranged": 0, "cavalry": 0}
    assert got[0]["mismatch"] == {}

    trailing = frames({7: {"CATAPULT": 0, "WARRIOR": 2, "SLINGER": 0, "HORSEMAN": 0, "BATTERING_RAM": 0}})
    trailing[7]["reflections"] = {
        "strategic": "ESTABLISHMENT: siege 0/2 melee 2/2 ram 0/1 ranged 0/4 cavalry 0/1 at T7 - the "
                     "plan is siege 2/2 and ranged 4/4. WAR READY: not yet."
    }
    got = report.self_reports(trailing)
    assert got[0]["claimed"]["siege"] == 0 and got[0]["claimed"]["ranged"] == 0
    assert got[0]["mismatch"] == {}


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


def test_the_gold_floor_detail_reports_both_measures():
    """A2's Q4 named the rule `carrying-capacity`, which is gated at turn 60.

    Its horizon was T60, so the rule could only ever report zero red turns - and zero is not evidence
    the army was paid for. `end_turn`'s own 10-turn review printed `carrying capacity: gold/turn +5.0
    ... BELOW the +10` at T19, and +7.0/+6.0 at T29/T39, over the same turns. The diary's own number is
    therefore printed beside the rule's, so a vacuous zero cannot read as a healthy economy.
    """
    by_turn = frames({1: {"WARRIOR": 1}, 40: {"WARRIOR": 1}})
    by_turn[1]["gold_per_turn"] = 5.0
    by_turn[40]["gold_per_turn"] = 9.0
    _name, status, detail = report.verdict(by_turn, [])[3]
    assert status == report.OPEN  # the deadline has not arrived, so nothing is claimed either way
    assert "0 red turn(s) by the rule" in detail
    assert "below 10 on 2 of those 2 turn(s)" in detail
    # A turn that is fine by the diary's number is not counted against the attempt.
    by_turn[40]["gold_per_turn"] = 12.0
    _n, _s, detail = report.verdict(by_turn, [])[3]
    assert "below 10 on 1 of those 2 turn(s)" in detail


def _order_row(turn: int, name: str, kind: str = "UNIT") -> dict:
    """A logged production order: the shape `orders()` reads."""
    return {"turn": turn, "tool": "set_city_production", "params": {"item_name": name, "item_type": kind}}


def _diary_with_tech(turn: int, techs: list[str]) -> dict:
    row = _diary_row(turn, "2026-09-29T07:00:00+00:00")
    row["techs"] = techs
    return row


def test_the_engineering_gate_reads_the_order_of_asking():
    """A2's Q2 has no generic slot: it is about what was asked for *after* Engineering landed.

    The generic P1 asks about a calendar deadline and reads this attempt's T48 order as late; the
    question the attempt actually asked is whether the siege train came before the economy once the
    tech existed. The gate is HELD, FALSIFIED or OPEN - never a deadline.
    """
    before = {1: _diary_with_tech(1, ["TECH_MINING"])}
    landed = {1: _diary_with_tech(1, ["TECH_MINING"]), 48: _diary_with_tech(48, ["TECH_MINING", "TECH_ENGINEERING"])}

    # Engineering has not landed: the order is unaskable, not missed.
    gate = report.engineering_gate(before, [])
    assert gate["status"] == report.OPEN and "unaskable" in gate["detail"]

    # The attempt's own case: both Catapults ordered the same turn the tech landed, no economy order.
    siege_only = [_order_row(43, "UNIT_BUILDER"), _order_row(46, "UNIT_TRADER"), _order_row(48, "UNIT_CATAPULT")]
    gate = report.engineering_gate(landed, siege_only)
    assert gate["status"] == report.HELD
    assert "Engineering T48" in gate["detail"] and "first siege order T48" in gate["detail"]
    assert "no economy order since" in gate["detail"]

    # An economy order after the gate is fine as long as it comes after the siege order.
    siege_first = [*siege_only, _order_row(52, "BUILDING_GRANARY", "BUILDING")]
    assert report.engineering_gate(landed, siege_first)["status"] == report.HELD

    # A building before the siege train breaks the claim, and the detail names both turns.
    economy_first = [_order_row(49, "BUILDING_GRANARY", "BUILDING"), _order_row(52, "UNIT_CATAPULT")]
    gate = report.engineering_gate(landed, economy_first)
    assert gate["status"] == report.FALSIFIED
    assert "economy order T49" in gate["detail"] and "T52" in gate["detail"]

    # Orders placed before the gate do not decide it.
    pre_gate = [_order_row(20, "BUILDING_MONUMENT", "BUILDING"), _order_row(22, "UNIT_CATAPULT")]
    gate = report.engineering_gate(landed, pre_gate)
    assert gate["status"] == report.OPEN and "neither" in gate["detail"]


def test_the_a2_question_set_asks_a2_s_own_four():
    """A2's Q1 is the generic slot 2 and its Q2 has no slot, so position alone would mislabel them."""
    by_turn = {
        1: _diary_with_tech(1, ["TECH_MINING"]),
        48: _diary_with_tech(48, ["TECH_MINING", "TECH_ENGINEERING"]),
    }
    by_turn[1]["unit_composition"] = {"WARRIOR": 1}
    by_turn[48]["unit_composition"] = {"WARRIOR": 4, "SLINGER": 4, "HEAVY_CHARIOT": 1}
    by_turn[1]["gold_per_turn"] = 5.0
    by_turn[48]["gold_per_turn"] = 7.0
    rows = [_order_row(48, "UNIT_CATAPULT")]
    questions = report.verdict_a2(by_turn, rows)
    assert [name.split()[0] for name, _s, _d in questions] == ["Q1", "Q2", "Q3", "Q4"]
    assert questions[0][0].startswith("Q1 establishment complete by T60")
    assert questions[1][1] == report.HELD
    assert questions[2][0].startswith("Q3 first enemy city kept by T80")
    # And the generic set is untouched: its slot 1 is A1's calendar question, not A2's Q1.
    generic = report.verdict(by_turn, rows)
    assert generic[0][0].startswith("P1 a siege unit early")


def _attack_row(turn: int, walls: str, city_hp: str = "200/200") -> dict:
    """An attack reply on a city: the line the wall pool is read from."""
    return {
        "turn": turn,
        "tool": "unit_action",
        "params": {"action": "attack"},
        "result": f"CITY_ATTACK|city hp: {city_hp}, walls: {walls}",
    }


def _keep_row(turn: int) -> dict:
    return {"turn": turn, "tool": "resolve_city_capture", "params": {"action": "keep"},
            "result": "KEEP|Yerushalayim (pop 5, id:196610, captured)"}


def test_a_capture_the_game_resolved_itself_is_still_a_capture():
    """Measured on A4 at T65: the game kept the city, so `KEEP|` never appeared.

    The melee unit's move answered `CAPTURE_MOVE|50,22|...|CITY TAKEN`, and every
    `resolve_city_capture` after it answered `NO_PENDING_CITY` because nothing was pending. A reader
    that only looked for `KEEP|` scored the attempt as having kept nothing while `get_cities` showed
    three cities. Both shapes are evidence now.
    """
    taken = {
        "turn": 65,
        "tool": "unit_action",
        "params": {"unit_id": 720903, "action": "move", "target_x": 50, "target_y": 22},
        "result": "CAPTURE_MOVE|50,22|from:49,23|now_at:50,22|(moved dx:+1 dy:-1)|"
                  "CITY TAKEN - resolve keep/raze with city_action",
    }
    got = report.captures([taken])
    assert [turn for turn, _ in got] == [65]
    assert "CITY TAKEN" in got[0][1]

    # The explicit reply still counts, and a capture-move whose city was NOT taken does not.
    assert [t for t, _ in report.captures([_keep_row(67)])] == [67]
    assert report.captures(
        [
            {
                "turn": 65,
                "tool": "unit_action",
                "result": "CAPTURE_MOVE|50,22|from:49,23|now_at:49,23|BLOCKED (occupied)",
            }
        ]
    ) == []


def test_verdict_a7_holds_on_a_capture_the_game_resolved_itself():
    """Q3 asks whether a city was kept, not which reply spelled it - A4's shape must read HELD."""
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 65: FULL}))
    taken = {
        "turn": 65,
        "tool": "unit_action",
        "params": {"unit_id": 720903, "action": "move", "target_x": 50, "target_y": 22},
        "result": "CAPTURE_MOVE|50,22|from:49,23|now_at:50,22|CITY TAKEN - resolve keep/raze with "
                  "city_action",
    }
    questions = report.verdict_a7(by_turn, [taken])
    assert questions[2][1] == report.HELD
    assert "T65" in questions[2][2]


def _a3_frames(turns: list[int]) -> dict[int, dict]:
    by_turn = frames({t: {"WARRIOR": 1} for t in turns})
    for turn in turns:
        by_turn[turn]["gold_per_turn"] = 7.0
    return by_turn


def test_the_a3_question_set_measures_the_wall_phase():
    """A3's Q2 is the one question no attempt has had: was there a wall, and how long did it take?

    The pool is read off the attack replies (`walls: N/M`, and `walls: none` when there is none), so the
    instrument can answer it rather than describing it. A2 could not: every shot of its assault read
    `walls: none`.
    """
    # A walled city, breached, kept inside the window: the claim holds.
    by_turn = _a3_frames([1, 60, 68, 70, 74])
    rows = [
        _attack_row(68, "100/100"),
        _attack_row(70, "0/100"),
        _keep_row(74),
    ]
    wall = report.wall_phase(by_turn, rows)
    assert wall["status"] == report.HELD
    assert wall["first_wall_turn"] == 68 and wall["walls_down_turn"] == 70 and wall["keep_turn"] == 74
    assert "walls first read T68" in wall["detail"] and "breached T70" in wall["detail"]

    # No wall pool above zero anywhere: unaskable, and the detail says so rather than calling it a miss.
    wall = report.wall_phase(by_turn, [])
    assert wall["status"] == report.OPEN
    assert "unaskable" in wall["detail"]

    # Unwalled reads do not count as walls - `walls: none` is what A2 saw on every shot.
    no_walls = [_attack_row(66, "none"), _attack_row(68, "none")]
    assert report.wall_phase(by_turn, no_walls)["status"] == report.OPEN

    # Breached but not yet kept: open, with the breach on the record.
    wall = report.wall_phase(by_turn, [_attack_row(68, "100/100"), _attack_row(70, "0/100")])
    assert wall["status"] == report.OPEN and wall["walls_down_turn"] == 70

    # Kept too early: walls did not slow anything down.
    early = [_attack_row(60, "100/100"), _keep_row(62)]
    wall = report.wall_phase(_a3_frames([1, 60, 62]), early)
    assert wall["status"] == report.FALSIFIED and "earlier than T68" in wall["detail"]

    # Kept too late: outside the window's other end.
    late = [_attack_row(60, "100/100"), _attack_row(62, "0/100"), _keep_row(81)]
    wall = report.wall_phase(_a3_frames([1, 60, 62, 81]), late)
    assert wall["status"] == report.FALSIFIED and "later than T80" in wall["detail"]


def test_an_unaskable_wall_phase_is_terminal_once_the_attempt_is_over():
    """A finished attempt whose Q2 still read OPEN would look undecided; its answer is "unaskable".

    A3's own falsifier says "no city with `walls > 0` is found and attacked inside the window (unaskable -
    report the reads)", so once the window has closed that is the result. Measured reason for the change:
    A3 attacked an unwalled city-state from T61 and kept it, and every read - the target's and both rivals'
    capitals - said `walls: none`; a snapshot of that attempt whose Q2 still read `OPEN` would have said the
    question was undecided where the attempt had in fact answered it.
    """
    by_turn = _a3_frames([1, 60, 62])
    no_walls = [_attack_row(62, "none")]
    # Mid-window, with nothing walled attacked yet: still open, because a walled city could still appear.
    assert report.wall_phase(by_turn, no_walls)["status"] == report.OPEN

    # **A keep is not what closes it.** A3 kept an *unwalled* city at T67 and its brief kept the attempt
    # running to T110 in search of a walled one, so "a city was kept" would have shut the question while
    # the attempt was still hunting for the target the question is about.
    kept_early = _a3_frames([1, 60, 62, 70])
    assert report.wall_phase(kept_early, [*no_walls, _keep_row(70)])["status"] == report.OPEN

    # The question's own late bound is what closes it.
    wall = report.wall_phase(_a3_frames([1, 60, 62, 81]), no_walls)
    assert wall["status"] == report.UNASKABLE
    assert "unaskable on this map" in wall["detail"] and "T80 bound has passed" in wall["detail"]


def test_the_a3_question_set_asks_a3_s_own_four():
    by_turn = _a3_frames([1, 48, 60, 74])
    by_turn[48]["techs"] = ["TECH_MINING", "TECH_ENGINEERING"]
    by_turn[1]["unit_composition"] = {"WARRIOR": 1}
    by_turn[48]["unit_composition"] = {"WARRIOR": 2, "ARCHER": 4, "CATAPULT": 2, "SPEARMAN": 1, "SCOUT": 1}
    rows = [_attack_row(68, "100/100"), _attack_row(70, "0/100"), _keep_row(74)]
    questions = report.verdict_a3(by_turn, rows)
    assert [name.split()[0] for name, _s, _d in questions] == ["Q1", "Q2", "Q3", "Q4"]
    assert "corrected table" in questions[0][0]
    assert questions[1][1] == report.HELD
    assert questions[1][0].startswith("Q2 a walled target")
    assert questions[3][1] == report.HELD  # 7.0 gold/turn is under the floor: the rule counts, not the diary


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


# --------------------------------------------------------------------------- A5/A6/A7
#
# The three new question sets are compared against A2's measured numbers, so their fixtures carry what
# A2's record carries: a siege train, a first non-unit order, a war declaration and a red gold floor.
# A synthetic log row is the shape `log_rows()` hands the tool - turn, ts, tool, params, result.


def _city_order_row(turn: int, city_id: int, name: str, kind: str = "UNIT") -> dict:
    """A logged order with the city it was placed in - A7's measure is per city."""
    return {"turn": turn, "tool": "set_city_production",
            "params": {"city_id": city_id, "item_type": kind, "item_name": name}}


def _purchase_row(turn: int, name: str, city_id: int = 11) -> dict:
    """A logged purchase - the row A6's variable is read from."""
    return {"turn": turn, "tool": "purchase_item",
            "params": {"city_id": city_id, "item_type": "UNIT", "item_name": name,
                       "yield_type": "YIELD_GOLD"}}


def _war_row(turn: int) -> dict:
    """The game's own acknowledgement of a declaration (`src/civ_mcp/lua/diplomacy.py`)."""
    return {"turn": turn, "tool": "send_diplomatic_action",
            "params": {"other_player_id": 6, "action": "DECLARE_SURPRISE_WAR"},
            "result": "OK:WAR_REQUESTED|DECLARE_SURPRISE_WAR on the city-state"}


def _red_row(turn: int) -> dict:
    """A turn the gold floor's rule read red."""
    return {"turn": turn, "tool": "end_turn", "params": {},
            "result": "CHECK FAILED [carrying-capacity] gold/turn +6.0 with military 156"}


def _floored(by_turn: dict[int, dict], gold_per_turn: float = 12.0) -> dict[int, dict]:
    """The frames with an income on every turn, so the floor's second measure is a real number."""
    for row in by_turn.values():
        row["gold_per_turn"] = gold_per_turn
    return by_turn


def test_pin_check_holds_deviates_and_stays_undecided():
    """A3's run is why this exists: the pin was in force and the fourth order was a Warrior at T15.

    The promise is about the executor, and until this check nothing mechanical read it - so the three
    states are pinned separately, because "fewer than four orders placed" is an undecided pin and not a
    held one.
    """
    opening = [
        _city_order_row(1, 11, "UNIT_SCOUT"),
        _city_order_row(5, 11, "UNIT_SLINGER"),
        _city_order_row(6, 11, "UNIT_SETTLER"),
        _city_order_row(15, 11, "UNIT_BUILDER"),
    ]
    pin = report.pin_check(opening)
    assert pin["matched"] is True and pin["first_deviation"] is None
    assert pin["orders"] == [
        (1, "UNIT_SCOUT", "11"),
        (5, "UNIT_SLINGER", "11"),
        (6, "UNIT_SETTLER", "11"),
        (15, "UNIT_BUILDER", "11"),
    ]
    assert "held" in pin["note"]

    # A3's own shape: three positions as promised and a Warrior where the Builder was promised.
    deviated = [*opening[:3], _city_order_row(15, 11, "UNIT_WARRIOR")]
    pin = report.pin_check(deviated)
    assert pin["matched"] is False
    assert pin["first_deviation"] == (15, "UNIT_WARRIOR")
    assert "opening order 4" in pin["note"] and "UNIT_WARRIOR" in pin["note"] and "T15" in pin["note"]

    # Three orders placed is not a pin that held: the fourth position does not exist yet.
    pin = report.pin_check(opening[:3])
    assert pin["matched"] is False and pin["first_deviation"] is None
    assert "only 3 of 4" in pin["note"] and "undecided" in pin["note"]

    # A building in position 1 is a deviation like any other.
    pin = report.pin_check([_city_order_row(2, 11, "BUILDING_MONUMENT", "BUILDING"), *opening[1:]])
    assert pin["matched"] is False and pin["first_deviation"] == (2, "BUILDING_MONUMENT")

    # The name is compared through the same normalisation the role map uses.
    assert report.pin_check([_city_order_row(1, 11, "SCOUT"), *opening[1:]])["matched"] is True
    assert report.pin_check([])["placed"] == 0


def test_siege_purchases_ignores_a_produced_siege_order():
    """A6's variable is that the train is *bought*, so a queue order of the same unit is not one."""
    rows = [
        _city_order_row(40, 11, "UNIT_CATAPULT"),  # produced: the thing the variable replaces
        _purchase_row(45, "UNIT_CATAPULT"),
        _purchase_row(44, "UNIT_ARCHER"),  # bought, but not siege
        _purchase_row(48, "UNIT_TREBUCHET", city_id=22),
    ]
    assert report.siege_purchases(rows) == [(45, "UNIT_CATAPULT"), (48, "UNIT_TREBUCHET")]
    assert report.siege_purchases([_city_order_row(40, 11, "UNIT_CATAPULT")]) == []
    # The produced order is still an order - the two measures answer different questions.
    assert report.first_order_turn(rows, "siege") == 40


def test_war_declared_reads_the_games_own_reply():
    """A2's three declarations answered WARN:WAR_UNCERTAIN and changed nothing, so this reads the reply."""
    uncertain = {"turn": 60, "tool": "send_diplomatic_action",
                 "params": {"other_player_id": 6, "action": "DECLARE_SURPRISE_WAR"},
                 "result": "WARN:WAR_UNCERTAIN|session completed but war state not yet confirmed"}
    refused = {"turn": 61, "tool": "unit_action", "params": {"action": "attack"},
               "result": "ERR:NOT_AT_WAR"}
    # Nothing declares: a warning and a refusal are not a war, and no row at all has no answer.
    assert report.war_declared([uncertain, refused]) is None
    assert report.war_declared([]) is None
    # The earliest declaration is the turn the war opened, whatever order the log holds them in.
    declared = _war_row(55)
    assert report.war_declared([declared, uncertain, refused]) == 55
    later = {**_war_row(58)}
    assert report.war_declared([later, declared]) == 55


def test_army_producing_cities_counts_army_orders_per_city_before_a_turn():
    """A7's measure: per city, how many army-role units it was asked for - before the keep."""
    rows = [
        _city_order_row(30, 11, "UNIT_WARRIOR"),
        _city_order_row(32, 11, "UNIT_ARCHER"),
        _city_order_row(40, 22, "UNIT_WARRIOR"),
        _city_order_row(50, 22, "UNIT_CATAPULT"),
        _city_order_row(55, 11, "UNIT_SCOUT"),  # recon is not the army
        _city_order_row(56, 11, "BUILDING_MONUMENT", "BUILDING"),  # not a unit
    ]
    assert report.army_producing_cities(rows) == {"11": 2, "22": 2}
    # Strictly before: an order on the keep turn itself is after the war that matters.
    assert report.army_producing_cities(rows, before_turn=40) == {"11": 2}
    assert report.army_producing_cities(rows, before_turn=41) == {"11": 2, "22": 1}
    assert report.army_producing_cities(rows, before_turn=30) == {}


def test_the_a5_question_set_asks_a5_s_own_four():
    """A5's variable is Q2: the establishment has to arrive 5+ turns ahead of A2's siege train at T55."""
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 60: FULL}, techs_from=47))
    rows = [_order_row(40, "UNIT_CATAPULT"), _order_row(55, "BUILDING_GRANARY", "BUILDING")]
    questions = report.verdict_a5(by_turn, rows)
    assert [name.split()[0] for name, _s, _d in questions] == ["Q1", "Q2", "Q3", "Q4"]
    assert questions[0][1] == report.HELD  # the corrected table at T47, inside T60
    assert questions[1][1] == report.HELD
    assert "T47" in questions[1][2] and "T55" in questions[1][2]
    assert questions[2][1] == report.HELD
    assert "T55" in questions[2][2] and "BUILDING_GRANARY" in questions[2][2]
    assert "after the T47 gate" in questions[2][2]
    assert questions[3][1] == report.HELD  # nothing red and the window has closed


def test_a5_q3_reads_the_economy_after_the_gate_not_before_it():
    """The measure's own failure, pinned: A2's first non-unit order was a pre-gate T28 Granary.

    Read as "the first non-unit order", Q3 scored that T28 order as the economy's answer - twenty turns
    before the train's tech existed - where the number A5 compares against (A2's T55) is its first
    economy order *after* the gate. A pre-gate Granary must not satisfy the question, and a post-gate
    order must.
    """
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 60: FULL}, techs_from=47))
    pre_gate = [_order_row(28, "BUILDING_GRANARY", "BUILDING"), _order_row(40, "UNIT_CATAPULT")]
    questions = report.verdict_a5(by_turn, pre_gate)
    assert questions[2][1] == report.FALSIFIED
    assert "T28" not in questions[2][2]
    assert "no building or district ordered since the T47 gate" in questions[2][2]

    after_gate = [*pre_gate, _order_row(50, "BUILDING_WATER_MILL", "BUILDING")]
    questions = report.verdict_a5(by_turn, after_gate)
    assert questions[2][1] == report.HELD
    assert "T50" in questions[2][2] and "BUILDING_WATER_MILL" in questions[2][2]


def test_the_a5_question_set_falsifies_and_stays_open():
    """A window that has not closed is OPEN, and each question names what makes it false."""
    early = _floored(frames({1: {"WARRIOR": 1}, 40: {"WARRIOR": 1}}))
    assert [status for _n, status, _d in report.verdict_a5(early, [])] == [report.OPEN] * 4

    # Past T60 with no establishment, no gate and no economy: Q1, Q2 and Q3 all decide.
    late = _floored(frames({1: {"WARRIOR": 1}, 60: {"WARRIOR": 1}}))
    questions = report.verdict_a5(late, [])
    assert questions[0][1] == report.FALSIFIED
    assert questions[1][1] == report.FALSIFIED and "no turn to compare" in questions[1][2]
    assert questions[2][1] == report.FALSIFIED and "no gate to measure against" in questions[2][2]

    # The table completes, but at T52 it is not 5 turns earlier than A2's T55: the variable missed.
    late_table = _floored(frames({1: {"WARRIOR": 1}, 52: FULL}))
    questions = report.verdict_a5(late_table, [])
    assert questions[1][1] == report.FALSIFIED and "T52" in questions[1][2]

    # The economy's own deadline on its own: an order at T61 is one turn behind A2's by more than five.
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 61: FULL}))
    questions = report.verdict_a5(by_turn, [_order_row(61, "BUILDING_GRANARY", "BUILDING")])
    assert questions[2][1] == report.FALSIFIED and "T61" in questions[2][2]


def test_the_a6_question_set_asks_a6_s_own_four():
    """A6 holds when the train is bought early, the war opens early, and the price is a longer window."""
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 70: FULL}), gold_per_turn=6.0)
    rows = [
        # The pinned opening first, so the pin holds and Q1 is comparable.
        _city_order_row(1, 11, "UNIT_SCOUT"),
        _city_order_row(5, 11, "UNIT_SLINGER"),
        _city_order_row(6, 11, "UNIT_SETTLER"),
        _city_order_row(15, 11, "UNIT_BUILDER"),
        _purchase_row(45, "UNIT_CATAPULT"),
        _war_row(52),
        # The keep is what sets `gold_floor`'s horizon, and the rule only runs from T60.
        _keep_row(70),
        *[_red_row(turn) for turn in range(60, 71)],
    ]
    questions = report.verdict_a6(by_turn, rows)
    assert [name.split()[0] for name, _s, _d in questions] == ["Q1", "Q2", "Q3", "Q4"]
    assert questions[0][1] == report.HELD
    assert questions[1][1] == report.HELD and "bought T45" in questions[1][2]
    assert questions[2][1] == report.HELD and "T52" in questions[2][2]
    # 11 red turns to the T70 keep, against A2's whole-attempt 10: the predicted trade happened.
    assert questions[3][1] == report.HELD
    assert "11 red turn(s)" in questions[3][2] and "A2's 10" in questions[3][2]
    # The opening matched the pin, so Q1 carries no deviation note.
    assert "PIN DEVIATED" not in questions[0][2]


def test_the_a6_variable_is_falsified_by_a_produced_train_or_a_late_purchase():
    """Q2 names two distinct failures: the train was produced, or the buy came after T50."""
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 60: FULL}))
    q2 = report.verdict_a6(by_turn, [_order_row(40, "UNIT_CATAPULT")])[1]
    assert q2[1] == report.FALSIFIED and "produced" in q2[2] and "T40" in q2[2]

    q2 = report.verdict_a6(by_turn, [_purchase_row(52, "UNIT_CATAPULT")])[1]
    assert q2[1] == report.FALSIFIED and "T52" in q2[2]

    # Nothing at all by T50: the first siege unit does not exist, so there is no early buy either.
    q2 = report.verdict_a6(by_turn, [])[1]
    assert q2[1] == report.FALSIFIED and "not existing at all" in q2[2]


def test_the_a6_war_and_cost_questions_open_then_falsify():
    """Q3 is judged at A2's own T60; Q4's price needs both an early war and a longer red window."""
    early = _floored(frames({1: {"WARRIOR": 1}, 40: {"WARRIOR": 1}}))
    assert [status for _n, status, _d in report.verdict_a6(early, [])] == [report.OPEN] * 4

    bought = [_purchase_row(45, "UNIT_CATAPULT")]
    # No declaration at all: Q4 decides at T55, Q3 only at A2's T60 - the two deadlines differ.
    at_56 = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 56: FULL}))
    questions = report.verdict_a6(at_56, bought)
    assert questions[2][1] == report.OPEN and "no war-declaration row" in questions[2][2]
    assert questions[3][1] == report.FALSIFIED
    at_61 = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 61: FULL}))
    questions = report.verdict_a6(at_61, bought)
    assert questions[2][1] == report.FALSIFIED and "no war-declaration row" in questions[2][2]
    assert questions[3][1] == report.FALSIFIED

    # A war that opens late falsifies both the timing and the trade.
    questions = report.verdict_a6(at_61, [*bought, _war_row(58)])
    assert questions[2][1] == report.FALSIFIED and "T58" in questions[2][2]
    assert questions[3][1] == report.FALSIFIED and "later than T55" in questions[3][2]

    # An early war whose red window is no longer than A2's: the purchase turned out free.
    questions = report.verdict_a6(at_61, [*bought, _war_row(52), _red_row(61), _red_row(62)])
    assert questions[3][1] == report.FALSIFIED and "free" in questions[3][2]

    # An early war with the window still running is not a verdict yet.
    questions = report.verdict_a6(at_56, [*bought, _war_row(52)])
    assert questions[3][1] == report.OPEN and "not final" in questions[3][2]


def test_the_a7_question_set_asks_a7_s_own_four():
    """A7 holds when two cities produced army units before the first city was kept."""
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 74: FULL}))
    rows = [
        _city_order_row(30, 11, "UNIT_WARRIOR"),
        _city_order_row(32, 11, "UNIT_ARCHER"),
        _city_order_row(40, 22, "UNIT_WARRIOR"),
        _keep_row(74),
    ]
    questions = report.verdict_a7(by_turn, rows)
    assert [name.split()[0] for name, _s, _d in questions] == ["Q1", "Q2", "Q3", "Q4"]
    assert questions[0][1] == report.HELD
    assert questions[1][1] == report.HELD
    assert "city 11 2 (first T30)" in questions[1][2]
    assert "city 22 1 (first T40)" in questions[1][2]
    assert "second city's first army order is T40 (city 22)" in questions[1][2]
    assert "before the keep on T74" in questions[1][2]
    # The stricter share measure is printed, and is deliberately not the pass condition.
    assert "stricter secondary measure" in questions[1][2] and "not the pass condition" in questions[1][2]
    assert questions[2][1] == report.HELD and "T74" in questions[2][2]
    assert questions[3][1] == report.HELD


def test_the_a7_second_city_has_to_produce_before_the_keep():
    """The window is the variable: a city that starts after the keep is not a second war city."""
    # One city before a T74 keep, a second only after it: the variable is falsified.
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 74: FULL}))
    rows = [
        _city_order_row(30, 11, "UNIT_WARRIOR"),
        _city_order_row(32, 11, "UNIT_ARCHER"),
        _city_order_row(80, 22, "UNIT_WARRIOR"),
        _keep_row(74),
    ]
    questions = report.verdict_a7(by_turn, rows)
    assert questions[1][1] == report.FALSIFIED
    assert "city 22" not in questions[1][2]  # the per-city counts are inside the window
    assert questions[2][1] == report.HELD

    # No keep yet and one city: the second city could still contribute, so the count is open - and the
    # detail says the whole log is being counted because nothing was kept.
    open_by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 60: FULL}))
    questions = report.verdict_a7(open_by_turn, [_city_order_row(30, 11, "UNIT_WARRIOR")])
    assert questions[1][1] == report.OPEN
    assert "no city was kept by T60" in questions[1][2]
    assert questions[2][1] == report.OPEN

    # No keep by T80 and no second city: both the variable and the deadline falsify.
    late = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 80: FULL}))
    questions = report.verdict_a7(late, [_city_order_row(30, 11, "UNIT_WARRIOR")])
    assert questions[1][1] == report.FALSIFIED
    assert questions[2][1] == report.FALSIFIED and "no keep row" in questions[2][2]

    # A keep after T80 is outside the window.
    too_late = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 85: FULL}))
    rows = [_city_order_row(30, 11, "UNIT_WARRIOR"), _keep_row(85)]
    questions = report.verdict_a7(too_late, rows)
    assert questions[2][1] == report.FALSIFIED and "T85" in questions[2][2]


def test_a_deviated_pin_is_printed_beside_the_new_modes_q1():
    """A Q1 verdict read without the pin would compare an attempt whose opening was not comparable."""
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 60: FULL}))
    opening = [
        _city_order_row(1, 11, "UNIT_SCOUT"),
        _city_order_row(5, 11, "UNIT_SLINGER"),
        _city_order_row(6, 11, "UNIT_SETTLER"),
        _city_order_row(15, 11, "UNIT_BUILDER"),
    ]
    deviated = [*opening[:3], _city_order_row(15, 11, "UNIT_WARRIOR")]
    for setter in (report.verdict_a5, report.verdict_a6, report.verdict_a7):
        assert "PIN DEVIATED" not in setter(by_turn, opening)[0][2]
        q1 = setter(by_turn, deviated)[0]
        assert "PIN DEVIATED" in q1[2] and "UNIT_WARRIOR" in q1[2] and "T15" in q1[2]
    # A2's and A3's verdict text is untouched: for A3 the deviation shows in the doctrine block.
    assert "PIN" not in report.verdict_a3(by_turn, deviated)[0][2]
    assert "PIN" not in report.verdict_a2(by_turn, deviated)[0][2]


def test_asked_questions_dispatches_every_named_set():
    """The one dispatch point both `--verdict` and `--save` go through, and there is no `a4`."""
    by_turn = _floored(frames({1: {"WARRIOR": 1}, 47: FULL, 60: FULL}))
    rows = [
        _city_order_row(1, 11, "UNIT_SCOUT"),
        _city_order_row(5, 11, "UNIT_SLINGER"),
        _city_order_row(6, 11, "UNIT_SETTLER"),
        _city_order_row(15, 11, "UNIT_BUILDER"),
    ]
    ids = {"generic": ["P1", "P2", "P3", "P4"]}
    for name in ("generic", "a2", "a3", "a5", "a6", "a7"):
        got = report.asked_questions(name, by_turn, rows)
        assert [q[0].split()[0] for q in got] == ids.get(name, ["Q1", "Q2", "Q3", "Q4"]), name
        assert all(status in (report.HELD, report.FALSIFIED, report.OPEN) for _n, status, _d in got), name
    assert set(report.QUESTION_SETS) == {"a2", "a3", "a5", "a6", "a7"}
    assert "a4" not in report.QUESTION_SETS
    # The generic set is the only one that takes the caller's own labels.
    generic = report.asked_questions("generic", by_turn, rows, ids=("X1", "X2", "X3", "X4"))
    assert [q[0].split()[0] for q in generic] == ["X1", "X2", "X3", "X4"]
