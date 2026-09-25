"""The play driver's guards, which exist because each one cost units before it was written.

Moscow, T105-T120. A legal attack went unused while a wounded Archer was left beside a Russian Scout
(five of our units were within two tiles and the Scout died to a single shot), and a Battering Ram
plus three Warriors sat out the whole siege because the only units the driver moves are the ones the
caller names - the Ram was killed without ever attacking. These are the two rules that came out of
it, and the unit lookup they are built on.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def load_module():
    spec = importlib.util.spec_from_file_location("play_turn", ROOT / "scripts" / "play-turn.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["play_turn"] = module
    spec.loader.exec_module(module)
    return module


play = load_module()


class FakeUnit:
    def __init__(self, index, unit_type, x, y, moves):
        self.unit_index = index
        self.unit_type = unit_type
        self.x = x
        self.y = y
        self.moves_remaining = moves


UNITS = [
    FakeUnit(1, "UNIT_WARRIOR", 52, 26, 2.0),
    FakeUnit(3, "UNIT_ARCHER", 54, 39, 2.0),
    FakeUnit(4, "UNIT_HEAVY_CHARIOT", 54, 40, 3.0),
    FakeUnit(11, "UNIT_WARRIOR", 55, 38, 2.0),
]


class TestUnitLookup:
    def test_by_index(self):
        assert play.find(UNITS, "11").unit_index == 11

    def test_by_type_substring(self):
        assert play.find(UNITS, "ARCHER").unit_index == 3

    def test_the_unit_prefix_is_optional(self):
        assert play.find(UNITS, "UNIT_HEAVY_CHARIOT").unit_index == 4

    def test_the_first_match_wins(self):
        # The lowest index is why a WARRIOR order kept taking the Shanghai garrison off its city
        # tile - which is why index orders exist at all.
        assert play.find(UNITS, "WARRIOR").unit_index == 1

    def test_no_match_is_none(self):
        assert play.find(UNITS, "SETTLER") is None


class TestTheUnusedAttackGuard:
    def test_an_unused_attack_refuses_the_end(self):
        assert play.end_turn_blocker(["UNIT_ARCHER@54,38 -> UNIT_SCOUT@54,36"], False) is not None

    def test_nothing_unused_lets_the_turn_end(self):
        assert play.end_turn_blocker([], False) is None

    def test_force_overrides_it(self):
        assert play.end_turn_blocker(["anything"], True) is None


class TestTheNamedSkip:
    def test_every_discarded_unit_is_named_with_where_it_stands(self):
        lines = play.format_skipped(UNITS)
        assert len(lines) == len(UNITS)
        assert "UNIT_WARRIOR" in lines[0]
        assert "(52,26)" in lines[0]
        assert "mv2.0" in lines[0]

    def test_the_index_is_in_the_line_so_it_can_be_ordered_next_turn(self):
        assert "[ 4]" in play.format_skipped([UNITS[2]])[0]
