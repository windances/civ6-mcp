"""The play driver's guards, which exist because each one cost units before it was written.

Moscow, T105-T120. A legal attack went unused while a wounded Archer was left beside a Russian Scout
(five of our units were within two tiles and the Scout died to a single shot), and a Battering Ram
plus three Warriors sat out the whole siege because the only units the driver moves are the ones the
caller names - the Ram was killed without ever attacking. These are the two rules that came out of
it, and the unit lookup they are built on.
"""

from __future__ import annotations

import asyncio
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


class TestThePopupLayerHasACommand:
    """The layer that holds a turn without leaving any other trace (measured live T96).

    The driver had no way to clear it: `end` reported the same `Turn 95 -> 96` twice while the
    screen read `NATURAL DISASTER OCCURRING`, and one `dismiss_popup` cleared 23 popups
    (`cinematic_camera`, `NaturalDisasterPopup`, `InvitePopup` x20). A normal MCP session has
    `spectator.PopupWatcher` for this; a direct session had nothing.
    """

    class FakePopups:
        def __init__(self, answers):
            self.answers = list(answers)
            self.calls = 0

        async def dismiss_popup(self):
            self.calls += 1
            return self.answers.pop(0) if self.answers else "No popups to dismiss."

    def test_it_stops_at_the_first_pass_that_found_nothing(self):
        gs = self.FakePopups(["Dismissed: NaturalDisasterPopup, InvitePopup", "No popups to dismiss."])
        answers = asyncio.run(play.dismiss_popups(gs))
        assert answers == ["Dismissed: NaturalDisasterPopup, InvitePopup", "No popups to dismiss."]
        assert gs.calls == 2, "a pass that found nothing ends the loop"

    def test_it_is_bounded_even_when_popups_keep_appearing(self):
        gs = self.FakePopups(["Dismissed: a", "Dismissed: b", "Dismissed: c", "Dismissed: d"])
        answers = asyncio.run(play.dismiss_popups(gs))
        assert len(answers) == 3, "re-dismissing in a loop during AI processing is how a turn hangs"
        assert gs.calls == 3

    def test_one_pass_reports_everything_it_cleared(self):
        # The live T96 shape: one call, 23 names in it.
        report = "Dismissed: cinematic_camera, NaturalDisasterPopup, " + ", ".join(
            ["InvitePopup"] * 20
        )
        gs = self.FakePopups([report, "No popups to dismiss."])
        answers = asyncio.run(play.dismiss_popups(gs))
        assert answers[0].count("InvitePopup") == 20

    def test_the_default_is_one_pass_when_nothing_is_there(self):
        gs = self.FakePopups(["No popups to dismiss."])
        assert asyncio.run(play.dismiss_popups(gs)) == ["No popups to dismiss."]
        assert gs.calls == 1


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


class TestTheWoundedInReachWarning:
    """All three losses of the T103-T130 Russian war were a wounded unit left inside an enemy's
    reach; the rule was in the doctrine the whole time and nothing printed it at the moment the turn
    was closed.
    """

    def test_a_wounded_unit_two_tiles_from_an_enemy_is_named(self):
        pairs = [
            {"unit": "UNIT_ARCHER", "unit_at": (51, 36), "unit_hp": 35,
             "enemy": "UNIT_SWORDSMAN", "enemy_at": (50, 37), "distance": 1},
        ]
        lines = play.wounded_in_reach(pairs)
        assert len(lines) == 1
        assert "UNIT_ARCHER" in lines[0] and "35 HP" in lines[0]

    def test_a_healthy_unit_is_not_named(self):
        pairs = [
            {"unit": "UNIT_ARCHER", "unit_at": (51, 36), "unit_hp": 100,
             "enemy": "UNIT_SWORDSMAN", "enemy_at": (50, 37), "distance": 1},
        ]
        assert play.wounded_in_reach(pairs) == []

    def test_a_wounded_unit_out_of_reach_is_not_named(self):
        pairs = [
            {"unit": "UNIT_ARCHER", "unit_at": (51, 36), "unit_hp": 30,
             "enemy": "UNIT_SWORDSMAN", "enemy_at": (50, 40), "distance": 4},
        ]
        assert play.wounded_in_reach(pairs) == []


