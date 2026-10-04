"""A city-scoped notification must name its city, and `GetMessage()` never does.

Three notification types are *about* one city and carry neither piece of data a reader would reach
for: `GetMessage()` is the generic banner ("needs more Amenities", "city is not fully powered") and
`GetLocation()` returns the sentinel `-9999,-9999`. Measured live on turn 344:

    NOTIFICATION_CITY_LOW_AMENITIES  loc=-9999,-9999  需要更高的宜居度
    NOTIFICATION_CITY_UNPOWERED      loc=-9999,-9999  城市供电不足
    NOTIFICATION_HOUSING_PREVENTING_GROWTH  loc=-9999,-9999  需要更多住房

The city is in `GetSummary()`, the sentence the game's own panel shows, which nothing read. Measured
in the same read: three low-amenity notifications whose summaries named Amsterdam, Sidon and Lagash,
and two power notifications reading "Novgorod needs 3 power, has 2" and "Yerevan needs 3, has 0".

That matters because it is the only place those cities are named. `get_cities` prints the amenity
figure *gross* (demand travels separately), so a session choosing amenity buildings has nothing else
to go on: on the same turn a live session had built an Entertainment Complex in Novgorod and in
Alexandria, a Zoo in Changsha and an Arena in Haarlem - none of which was one of the three cities
the game was actually complaining about.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import narrate  # noqa: E402
from civ_mcp.lua.notifications import parse_notifications_response  # noqa: E402

SENT = "---END---"


def parsed(*rows: str):
    return parse_notifications_response([*rows, SENT])


def test_the_summary_survives_parsing() -> None:
    n = parsed("NOTIF|NOTIFICATION_CITY_LOW_AMENITIES|需要更高的宜居度|344|-9999,-9999|阿姆斯特丹需要更高的宜居度。")[0]
    assert n.message == "需要更高的宜居度"
    assert n.x == -9999 and n.y == -9999
    assert n.summary == "阿姆斯特丹需要更高的宜居度。"


def test_a_low_amenity_notification_names_its_city_in_the_output() -> None:
    text = narrate.narrate_notifications(
        parsed("NOTIF|NOTIFICATION_CITY_LOW_AMENITIES|需要更高的宜居度|344|-9999,-9999|阿姆斯特丹需要更高的宜居度。")
    )
    assert "需要更高的宜居度" in text
    assert "阿姆斯特丹" in text, "the banner alone does not say which city"


def test_an_unpowered_notification_carries_its_numbers() -> None:
    text = narrate.narrate_notifications(
        parsed("NOTIF|NOTIFICATION_CITY_UNPOWERED|城市供电不足|344|-9999,-9999|"
               "强化诺夫哥罗德的建筑或项目需要3点 电力，但现在仅能获得2点。")
    )
    assert "诺夫哥罗德" in text
    assert "需要3点" in text and "仅能获得2点" in text


def test_a_notification_without_a_summary_is_unchanged() -> None:
    """A sixth column that the server did not send must not add a blank line."""
    text = narrate.narrate_notifications(
        parsed("NOTIF|NOTIFICATION_UNIT_PROMOTION_AVAILABLE|单位可升级|315|-9999,-9999|")
    )
    assert "\n      " not in text, f"no summary line expected, got:\n{text}"
    assert text == (
        "== Action Required (1) ==\n"
        "  * 单位可升级  -> Use: get_unit_promotions(unit_id=...) then promote_unit()"
    )


def test_a_summary_equal_to_the_message_is_not_repeated() -> None:
    text = narrate.narrate_notifications(
        parsed("NOTIF|NOTIFICATION_CITY_LOW_AMENITIES|需要更高的宜居度|344|-9999,-9999|需要更高的宜居度")
    )
    assert text.count("需要更高的宜居度") == 1


def test_a_notification_with_a_location_keeps_it() -> None:
    text = narrate.narrate_notifications(
        parsed("NOTIF|NOTIFICATION_PLAYER_DEFEATED|失败！|165|61,42|")
    )
    assert "at (61,42)" in text
