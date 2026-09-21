"""Loyalty: the city you already took, leaving again with no enemy involved.

Live T105-T121 (hand-played, from the game's own logs): Moscow was captured at T112 with pop 3,
no governor and no garrison; `Player_Stats.csv` shows a Free City in its place from T116; it was
retaken at T121. Nine of the campaign's 64 attacks and four turns went into taking back a city
that was already ours, and nothing in the turn result mentioned loyalty once.

The APIs here are the ones the game's own UI uses (`DLC/Expansion2/UI/CityPanelCulture.lua`,
`CityBannerManager.lua`): `City:GetCulturalIdentity()` for the pool, pressure and
turns-to-conversion, `Player:GetGovernors():GetGovernorList()` with `Governor:GetAssignedCity()`
for who governs what, and `City:GetLoyaltyAdvice()` for the game's own recommendation.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import lua as lq  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

MOSCOW = (
    "CITY_LOYALTY|65536|莫斯科|54,40|pop:3|loyalty:32.5|max:100.0|per_turn:-3.50|flip:4"
    "|governor:|garrison:0|Assign a Governor to this city."
)
BEIJING = (
    "CITY_LOYALTY|65537|北京|52,29|pop:12|loyalty:100.0|max:100.0|per_turn:2.00|flip:0"
    "|governor:GOVERNOR_THE_EDUCATOR|garrison:2|"
)


class TestTheScan:
    def test_the_query_uses_the_apis_the_game_ui_uses(self):
        lua = lq.build_loyalty_check_query()
        assert "GetCulturalIdentity" in lua
        assert "GetLoyaltyPerTurn" in lua
        assert "GetTurnsToConversion" in lua
        assert "GetGovernorList" in lua and "GetAssignedCity" in lua
        assert "GetLoyaltyAdvice" in lua

    def test_the_advice_string_cannot_break_the_protocol_line(self):
        # A free-text advice string with a newline in it would split one city into two lines, and
        # the escaped "[\\r\\n]" form is a character set of backslash, r and n - it eats letters
        # out of the city's own advice. `%c` is every control character.
        lua = lq.build_loyalty_check_query()
        assert 'gsub("%c", " ")' in lua
        assert 'gsub("[\\' not in lua, "no escaped character-set pattern in the Lua"

    def test_it_parses_the_city_line(self):
        rows = lq.parse_loyalty_response([MOSCOW, BEIJING])
        assert [r.city_name for r in rows] == ["莫斯科", "北京"]
        moscow = rows[0]
        assert (moscow.x, moscow.y, moscow.population) == (54, 40, 3)
        assert moscow.loyalty == 32.5 and moscow.loyalty_max == 100.0
        assert moscow.loyalty_per_turn == -3.5 and moscow.turns_to_flip == 4
        assert moscow.governor == "" and moscow.garrison == 0
        assert "Governor" in moscow.advice
        assert rows[1].governor == "GOVERNOR_THE_EDUCATOR" and rows[1].garrison == 2

    def test_a_short_line_is_skipped(self):
        assert lq.parse_loyalty_response(["CITY_LOYALTY|1|X", "SENTINEL", ""]) == []

    def test_state_flags(self):
        moscow, beijing = lq.parse_loyalty_response([MOSCOW, BEIJING])
        assert moscow.low and moscow.falling and moscow.unsupported
        assert not beijing.low and not beijing.falling and not beijing.unsupported

    def test_a_garrison_alone_still_counts_as_supported(self):
        guarded = lq.parse_loyalty_response([MOSCOW.replace("garrison:0", "garrison:1")])[0]
        assert guarded.low and not guarded.unsupported

    def test_it_runs_in_the_ingame_context(self):
        calls: list[str] = []

        class FakeConn:
            async def execute_write(self, lua, timeout=5.0):
                calls.append("write")
                return [MOSCOW]

            async def execute_read(self, lua, timeout=5.0):
                calls.append("read")
                return [MOSCOW]

        gs = GameState.__new__(GameState)
        gs.conn = FakeConn()
        rows = asyncio.run(gs.city_loyalty())
        assert calls == ["write"], "the loyalty and governor APIs are the UI's, not GameCore's"
        assert rows and rows[0].city_name == "莫斯科"

    def test_a_failed_scan_returns_nothing(self):
        class Broken:
            async def execute_write(self, lua, timeout=5.0):
                raise RuntimeError("tuner busy")

        gs = GameState.__new__(GameState)
        gs.conn = Broken()
        assert asyncio.run(gs.city_loyalty()) == []


class TestTheMetric:
    def test_a_low_city_with_no_governor_and_no_garrison_is_counted(self):
        rows = lq.parse_loyalty_response([MOSCOW])
        metrics = et._loyalty_metrics(rows)
        assert metrics["cities_low_loyalty"] == 1
        assert metrics["low_loyalty_without_governor"] == 1
        assert metrics["cities_falling_loyalty"] == 1
        assert metrics["lowest_loyalty"] == 32
        assert metrics["nearest_loyalty_flip"] == 4

    def test_a_governor_takes_the_city_out_of_the_count(self):
        rows = lq.parse_loyalty_response([MOSCOW.replace("|governor:|", "|governor:GOVERNOR_THE_DEFENDER|")])
        metrics = et._loyalty_metrics(rows)
        assert metrics["cities_low_loyalty"] == 1
        assert metrics["low_loyalty_without_governor"] == 0

    def test_healthy_cities_are_neutral(self):
        metrics = et._loyalty_metrics(lq.parse_loyalty_response([BEIJING]))
        assert metrics == {
            "cities_low_loyalty": 0,
            "lowest_loyalty": 100,
            "low_loyalty_without_governor": 0,
            "cities_falling_loyalty": 0,
            "nearest_loyalty_flip": 0,
        }

    def test_nothing_at_all_is_neutral(self):
        assert et._loyalty_metrics([])["lowest_loyalty"] == 100

    def test_a_falling_city_above_fifty_is_still_reported(self):
        sliding = BEIJING.replace("loyalty:100.0", "loyalty:70.0").replace("per_turn:2.00", "per_turn:-5.00")
        metrics = et._loyalty_metrics(lq.parse_loyalty_response([sliding]))
        assert metrics["cities_low_loyalty"] == 0
        assert metrics["cities_falling_loyalty"] == 1


class TestTheWarning:
    def test_it_names_the_city_the_numbers_and_the_game_advice(self):
        text = et._loyalty_event(lq.parse_loyalty_response([MOSCOW]), 112) or ""
        assert "LOYALTY WARNING" in text
        assert "莫斯科" in text and "(54,40)" in text
        assert "-3.5/turn" in text and "flips in 4" in text
        assert "governor: none, garrison: 0" in text
        assert 'Game advice: "Assign a Governor to this city."' in text
        assert "Free City" in text, "the cost of ignoring it has to be in the warning"

    def test_a_falling_city_above_the_line_is_reported_without_the_revolt_lecture(self):
        sliding = BEIJING.replace("loyalty:100.0", "loyalty:70.0").replace("per_turn:2.00", "per_turn:-5.00")
        text = et._loyalty_event(lq.parse_loyalty_response([sliding]), 112) or ""
        assert "LOYALTY WARNING" in text
        assert "北京" in text
        assert "Free City" not in text

    def test_healthy_cities_say_nothing(self):
        assert et._loyalty_event(lq.parse_loyalty_response([BEIJING]), 112) is None
        assert et._loyalty_event([], 112) is None


class TestTheRule:
    FILE = pathlib.Path("prompts/checks/turn-checks.md")

    def context(self, **metrics):
        base = {
            "wonders": 1, "districts": 30, "pop": 30, "improvements": 90, "cities": 5,
            "gold_per_turn": 30, "attacks_this_turn": 0, "unused_attacks": 0,
            "capture_ready": 0, "downed_enemy_cities": 0, "enemy_city_hp_min": 999,
            "strongest_enemy_melee_cs": 0, "our_best_melee_cs": 0,
            "melee_upgrades_available": 0, "min_melee_upgrade_cost": 0,
            "siege_upgrades_available": 0, "min_siege_upgrade_cost": 0,
            "gold": 0, "at_war": 0,
            "cities_low_loyalty": 0, "lowest_loyalty": 100,
            "low_loyalty_without_governor": 0, "cities_falling_loyalty": 0,
            "nearest_loyalty_flip": 0,
        }
        base.update(metrics)
        return turn_checks.CheckContext(turn=112, units={}, metrics=base, researched=frozenset())

    def failing(self, **metrics) -> set[str]:
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), self.context(**metrics))
        return run.failing_ids

    def test_a_low_city_with_nothing_holding_it_fails(self):
        ids = self.failing(
            cities_low_loyalty=1, low_loyalty_without_governor=1, lowest_loyalty=32,
            nearest_loyalty_flip=4,
        )
        assert "hold-what-you-take" in ids

    def test_a_governor_clears_it(self):
        ids = self.failing(
            cities_low_loyalty=1, low_loyalty_without_governor=0, lowest_loyalty=32
        )
        assert "hold-what-you-take" not in ids

    def test_healthy_cities_are_not_this_rules_business(self):
        assert "hold-what-you-take" not in self.failing()

    def test_a_historical_row_reads_as_neutral(self):
        row = {
            "turn": 112, "is_agent": True, "unit_composition": {"SPEARMAN": 1},
            "pop": 30, "districts": 30, "wonders": 1, "cities": 5, "improvements": 90,
            "gold_per_turn": 30, "gold": 400,
        }
        run = turn_checks.run_checks(self.FILE.read_text(encoding="utf-8"), et._context_from_row(row))
        assert "hold-what-you-take" not in run.failing_ids
        assert not [c for c, reason in run.failures if "un-evaluable" in reason]