class TestStaleUnusedAttacks:
    """The adapter's Lua state lags inside a turn frame, so a unit that has just acted is still
    reported as holding a legal attack - measured live 2026-09-25 at 阿斯特拉罕, where the driver
    used the attack it was told about, called `end` again, and was refused with the same line.
    """

    LINE = "UNIT_ARCHER@51,36 -> UNIT_SWORDSMAN@50,37(87hp)"

    def _unit(self, type_name, x, y, moves):
        return FakeUnit(99, type_name, x, y, moves)

    def test_a_spent_unit_is_dropped(self):
        units = [self._unit("UNIT_ARCHER", 51, 36, 0)]
        assert play.drop_stale_unused([self.LINE], units) == []

    def test_a_unit_that_still_has_moves_is_kept(self):
        units = [self._unit("UNIT_ARCHER", 51, 36, 2)]
        assert play.drop_stale_unused([self.LINE], units) == [self.LINE]

    def test_a_unit_that_has_moved_away_is_dropped(self):
        units = [self._unit("UNIT_ARCHER", 52, 36, 2)]
        assert play.drop_stale_unused([self.LINE], units) == []

    def test_an_unparseable_line_is_kept_so_it_is_never_swallowed(self):
        assert play.drop_stale_unused(["garbage"], []) == ["garbage"]


class TestTheNamedSkip:
    def test_every_discarded_unit_is_named_with_where_it_stands(self):
        lines = play.format_skipped(UNITS)
        assert len(lines) == len(UNITS)
        assert "UNIT_WARRIOR" in lines[0]
        assert "(52,26)" in lines[0]
        assert "mv2.0" in lines[0]

    def test_the_index_is_in_the_line_so_it_can_be_ordered_next_turn(self):
        assert "[ 4]" in play.format_skipped([UNITS[2]])[0]


class TestTheIdleRangedWarning:
    """A ranged unit that is close enough to matter and too far to fire is the one idle nobody
    reports: it has no legal attack (so the unused-attack guard is silent) and it is one of a dozen
    lines in the skip list. Measured T113-T117 at 圣彼得堡: three Archers sat 4-6 tiles out while the
    city was ground down by two Catapults, and the siege took a turn longer than it had to.
    """

    LINE = "IDLE_RANGED|UNIT_ARCHER|53,38|3|阿斯特拉罕"

    def test_a_row_parses_into_unit_place_distance_and_city(self):
        assert play.parse_idle_ranged([self.LINE, "garbage", "NO_MOVES"]) == [
            {"unit": "UNIT_ARCHER", "unit_at": (53, 38), "distance": 3, "city": "阿斯特拉罕"}
        ]

    def test_the_warning_names_the_unit_where_it_stands_and_the_city(self):
        rows = play.parse_idle_ranged([self.LINE])
        lines = play.idle_ranged_warning(rows)
        assert len(lines) == 1
        assert "UNIT_ARCHER" in lines[0]
        assert "(53, 38)" in lines[0]
        assert "3 from 阿斯特拉罕" in lines[0]

    def test_nearest_first_so_the_most_actionable_unit_is_on_top(self):
        rows = play.parse_idle_ranged(
            ["IDLE_RANGED|UNIT_CATAPULT|60,60|5|X", self.LINE]
        )
        lines = play.idle_ranged_warning(rows)
        assert "UNIT_ARCHER" in lines[0]

    def test_nothing_near_means_nothing_printed(self):
        assert play.idle_ranged_warning([]) == []


class TestRole:
    def test_the_classes_the_formation_is_built_on(self):
        assert play.role("UNIT_WARRIOR") == "screen"
        assert play.role("UNIT_SPEARMAN") == "screen"
        assert play.role("UNIT_HEAVY_CHARIOT") == "screen"
        assert play.role("UNIT_ARCHER") == "ranged"
        assert play.role("UNIT_CATAPULT") == "siege"
        assert play.role("UNIT_BATTERING_RAM") == "support"
        assert play.role("UNIT_BUILDER") == "civilian"

    def test_the_unit_prefix_is_optional(self):
        assert play.role("ARCHER") == "ranged"


class Posture:
    """The fields `screen_rule_failure` reads, as the adapter reports them."""

    def __init__(self, unit_type, enemy_distance, screen_enemy_distance, x=0, y=0):
        self.unit_type = unit_type
        self.enemy_distance = enemy_distance
        self.screen_enemy_distance = screen_enemy_distance
        self.x = x
        self.y = y


