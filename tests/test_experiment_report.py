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
