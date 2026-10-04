"""The city line must show the amenity *difference*, not a bare gross number.

`CityInfo.amenities` is gross - the game's `GetAmenities()` net plus the demand
(`src/civ_mcp/lua/cities.py:349-351`) - so on its own it says nothing: the demand scales with
population, and 12 amenities against a demand of 9 is a healthy city while 12 against 14 is not.
The parser has carried `amenities_needed` since the column was appended at index 36, and
`end_turn._city_health_metrics` turns it into `amenities_floor`/`cities_unhappy`, but the rule that
would print those (`mind-the-amenities`) is still staged in `prompts/checks/pending/`, and the
narrator printed only the gross figure. So a live session reading `get_cities` saw
`Amenities 22` and had no way to tell a surplus from a shortfall.

Measured on the live match at T341: the session was choosing amenity buildings (an Entertainment
Complex in Novgorod and in Alexandria, a Zoo in Changsha, an Arena in Haarlem) with only the game's
bare "Need More Amenities" notification - which does not name the city - to go on.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import narrate  # noqa: E402
from civ_mcp.lua.models import CityInfo  # noqa: E402


def city(**kw) -> CityInfo:
    base = dict(
        city_id=1, name="Xi'an", population=9, x=23, y=30,
        food=30.0, production=20.0, gold=5.0, science=10.0, culture=3.0, faith=0.0,
        housing=12.0, amenities=12, amenities_needed=9,
        turns_to_grow=3, currently_building="nothing", production_turns_left=0,
        defense_strength=80, garrison_hp=0, garrison_max_hp=200,
        wall_hp=400, wall_max_hp=400,
    )
    base.update(kw)
    return CityInfo(**base)


def line(c: CityInfo) -> str:
    return next(l for l in narrate.narrate_cities([c]).splitlines() if c.name in l)


def test_a_surplus_shows_both_numbers() -> None:
    text = line(city(amenities=12, amenities_needed=9))
    assert "Amenities 12/9" in text
    assert "SHORT" not in text


def test_a_shortfall_is_named_with_its_sign() -> None:
    """The case the whole column exists for: demand above supply."""
    text = line(city(amenities=12, amenities_needed=14))
    assert "Amenities 12/14" in text
    assert "!! SHORT -2" in text


def test_a_server_that_did_not_report_the_demand_prints_the_bare_number() -> None:
    """`amenities_needed == 0` means unreported, so no ratio and no verdict is implied."""
    text = line(city(amenities=12, amenities_needed=0))
    assert "Amenities 12 |" in text
    assert "/" not in text.split("Amenities")[1].split("|")[0]
    assert "SHORT" not in text


def test_an_exactly_met_demand_is_flagged_as_the_limit_not_as_healthy() -> None:
    """`slack == 0` is the boundary the game acts on.

    Measured live at T344: Sidon read `2/2` and drew no marker, while the game's own notification
    named Sidon among the cities needing more amenities. A surplus above the demand is healthy;
    sitting exactly on it is the first thing to look at.
    """
    text = line(city(amenities=2, amenities_needed=2))
    assert "Amenities 2/2" in text
    assert "!! AT LIMIT" in text
    assert "SHORT" not in text


def test_the_two_numbers_are_not_the_same_number() -> None:
    """A gross reading of 20 must not be reported as a surplus when the demand is 22."""
    text = line(city(amenities=20, amenities_needed=22))
    assert "Amenities 20/22" in text
    assert "!! SHORT -2" in text