class TestTheScreenRule:
    def test_a_closer_screen_passes(self):
        assert play.screen_rule_failure(Posture("UNIT_CATAPULT", 2, 1)) is None

    def test_a_screen_exactly_as_close_fails(self):
        # "As close as the siege unit" is a second target, not cover.
        assert play.screen_rule_failure(Posture("UNIT_CATAPULT", 2, 2)) is not None

    def test_an_enemy_beyond_two_tiles_is_not_this_turn_s_problem(self):
        # The rule is "within two tiles of an enemy"; flagged at six it can never be acted on, and a
        # warning nobody can act on trains the operator to ignore the whole block. Measured T132.
        assert play.screen_rule_failure(Posture("UNIT_CATAPULT", 6, 6)) is None

    def test_a_missing_screen_inside_reach_still_fails(self):
        assert play.screen_rule_failure(Posture("UNIT_CATAPULT", 2, None)) is not None

    def test_no_screen_at_all_fails(self):
        assert play.screen_rule_failure(Posture("UNIT_CATAPULT", 2, None)) is not None


class TestFormationViolations:
    pair = staticmethod(
        lambda unit, uat, hp, enemy, eat, distance: {
            "unit": unit,
            "unit_at": uat,
            "unit_hp": hp,
            "enemy": enemy,
            "enemy_at": eat,
            "distance": distance,
        }
    )

    def test_shooters_in_front_of_every_screen_is_inverted(self):
        pairs = [
            self.pair("UNIT_ARCHER", (53, 39), 100, "UNIT_SWORDSMAN", (52, 39), 1),
            self.pair("UNIT_WARRIOR", (55, 38), 100, "UNIT_SWORDSMAN", (52, 39), 3),
        ]
        problems = play.formation_violations(pairs)
        assert any(p.startswith("INVERTED") for p in problems)

    def test_a_screen_strictly_in_front_is_not_inverted(self):
        pairs = [
            self.pair("UNIT_ARCHER", (54, 38), 100, "UNIT_SWORDSMAN", (52, 39), 2),
            self.pair("UNIT_WARRIOR", (53, 38), 100, "UNIT_SWORDSMAN", (52, 39), 1),
        ]
        assert play.formation_violations(pairs) == []

    def test_a_wounded_unit_in_melee_reach_is_bait(self):
        # The Archer at 10 HP beside a Russian Scout: five of our units were within two tiles and
        # the Scout died to a single shot.
        pairs = [self.pair("UNIT_ARCHER", (54, 38), 10, "UNIT_SCOUT", (54, 36), 2)]
        assert any(p.startswith("BAIT") for p in play.formation_violations(pairs))

    def test_a_wounded_unit_out_of_reach_is_not_flagged(self):
        pairs = [self.pair("UNIT_ARCHER", (54, 38), 10, "UNIT_SCOUT", (54, 36), 4)]
        assert play.formation_violations(pairs) == []

    def test_no_contact_is_no_violation(self):
        assert play.formation_violations([]) == []


class TestPairParsing:
    def test_a_pair_line_becomes_a_row(self):
        rows = play.parse_pairs(
            ["PAIR|123|UNIT_ARCHER|54,38|10|UNIT_SCOUT|54,36|2", "noise"]
        )
        assert len(rows) == 1
        assert rows[0]["unit"] == "UNIT_ARCHER"
        assert rows[0]["unit_at"] == (54, 38)
        assert rows[0]["unit_hp"] == 10
        assert rows[0]["distance"] == 2

    def test_junk_is_ignored(self):
        assert play.parse_pairs(["", "PAIR|short", None]) == []


class TestTheProduceTileArgument:
    """`produce <city> <ITEM> [X,Y]` - the two spellings, and the crash that started this.

    Measured live T103: `play-turn.py produce Chengdu BUILDING_ETEMENANKI 53 23` - the shape a
    hand-typed call takes - died with `ValueError: too many values to unpack` out of an inline
    `(int(v) for v in sys.argv[4].split(","))`, printing a stack trace for a command whose problem
    was one missing comma. Both spellings are read now, and everything else is a usage line.
    """

    def test_the_documented_comma_form(self):
        assert play.parse_tile_args(["53,23"]) == (53, 23)

    def test_the_space_separated_form_that_used_to_crash(self):
        assert play.parse_tile_args(["53", "23"]) == (53, 23)

    def test_negative_and_large_coordinates_survive(self):
        assert play.parse_tile_args(["-3,140"]) == (-3, 140)

    def test_a_single_token_with_no_comma_is_not_a_tile(self):
        assert play.parse_tile_args(["53"]) is None

    def test_three_tokens_are_not_a_tile(self):
        assert play.parse_tile_args(["53", "23", "9"]) is None

    def test_a_comma_triple_is_not_a_tile(self):
        assert play.parse_tile_args(["53,23,9"]) is None

    def test_non_numbers_are_not_a_tile(self):
        assert play.parse_tile_args(["a,b"]) is None
        assert play.parse_tile_args(["53", "north"]) is None

    def test_no_argument_is_not_a_tile(self):
        assert play.parse_tile_args([]) is None

