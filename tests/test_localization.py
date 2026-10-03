"""English names for localized game data - and the cases where it must change nothing.

The module's contract is asymmetric on purpose: resolving a name is a convenience, while resolving
one *wrongly* is a defect that reaches the model as a plausible fact. So the tests spend as much
effort on the no-ops as on the hits, and one of them pins that a miss returns the input unchanged.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import localization as loc  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


@pytest.fixture
def table(tmp_path, monkeypatch):
    """A table of our own, so the tests never depend on a built one or on the game install."""

    def build(by_type=None, by_zh=None, by_space=None):
        path = tmp_path / "loc-en-names.json"
        path.write_text(
            json.dumps(
                {
                    "by_type": by_type or {},
                    "by_zh": by_zh or {},
                    "by_space": by_space or {},
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(loc, "table_path", lambda: path)
        loc.reset_cache()
        return path

    yield build
    loc.reset_cache()


def no_table(tmp_path, monkeypatch):
    monkeypatch.setattr(loc, "table_path", lambda: tmp_path / "absent.json")
    loc.reset_cache()


class TestWithNoTable:
    """A checkout without the game install, and every existing test, must behave as before."""

    def test_everything_is_returned_unchanged(self, tmp_path, monkeypatch):
        no_table(tmp_path, monkeypatch)
        assert loc.english("西安") == "西安"
        assert loc.by_type("UNIT_ARCHER") is None
        assert loc.by_text("西安") is None

    def test_a_record_is_left_alone(self, tmp_path, monkeypatch):
        no_table(tmp_path, monkeypatch)
        unit = m.UnitInfo(
            unit_id=1, unit_index=1, name="弓箭手", unit_type="UNIT_ARCHER",
            x=0, y=0, moves_remaining=2, max_moves=2, health=100, max_health=100,
        )
        loc.englishify(unit)
        assert unit.name == "弓箭手"

    def test_a_corrupt_table_does_not_raise(self, tmp_path, monkeypatch):
        path = tmp_path / "loc-en-names.json"
        path.write_text("{not json", encoding="utf-8")
        monkeypatch.setattr(loc, "table_path", lambda: path)
        loc.reset_cache()
        assert loc.english("西安") == "西安"


class TestResolution:
    def test_english_text_is_never_touched(self, table):
        table(by_zh={"西安": "Xi'an"})
        assert loc.english("Crossbowman") == "Crossbowman"

    def test_a_sibling_code_wins_over_the_reverse_map(self, table):
        """The code is exact; the reverse map is a guess that has already been filtered."""
        table(by_type={"UNIT_BUILDER": "Builder"}, by_zh={"建造者": "Built By"})
        assert loc.english("建造者", "UNIT_BUILDER") == "Builder"

    def test_the_reverse_map_is_the_fallback(self, table):
        table(by_zh={"西安": "Xi'an"})
        assert loc.english("西安") == "Xi'an"

    def test_a_space_beats_the_flat_map(self, table):
        """`毛利` is dropped from the flat map as ambiguous and unique inside its own space."""
        table(by_zh={}, by_space={"CIVILIZATION": {"毛利": "Māori"}})
        assert loc.english("毛利", space="CIVILIZATION") == "Māori"

    def test_a_miss_returns_the_input_unchanged(self, table):
        """Never guess: a wrong name is worse than a Chinese one."""
        table(by_zh={"西安": "Xi'an"})
        assert loc.english("使此城每回合的忠诚度+2") == "使此城每回合的忠诚度+2"

    def test_has_cjk_sees_chinese_and_not_latin(self):
        assert loc.has_cjk("西安")
        assert not loc.has_cjk("Xi'an")
        assert not loc.has_cjk("")


class TestEnglishify:
    def test_a_unit_name_comes_from_its_type_code(self, table):
        table(by_type={"UNIT_ARCHER": "Archer"})
        unit = m.UnitInfo(
            unit_id=1, unit_index=1, name="弓箭手", unit_type="UNIT_ARCHER",
            x=0, y=0, moves_remaining=2, max_moves=2, health=100, max_health=100,
        )
        loc.englishify(unit)
        assert unit.name == "Archer"

    def test_repeated_english_codes_do_not_corrupt_another_field(self, table):
        """The generic pairing tries every code on the record; a non-type string must not match."""
        table(by_type={"UNIT_ARCHER": "Archer", "UNIT_CATAPULT": "Catapult"})
        unit = m.UnitInfo(
            unit_id=1, unit_index=1, name="投石车", unit_type="UNIT_CATAPULT",
            x=0, y=0, moves_remaining=2, max_moves=2, health=100, max_health=100,
            upgrade_target="UNIT_ARCHER",
        )
        loc.englishify(unit)
        assert unit.name == "Catapult", "the unit's own type wins, not the upgrade target"

    def test_a_list_of_names_is_resolved_element_by_element(self, table):
        table(by_space={"CIVIC": {"军事训练": "Military Training", "神权": "Theology"}})
        civic = m.LockedCivic(
            name="Mercenaries", civic_type="CIVIC_MERCENARIES",
            missing_prereqs=["军事训练", "神权"], era="ERA_MEDIEVAL",
        )
        loc.englishify(civic)
        assert civic.missing_prereqs == ["Military Training", "Theology"]

    def test_a_name_only_field_uses_its_declared_space(self, table):
        table(by_space={"ERA": {"文艺复兴时期": "Renaissance Era"}})
        overview = m.GameOverview.__new__(m.GameOverview)
        dataclasses.fields(m.GameOverview)
        object.__setattr__(overview, "era_name", "文艺复兴时期")
        loc.englishify(overview)
        assert overview.era_name == "Renaissance Era"


class TestTheTreeWalk:
    def test_it_reaches_a_tuple_of_records(self, table):
        """`get_cities` and `get_empire_resources` return tuples; a list-only walk skipped them."""
        table(by_space={"CITY": {"西安": "Xi'an"}})
        city = m.CityInfo.__new__(m.CityInfo)
        object.__setattr__(city, "name", "西安")
        result = loc.englishify_tree(([city], ["note"]))
        assert result[0][0].name == "Xi'an"

    def test_it_reaches_a_nested_record(self, table):
        """A first version stopped at the outer record, leaving every sub-record in Chinese."""
        table(by_space={"CIVILIZATION": {"毛利": "Māori"}})
        outer = m.VictoryProgress.__new__(m.VictoryProgress)
        inner = m.VictoryPlayerProgress.__new__(m.VictoryPlayerProgress)
        object.__setattr__(inner, "name", "毛利")
        object.__setattr__(outer, "players", [inner])
        loc.englishify_tree(outer)
        assert outer.players[0].name == "Māori"

    def test_a_dict_keyed_by_a_localized_name_is_rebuilt(self, table):
        """`unit_breakdown` is `{unit name: count}` - the keys are the data, not the values.

        The keys are *localized names*, not type codes, so they come from the reverse map or from
        the field's own space - a sibling code is not evidence about them.
        """
        table(by_space={"UNIT": {"建造者": "Builder", "弓箭手": "Archer"}})
        overview = m.GameOverview.__new__(m.GameOverview)
        object.__setattr__(overview, "unit_breakdown", {"建造者": 3, "弓箭手": 2})
        loc.englishify(overview)
        assert overview.unit_breakdown == {"Builder": 3, "Archer": 2}

    def test_a_key_it_cannot_resolve_is_left_alone(self, table):
        table(by_space={"UNIT": {"建造者": "Builder"}})
        overview = m.GameOverview.__new__(m.GameOverview)
        object.__setattr__(overview, "unit_breakdown", {"建造者": 3, "某个未收录单位": 1})
        loc.englishify(overview)
        assert overview.unit_breakdown == {"Builder": 3, "某个未收录单位": 1}

    def test_a_sibling_code_is_not_stamped_onto_every_field(self, table):
        """A code is evidence for a *name*, not for every unresolved string on the record.

        Without this, one code that happened to resolve would be applied to each of them, turning a
        missing name into a wrong one.
        """
        table(by_type={"TECH_POTTERY": "Pottery"})
        overview = m.GameOverview.__new__(m.GameOverview)
        object.__setattr__(overview, "game_speed", "TECH_POTTERY")
        object.__setattr__(overview, "current_research", "火药")
        loc.englishify(overview)
        assert overview.current_research == "火药", "not a `name` field: the code must not be used"

    def test_a_great_person_uses_its_own_spaces(self, table):
        table(
            by_space={
                "GREAT_PERSON_CLASS": {"大预言家": "Great Prophet"},
                "ERA": {"古典时期": "Classical Era"},
            }
        )
        person = m.GreatPersonInfo.__new__(m.GreatPersonInfo)
        object.__setattr__(person, "class_name", "大预言家")
        object.__setattr__(person, "era_name", "古典时期")
        object.__setattr__(person, "ability", "使此城每回合的忠诚度+2")
        loc.englishify(person)
        assert person.class_name == "Great Prophet"
        assert person.era_name == "Classical Era"
        assert person.ability == "使此城每回合的忠诚度+2", "prose is never guessed at"

    def test_it_returns_the_same_object(self, table):
        table()
        value = m.UnitInfo(
            unit_id=1, unit_index=1, name="Archer", unit_type="UNIT_ARCHER",
            x=0, y=0, moves_remaining=2, max_moves=2, health=100, max_health=100,
        )
        assert loc.englishify_tree(value) is value


class TestTheDecorator:
    def test_it_rewrites_what_a_read_returns(self, table):
        table(by_type={"UNIT_ARCHER": "Archer"})

        @loc.english_output
        async def read():
            return [
                m.UnitInfo(
                    unit_id=1, unit_index=1, name="弓箭手", unit_type="UNIT_ARCHER",
                    x=0, y=0, moves_remaining=2, max_moves=2, health=100, max_health=100,
                )
            ]

        assert asyncio.run(read())[0].name == "Archer"

    def test_a_failing_read_still_raises(self, table):
        table()

        @loc.english_output
        async def read():
            raise RuntimeError("tuner busy")

        with pytest.raises(RuntimeError):
            asyncio.run(read())
