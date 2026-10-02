"""A session with no diary writer still gets real metrics for its `metric(...)` rules.

The failure this exists for (measured live at T115): `dynasty-cycle-wonder` reported
`No wonder built` on three consecutive turns while Chengdu had two standing - Great Bath and
Etemenanki - and the live snapshot read `wonders=2`. The rule's `metric(wonders)` is fed from the
agent's **diary row**, and a row is written by the MCP server's tool wrapper: `server.py` captures
a snapshot and emits one row per player. A session that drives the adapter directly - the repo
drivers, `scripts/play-turn.py` and its siblings - never passes through that wrapper, so
`_agent_diary_rows` answered with **zero rows**, `metrics` was `{}`, and every `metric(...)` rule
was judged against a missing value. The wonder rule could not be satisfied by any action.

`_live_agent_row` reads the snapshot the wrapper would have written. These tests hold both halves:
that the row it builds is the shape the rules read, and that `_evaluate_checks` reaches for it when
the stored rows are empty.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402
from civ_mcp import turn_checks  # noqa: E402
from civ_mcp.lua import models as m  # noqa: E402


def _player(pid: int, wonders: int, techs: list[str]) -> m.PlayerRow:
    return m.PlayerRow(
        pid=pid,
        civ="China" if pid == 0 else "Maori",
        leader="Qin" if pid == 0 else "Kupe",
        is_agent=pid == 0,
        score=271,
        cities=4,
        pop=34,
        science=41.9,
        culture=16.6,
        gold=127.9,
        gold_per_turn=25.1,
        faith=750.8,
        faith_per_turn=9.0,
        favor=24,
        favor_per_turn=1,
        military=319,
        wonders=wonders,
        districts=14,
        improvements=17,
        techs_completed=len(techs),
        civics_completed=14,
        techs=list(techs),
        civics=["CIVIC_FEUDALISM"],
    )


def _gs(players=None):
    class Snap:
        def __init__(self):
            self.players = players if players is not None else [
                _player(0, 2, ["TECH_GUNPOWDER"]),
                _player(2, 4, ["TECH_STIRRUPS"]),
            ]

    class GS:
        local_player_id = 0

        async def get_diary_snapshot(self):
            return Snap()

    return GS()


def _broken_gs():
    class GS:
        local_player_id = 0

        async def get_diary_snapshot(self):
            raise RuntimeError("tuner busy")

    return GS()


class TestTheLiveRow:
    def test_it_is_the_agents_own_row_with_the_turn_stamped(self):
        row = asyncio.run(et._live_agent_row(_gs(), 115))
        assert row["turn"] == 115
        assert row["is_agent"] is True
        assert row["pid"] == 0
        assert row["wonders"] == 2, "the whole point: the wonder the rule cannot see"

    def test_it_carries_the_tech_name_list_researched_rules_need(self):
        row = asyncio.run(et._live_agent_row(_gs(), 115))
        assert row["techs"] == ["TECH_GUNPOWDER"]
        assert row["civics"] == ["CIVIC_FEUDALISM"]

    def test_it_drops_other_players_rows(self):
        row = asyncio.run(et._live_agent_row(_gs(), 115))
        assert row["pid"] == 0 and row["civ"] == "China"

    def test_no_row_for_our_player_is_none(self):
        assert asyncio.run(et._live_agent_row(_gs([_player(2, 4, [])]), 115)) is None

    def test_a_failed_snapshot_is_none_not_an_exception(self):
        """A missing metric is the old behaviour; inventing one would be worse."""
        assert asyncio.run(et._live_agent_row(_broken_gs(), 115)) is None


CHECKS = """<!-- check
id: probe-wonder
when: turn() >= 1
require: metric(wonders) >= 1
message: No wonder built.
-->
"""


class TestEvaluateChecksUsesIt:
    def _patched(self, monkeypatch, tmp_path, rows, live_row):
        path = tmp_path / "turn-checks.md"
        path.write_text(CHECKS, encoding="utf-8")
        monkeypatch.setattr(turn_checks, "load_checks", lambda: (CHECKS, path))
        monkeypatch.setattr(turn_checks, "load_retired", lambda key: set())

        async def noddy(*_a, **_k):
            return []

        async def no_units(*_a, **_k):
            return {}

        async def no_contact(*_a, **_k):
            return {key: 0 for key in et._CONTACT_METRIC_KEYS}

        async def game_key(*_a, **_k):
            return "china_1"

        async def live(*_a, **_k):
            return live_row

        monkeypatch.setattr(et, "_agent_diary_rows", noddy)
        monkeypatch.setattr(et, "_units_for_checks", no_units)
        monkeypatch.setattr(et, "_contact_metrics", no_contact)
        monkeypatch.setattr(et, "_game_key", game_key)
        monkeypatch.setattr(et, "_live_agent_row", live)

    def test_the_empty_diary_is_paid_for_by_the_live_row(self, monkeypatch, tmp_path):
        live = asdict_row(2)
        self._patched(monkeypatch, tmp_path, [], live)
        run, *_ = asyncio.run(et._evaluate_checks(_gs(), 115, {}, None))
        assert "probe-wonder" in run.passed, "the live row's wonders=2 must satisfy the rule"

    def test_without_the_live_row_the_rule_fails(self, monkeypatch, tmp_path):
        """The old behaviour, pinned: no row at all leaves the metric missing."""
        self._patched(monkeypatch, tmp_path, [], None)
        run, *_ = asyncio.run(et._evaluate_checks(_gs(), 115, {}, None))
        assert "probe-wonder" not in run.passed


def asdict_row(wonders: int) -> dict:
    from dataclasses import asdict

    row = asdict(_player(0, wonders, ["TECH_GUNPOWDER"]))
    row["turn"] = 115
    row["is_agent"] = True
    return row
