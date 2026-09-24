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
# Measured live at T121 2026-09-25: 50/100, +15/turn, turns-to-conversion 4, and the outcome the
# game reports for it is GAINING_LOYALTY - so the 4 is "full in four turns", not "revolts in
# four". At exactly 50 the block stays silent (the line is "below 50 or losing"); the pool one
# point lower is the case that matters, so that is what this row carries.
MOSCOW_RECOVERING = (
    "CITY_LOYALTY|589830|莫斯科|54,40|pop:2|loyalty:40.0|max:100.0|per_turn:15.00|flip:4"
    "|governor:|garrison:1|改善忠诚度的方法|outcome:GAINING_LOYALTY|transfer:-1|transfer_name:"
)
# The same shape while the pool is actually draining, with the next owner the game names for a
# loyalty loss (probed live: GetPotentialTransferPlayer() -> 62 / 自由城市).
MOSCOW_REVOLTING = (
    "CITY_LOYALTY|589830|莫斯科|54,40|pop:2|loyalty:31.0|max:100.0|per_turn:-7.75|flip:4"
    "|governor:|garrison:0|改善忠诚度的方法|outcome:LOSING_LOYALTY|transfer:62|transfer_name:自由城市"
)


class TestTheScan:
    def test_the_query_uses_the_apis_the_game_ui_uses(self):
        lua = lq.build_loyalty_check_query()
        assert "GetCulturalIdentity" in lua
        assert "GetLoyaltyPerTurn" in lua
        assert "GetTurnsToConversion" in lua
        assert "GetGovernorList" in lua and "GetAssignedCity" in lua
        assert "GetLoyaltyAdvice" in lua

    def test_it_asks_which_way_loyalty_is_going_not_only_how_far(self):
        # GetTurnsToConversion() alone is ambiguous: it is a revolt countdown while a city is
        # losing and a count of turns to a full pool while it is gaining. The game's own banner
        # reads the two together (CityBannerManager.lua:2355-2358: warn when
        # `LOSING_LOYALTY and nTurns < 20`), and so must we.
        lua = lq.build_loyalty_check_query()
        assert "GetConversionOutcome" in lua
        assert "IdentityConversionOutcome" in lua, "name the outcome from the game's own enum"
        assert "GetPotentialTransferPlayer" in lua, "say who takes it, while it is draining"
        assert "|outcome:" in lua and "|transfer_name:" in lua

    def test_the_advice_string_cannot_break_the_protocol_line(self):
        # A free-text advice string with a newline in it would split one city into two lines, so
        # TAB/LF/CR are replaced. `%c` cannot be used for it: it is not locale-neutral. The C
        # locale and CP1252 both count 0x81 0x8D 0x8F 0x90 0x9D as control codes, and those byte
        # values occur inside CJK UTF-8 sequences - measured live 2026-09-25, `gsub("%c", " ")`
        # removed 20 of the 366 high bytes from a 540-byte Chinese advice string and the client
        # then decoded the mangled result as U+FFFD ("幸� 感" for "幸福感").
        lua = lq.build_loyalty_check_query()
        assert 'gsub("%c"' not in lua, "%c eats high bytes out of CJK text"
        assert "string.char(9) .. string.char(10) .. string.char(13)" in lua
        assert 'gsub(breaks, " ")' in lua

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

    def test_a_line_without_an_outcome_still_reads_the_pressure_sign(self):
        # Older rows, and any producer that has not been rebuilt, carry no outcome field: fall
        # back to the sign of the pressure rather than calling the city healthy.
        moscow = lq.parse_loyalty_response([MOSCOW])[0]
        assert moscow.conversion_outcome == ""
        assert moscow.losing and moscow.falling and moscow.turns_to_revolt == 4

    def test_the_trailing_fields_are_read_by_prefix(self):
        moscow = lq.parse_loyalty_response([MOSCOW_REVOLTING])[0]
        assert moscow.conversion_outcome == "LOSING_LOYALTY"
        assert moscow.transfer_to == 62 and moscow.transfer_name == "自由城市"
        assert moscow.advice == "改善忠诚度的方法", "the advice is still the field before them"

    def test_a_short_line_is_skipped(self):
        assert lq.parse_loyalty_response(["CITY_LOYALTY|1|X", "SENTINEL", ""]) == []

    def test_state_flags(self):
        moscow, beijing = lq.parse_loyalty_response([MOSCOW, BEIJING])
        assert moscow.low and moscow.falling and moscow.unsupported
        assert not beijing.low and not beijing.falling and not beijing.unsupported

    def test_the_game_word_beats_the_pressure_sign(self):
        # Live T121 Moscow: +15/turn *and* 4 turns to conversion, with the game saying GAINING.
        recovering = lq.parse_loyalty_response([MOSCOW_RECOVERING])[0]
        assert recovering.loyalty_per_turn > 0
        assert not recovering.losing and not recovering.falling
        assert recovering.turns_to_flip == 4, "the raw figure is kept"
        assert recovering.turns_to_revolt == 0, "but it is not a revolt countdown"

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

    def test_a_recovering_city_never_sets_the_revolt_countdown(self):
        # Live T121 Moscow: 40/100 and 4 turns to conversion, but GAINING_LOYALTY. Called a
        # revolt, this metric would have put a false alarm in the turn result for a city that
        # was four turns from a full pool.
        rows = lq.parse_loyalty_response([MOSCOW_RECOVERING])
        metrics = et._loyalty_metrics(rows)
        assert metrics["nearest_loyalty_flip"] == 0
        assert metrics["cities_falling_loyalty"] == 0
        assert metrics["cities_low_loyalty"] == 1
        assert metrics["lowest_loyalty"] == 40

    def test_the_revolting_city_sets_it(self):
        metrics = et._loyalty_metrics(lq.parse_loyalty_response([MOSCOW_REVOLTING]))
        assert metrics["nearest_loyalty_flip"] == 4
        assert metrics["cities_falling_loyalty"] == 1
        assert metrics["low_loyalty_without_governor"] == 1


class TestTheWarning:
    def test_it_names_the_city_the_numbers_and_the_game_advice(self):
        text = et._loyalty_event(lq.parse_loyalty_response([MOSCOW]), 112) or ""
        assert "LOYALTY WARNING" in text
        assert "莫斯科" in text and "(54,40)" in text
        assert "losing 3.5/turn" in text and "revolts in 4" in text
        assert "governor: none, garrison: 0" in text
        assert 'Game advice: "Assign a Governor to this city."' in text
        assert "Free City" in text, "the cost of ignoring it has to be in the warning"

    def test_the_countdown_says_who_takes_the_city(self):
        text = et._loyalty_event(lq.parse_loyalty_response([MOSCOW_REVOLTING]), 121) or ""
        assert "losing 7.8/turn, revolts in 4 -> 自由城市" in text
        assert "the first revolt is 4 turn(s) away" in text

    def test_a_recovering_city_below_fifty_is_not_called_a_revolt(self):
        # The failure mode this fixes: 40/100 and +15/turn, four turns from a full pool, reported
        # as "flips in 4" with "the first revolt is 4 turn(s) away" in the header.
        text = et._loyalty_event(lq.parse_loyalty_response([MOSCOW_RECOVERING]), 121) or ""
        assert "LOYALTY WARNING" in text, "it is still below 50, so still worth naming"
        assert "gaining 15.0/turn, full in 4" in text
        assert ", revolts in" not in text, "no revolt countdown for a city that is recovering"
        assert "flips" not in text and "the first revolt" not in text

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
