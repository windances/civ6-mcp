"""Units inside a city are reported at the city tile - say so, instead of looking like a bug.

Civ VI reports every unit inside a city at the city's own coordinates, so a raw `get_units`
listing showed "2 Archers + 1 Warrior at (57,29)" for ten consecutive turns. Nothing was wrong:
(57,29) is Beijing. Two independent advisor rehearsals flagged it as an impossible stack, because
the snapshot they were handed did not carry city coordinates - which is exactly the failure this
annotation prevents, on both sides: the agent reading `get_units`, and the check engine deciding
whether a multi-unit tile is a garrison or an anomaly.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import narrate as nr  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def unit(uid: int, unit_type: str, x: int, y: int) -> m.UnitInfo:
    return m.UnitInfo(
        unit_id=uid, unit_index=uid, name=unit_type, unit_type=unit_type, x=x, y=y,
        moves_remaining=2, max_moves=2, health=100, max_health=100,
        combat_strength=20 if "BUILDER" not in unit_type else 0,
    )


def city(city_id: int, name: str, x: int, y: int) -> m.CitySnapshot:
    return m.CitySnapshot(city_id=city_id, name=name, population=5, currently_building="",
                          x=x, y=y)


class TestTheNarrationMarksCityTiles:
    def test_a_garrison_is_labelled_with_its_city(self):
        text = nr.narrate_units(
            [unit(1, "UNIT_ARCHER", 57, 29), unit(2, "UNIT_WARRIOR", 57, 29)],
            cities={1: city(1, "Beijing", 57, 29)},
        )
        assert text.count("[IN Beijing]") == 2

    def test_a_unit_in_the_field_gets_no_label(self):
        text = nr.narrate_units([unit(1, "UNIT_ARCHER", 53, 35)], cities={1: city(1, "Beijing", 57, 29)})
        assert "[IN " not in text

    def test_a_civilian_on_a_city_tile_is_not_called_a_garrison(self):
        # one-garrison-per-city counts fighting units; a builder in a city is not one.
        text = nr.narrate_units([unit(1, "UNIT_BUILDER", 57, 29)], cities={1: city(1, "Beijing", 57, 29)})
        assert "[IN Beijing]" not in text

    def test_without_city_data_nothing_is_invented(self):
        text = nr.narrate_units([unit(1, "UNIT_ARCHER", 57, 29)])
        assert "[IN " not in text
        assert "(57,29)" in text


class TestTheSnapshotWarning:
    CITIES = {1: city(1, "Beijing", 57, 29), 2: city(2, "Changsha", 52, 30)}

    def _gs(self, units):
        gs = type("GS", (), {})()
        gs._last_snapshot = type("Snap", (), {"units": units, "cities": self.CITIES})()
        return gs

    def test_a_stack_on_a_city_tile_is_a_garrison_not_a_warning(self):
        units = {1: unit(1, "UNIT_ARCHER", 57, 29), 2: unit(2, "UNIT_WARRIOR", 57, 29)}
        metrics = et._garrison_metrics(self._gs(units), units)
        assert metrics["cities_over_garrison"] == 1
        assert metrics["unexplained_stacks"] == 0

    def test_a_stack_elsewhere_is_flagged(self):
        units = {1: unit(1, "UNIT_ARCHER", 40, 40), 2: unit(2, "UNIT_WARRIOR", 40, 40)}
        metrics = et._garrison_metrics(self._gs(units), units)
        assert metrics["unexplained_stacks"] == 1

    def test_the_warning_names_the_consequence(self):
        # The text is what the orchestrator reads, so pin the part that says what to do.
        source = (pathlib.Path(__file__).resolve().parents[1] / "src" / "civ_mcp" / "end_turn.py").read_text("utf-8")
        assert "SNAPSHOT WARNING" in source
        assert "treat" in source and "suspect" in source
