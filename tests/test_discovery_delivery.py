"""How a discovery reaches the agent: the sight block, and the `NEW TARGET` event.

Measured before this existed: the discovery narration attached to a move reported only tiles
revealed for the first time in the session, and over 158 recorded transcripts it produced **zero**
lines for a city or a camp - while 70 of those sessions contained moves that resolved. So a scout
could walk up to a foreign capital and the agent's next message said nothing about it. The other half
is the strategy trigger: nothing in the turn result reacted to a city becoming visible
(`enemy_cities_seen` is computed and no rule reads it), and `tactics/07` - the file that answers a
city - has never reached an advisor brief.

These tests pin the two fixes: every resolving move reports what is in sight, and the first turn a
foreign city is visible it is named with the two calls that answer it.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import narrate as nr  # noqa: E402


def meta(**kw):
    base = {
        "terrain": "TERRAIN_GRASS",
        "feature": None,
        "resource": None,
        "resource_class": None,
        "hills": False,
        "camp": False,
        "units": None,
        "city": None,
        "city_owner": None,
        "visible": True,
    }
    base.update(kw)
    return base


class TestTheSightBlock:
    def test_a_foreign_city_in_sight_names_itself_and_the_next_two_calls(self):
        text = nr.narrate_sight(
            [(58, 42, meta(city="St Petersburg", city_owner="Russia"))], (57, 41)
        )
        assert "IN SIGHT from (57,41)" in text
        assert "**[City: St Petersburg]** - Russia" in text
        assert "get_target_report(58,42)" in text
        assert "prompts/tactics/07-pre-war-analysis.md" in text
        assert "Gate 0" in text

    def test_a_camp_carries_its_own_doctrine(self):
        text = nr.narrate_sight([(60, 29, meta(camp=True))], (59, 28))
        assert "**[Barbarian Camp!]**" in text
        assert "CAMP/GUARD/FORCE/GROUND/WORTH/HOLD/CONVERT/GO" in text
        assert "walks onto the tile" in text

    def test_enemy_units_are_listed(self):
        text = nr.narrate_sight([(55, 40, meta(units=["Russia UNIT_ARCHER"]))], (54, 40))
        assert "**[Russia UNIT_ARCHER]**" in text

    def test_a_city_seen_before_but_not_visible_now_is_not_reported(self):
        """The scan returns every *revealed* tile, so "in sight" has to be asked for explicitly."""
        text = nr.narrate_sight(
            [(54, 39, meta(city="Moscow", city_owner="Russia", visible=False))], (57, 41)
        )
        assert text == ""

    def test_a_scan_with_nothing_on_it_adds_nothing(self):
        assert nr.narrate_sight([(1, 1, meta()), (2, 2, meta(hills=True))], (1, 1)) == ""

    def test_nothing_scanned_is_not_a_crash(self):
        assert nr.narrate_sight([], (1, 1)) == ""


class TestTheScanCarriesWhatItNeeds:
    def test_the_query_reports_the_owner_and_whether_the_tile_is_visible(self):
        q = lq.build_post_move_visibility_query(58, 42)
        assert "cityOwner" in q and "PlayerConfigurations[cOwner]" in q
        assert 'vis:IsVisible(plot:GetX(), plot:GetY()) and "1" or "0"' in q
        tile_print = next(line for line in q.splitlines() if line.strip().startswith("print(\"TILE|"))
        assert "cityName" in tile_print and "cityOwner" in tile_print and "visible" in tile_print

    def test_the_parser_reads_the_new_fields(self):
        tiles = lq.parse_post_move_visibility(
            [
                "TILE|58,42|TERRAIN_TUNDRA_HILLS|none|none|1|0|Russia UNIT_ARCHER|St Petersburg|Russia|1",
                "TILE|54,39|TERRAIN_GRASS|none|none|0|0|none|Moscow|Russia|0",
            ]
        )
        assert tiles[0][2]["city"] == "St Petersburg"
        assert tiles[0][2]["city_owner"] == "Russia"
        assert tiles[0][2]["visible"] is True
        assert tiles[1][2]["visible"] is False

    def test_a_server_without_the_new_fields_reads_as_before(self):
        tiles = lq.parse_post_move_visibility(
            ["TILE|58,42|TERRAIN_GRASS|none|none|0|0|none|none"]
        )
        assert tiles[0][2]["city_owner"] is None
        assert tiles[0][2]["visible"] is True, "an old row was treated as visible, and still is"


class TestTheMoveCarriesTheSight:
    """One recorded move: the reply names the tiles, then what is on them."""

    def _state(self, tiles: list[str]):
        from civ_mcp.game_state import GameState

        class FakeConn:
            async def execute_write(self, lua, timeout=5.0):
                return ["OK:MOVING_TO|58,42|from:54,40", "---END---"]

            async def execute_read(self, lua, timeout=5.0):
                if "POS" in lua:
                    return ["POS|57|41", "---END---"]
                return tiles

        class FakeSpatial:
            _revealed_seeded = True

            def __init__(self):
                self.revealed = {(57, 41)}

            def mark_revealed(self, tiles):
                new = set(tiles) - self.revealed
                self.revealed |= set(tiles)
                return new

            async def record_discovery(self, *a, **kw):
                return None

        gs = GameState.__new__(GameState)
        gs.conn = FakeConn()
        gs.spatial = FakeSpatial()
        return gs

    def test_a_city_next_to_the_landing_tile_is_reported_with_its_next_calls(self):
        gs = self._state(
            ["TILE|58,42|TERRAIN_TUNDRA_HILLS|none|none|1|0|none|St Petersburg|Russia|1"]
        )
        result = asyncio.run(gs.move_unit(42, 58, 42))
        assert result.startswith("MOVING_TO|58,42") and "now_at:57,41" in result
        assert "IN SIGHT from (57,41)" in result
        assert "get_target_report(58,42)" in result
        assert "prompts/tactics/07-pre-war-analysis.md" in result

    def test_a_move_that_sees_nothing_adds_no_noise(self):
        gs = self._state(["TILE|58,42|TERRAIN_GRASS|none|none|0|0|none|none|none|1"])
        result = asyncio.run(gs.move_unit(42, 58, 42))
        assert "IN SIGHT" not in result

    def test_the_sight_block_does_not_depend_on_the_tile_being_new(self):
        """The old narration was gated on first-reveal-in-session; the city block is not."""
        gs = self._state(
            ["TILE|58,42|TERRAIN_GRASS|none|none|0|0|none|St Petersburg|Russia|1"]
        )
        gs.spatial.revealed = {(58, 42), (57, 41)}  # already known: nothing is "new"
        result = asyncio.run(gs.move_unit(42, 58, 42))
        assert "Revealed" not in result
        assert "**[City: St Petersburg]**" in result


class TestTheNewTargetEvent:
    def _gs(self, cities):
        class Fake:
            _known_foreign_cities = None

            async def visible_foreign_cities(self_inner):
                return cities

        return Fake()

    def city(self, name="St Petersburg", x=58, y=42, owner="Russia", at_war=False, pop=8):
        return lq.CitySighting(
            player_id=1, owner_name=owner, name=name, x=x, y=y, pop=pop, at_war=at_war
        )

    def test_the_first_scan_of_a_process_only_seeds(self):
        gs = self._gs([self.city()])
        assert asyncio.run(et._new_target_event(gs, 100)) is None
        assert gs._known_foreign_cities == {"Russia:St Petersburg@58,42"}

    def test_a_new_city_is_reported_once_with_the_two_calls(self):
        gs = self._gs([self.city()])
        asyncio.run(et._new_target_event(gs, 100))
        gs.visible_foreign_cities = lambda: self._cities([self.city(), self.city("Moscow", 54, 39, pop=3)])
        text = asyncio.run(et._new_target_event(gs, 101))
        assert text is not None
        assert "NEW TARGET (T101)" in text
        assert "**Moscow** (Russia, pop 3, at peace)" in text
        assert "get_target_report(54,39)" in text
        assert "prompts/tactics/07-pre-war-analysis.md" in text
        assert "Gate 0" in text
        assert "St Petersburg" not in text

    def test_a_war_city_says_so(self):
        gs = self._gs([])
        asyncio.run(et._new_target_event(gs, 100))
        gs.visible_foreign_cities = lambda: self._cities([self.city(at_war=True, pop=12)])
        text = asyncio.run(et._new_target_event(gs, 101))
        assert "AT WAR" in text

    def test_no_change_is_not_an_event(self):
        gs = self._gs([self.city()])
        asyncio.run(et._new_target_event(gs, 100))
        assert asyncio.run(et._new_target_event(gs, 101)) is None

    def test_a_lost_city_does_not_re_report_when_it_comes_back(self):
        gs = self._gs([self.city()])
        asyncio.run(et._new_target_event(gs, 100))
        gs.visible_foreign_cities = lambda: self._cities([])
        assert asyncio.run(et._new_target_event(gs, 101)) is None
        gs.visible_foreign_cities = lambda: self._cities([self.city()])
        assert asyncio.run(et._new_target_event(gs, 102)) is None, "it was known all along"

    @staticmethod
    async def _cities(cities):
        return cities

    def test_the_scan_reads_every_visible_foreign_city(self):
        q = lq.build_visible_foreign_cities_query()
        assert "FCITY|" in q
        assert "pVis:IsVisible(cx, cy)" in q
        assert "IsOriginalCapital" in q
        for write in ("RequestOperation", "SetProduction", "end_turn"):
            assert write not in q

    def test_the_parser_reads_the_rows(self):
        cities = lq.parse_visible_foreign_cities_response(
            [
                "FCITY|1|Russia|St Petersburg|58,42|pop:8|capital:1|atwar:0",
                "junk",
            ]
        )
        assert len(cities) == 1
        assert cities[0].name == "St Petersburg" and cities[0].capital and not cities[0].at_war
        assert cities[0].key == "Russia:St Petersburg@58,42"
