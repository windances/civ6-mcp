"""The Great Person report hid the reason to keep a Great General alive.

``get_great_people`` listed only the individual's own action. For a Great General
or a Great Admiral that action is a *retirement*: ``activate`` consumes the unit.
The aura those two classes grant merely by existing was never shown at all, and it
is the more valuable half:

- ``ABILITY_GREAT_GENERAL_STRENGTH`` -> ``MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH``,
  Amount ``5`` (game text: "the Great General's combat bonus +5")
- ``ABILITY_GREAT_GENERAL_MOVEMENT`` -> ``MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT``,
  Amount ``1``
- both bound to the land unit classes (melee, ranged, siege, cavalry, recon), with
  the naval equivalents for ``ABILITY_GREAT_ADMIRAL_*``

So an agent following AGENTS.md's "move the GP to its matching district and
activate" had every reason to retire a general on the turn it was recruited and
trade a permanent aura for a one-off. These tests pin the report that stops that.
"""

from civ_mcp.lua.great_people import build_great_people_query, parse_great_people_response
from civ_mcp.narrate import narrate_great_people

AURA_EN = "the Great General's combat bonus +5"
AURA_EN_MOVEMENT = "the Great General provides +1 movement"
RETIRE_EN = "grants one promotion level to a land military unit"


def gp_line(passive: str = "") -> str:
    """A GP| line shaped like the one the Lua prints, with or without the aura."""
    line = (
        "GP|Great General|Hannibal Barca|Classical Era|60|Unclaimed|0|"
        f"{RETIRE_EN}|gold:1100,faith:750,recruit:false|57"
    )
    return f"{line}|{passive}" if passive else line


class TestAuraIsQueried:
    def test_general_aura_keys_are_looked_up(self):
        lua = build_great_people_query()
        assert "GREAT_PERSON_CLASS_GENERAL" in lua
        assert "LOC_GREATPERSON_COMBAT_STRENGTH_AOE_LAND_MODIFIER" in lua
        assert "LOC_ABILITY_GREAT_GENERAL_MOVEMENT_DESCRIPTION" in lua

    def test_admiral_aura_keys_are_looked_up(self):
        lua = build_great_people_query()
        assert "GREAT_PERSON_CLASS_ADMIRAL" in lua
        assert "LOC_GREATPERSON_COMBAT_STRENGTH_AOE_SEA_MODIFIER" in lua
        assert "LOC_ABILITY_GREAT_ADMIRAL_MOVEMENT_DESCRIPTION" in lua

    def test_aura_is_appended_to_the_printed_line(self):
        # Field 11, after the individual id, so the existing indices do not shift.
        lua = build_great_people_query()
        assert '"|" .. passive' in lua


class TestParserReadsTheAura:
    def test_passive_is_parsed(self):
        parsed = parse_great_people_response([gp_line(f"{AURA_EN} {AURA_EN_MOVEMENT}")])
        assert len(parsed) == 1
        assert parsed[0].passive == f"{AURA_EN} {AURA_EN_MOVEMENT}"
        assert parsed[0].ability == RETIRE_EN

    def test_line_without_the_field_still_parses(self):
        # An older MCP, or a class with no aura, must not become a parse error.
        parsed = parse_great_people_response([gp_line()])
        assert len(parsed) == 1
        assert parsed[0].passive == ""
        assert parsed[0].ability == RETIRE_EN

    def test_other_fields_are_unaffected(self):
        parsed = parse_great_people_response([gp_line(AURA_EN)])
        g = parsed[0]
        assert g.class_name == "Great General"
        assert g.individual_name == "Hannibal Barca"
        assert g.cost == 60
        assert g.gold_cost == 1100
        assert g.faith_cost == 750
        assert g.individual_id == 57


class TestNarratorDistinguishesAuraFromRetirement:
    def test_aura_is_reported(self):
        text = narrate_great_people(parse_great_people_response([gp_line(AURA_EN)]))
        assert "Passive aura" in text
        assert AURA_EN in text

    def test_activating_is_labelled_as_consuming_the_unit(self):
        text = narrate_great_people(parse_great_people_response([gp_line(AURA_EN)]))
        assert "CONSUMES the unit" in text
        # The plain "Ability:" label would hide that the unit is spent.
        assert "    Ability:" not in text

    def test_classes_without_an_aura_keep_the_plain_label(self):
        text = narrate_great_people(parse_great_people_response([gp_line()]))
        assert "    Ability:" in text
        assert "Passive aura" not in text
