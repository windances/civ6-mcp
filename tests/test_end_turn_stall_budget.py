"""The AI-turn stall reports at two minutes instead of burning a ten-minute budget.

Human rule 2026-10-04: a game held in the AI-processing state - the screen reads "other players are
taking their turn, please wait" - for more than two minutes needs a restart, so `end_turn` must say
so at that mark instead of hiding the stall behind a long silence. The decision that came with the
rule was **report early rather than self-restart**: the MCP may not kill and relaunch the game on its
own, because a reload throws away everything the running turn has already done (measured T354, where
the reload reset Korolev's activation, Xi'an's launch and the builder orders) and the restart is the
human's to make, with the session stopped first.

Measured before the change: two stalls at T354 (`22:13:34` and `22:56:21`) each burned the whole poll
budget, and the answer - `HANG:354:0_MCP_0354|... AI turn processing appears stuck.` - arrived minutes
after the game had visibly stopped, with nothing in it telling anyone what to do about it.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import sys
import textwrap

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import end_turn as et  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _execute_end_turn_source() -> str:
    return textwrap.dedent(inspect.getsource(et.execute_end_turn))


def _cadence_table() -> list[float]:
    """The Phase 2 sleep table, read from the function rather than copied beside it."""
    tree = ast.parse(_execute_end_turn_source())
    tables = [
        [node.value for node in loop.iter.elts]
        for loop in ast.walk(tree)
        if isinstance(loop, ast.For) and isinstance(loop.iter, ast.List)
    ]
    assert len(tables) == 1, f"expected one cadence table, found {len(tables)}"
    return tables[0]


class TestTheBudget:
    def test_it_is_two_minutes(self):
        assert et.AI_TURN_STALL_REPORT_S == 120.0

    def test_a_delay_is_trimmed_to_what_is_left(self):
        assert et.next_poll_delay(20.0, 109.0) == pytest.approx(11.0)
        assert et.next_poll_delay(2.0, 118.0) == pytest.approx(2.0)

    def test_the_budget_is_never_overshot(self):
        for waited in (0.0, 4.0, 84.0, 119.5, 120.0):
            for delay in (2.0, 15.0, 30.0, 600.0):
                slept = et.next_poll_delay(delay, waited)
                assert slept >= 0.0
                assert waited + slept <= et.AI_TURN_STALL_REPORT_S + 1e-9

    def test_a_loop_that_is_already_late_does_not_sleep_at_all(self):
        assert et.next_poll_delay(30.0, 600.0) == 0.0

    def test_a_spent_budget_stops_the_loop(self):
        assert et.next_poll_delay(15.0, et.AI_TURN_STALL_REPORT_S) == 0.0
        assert et.next_poll_delay(15.0, et.AI_TURN_STALL_REPORT_S + 80.0) == 0.0

    def test_the_cadence_table_outlasts_the_budget(self):
        """The table is a cadence; the budget is the deadline.

        If the table were shorter than the budget the loop would end early and report a stall the
        game had 30 seconds left to clear - so the table has to reach the budget, and the walk below
        has to land exactly on it.
        """
        source = _execute_end_turn_source()
        assert "cumulative_wait = 4.0" in source, "Phase 1's 4s is not counted in the budget"

        waited = 4.0
        for delay in _cadence_table():
            delay = et.next_poll_delay(delay, waited)
            if delay <= 0:
                break
            waited += delay
        assert waited == pytest.approx(et.AI_TURN_STALL_REPORT_S)

    def test_the_loop_uses_the_helper_rather_than_a_second_copy_of_the_rule(self):
        source = _execute_end_turn_source()
        assert "delay = next_poll_delay(delay, cumulative_wait)" in source


class TestTheReport:
    def test_it_states_the_two_minute_rule(self):
        source = _execute_end_turn_source()
        assert "two-minute limit" in source
        assert "it needs a restart" in source

    def test_it_names_the_way_out(self):
        # Stop the session first, restart the game, come back from the save named in the HANG.
        source = _execute_end_turn_source()
        assert "stop-agent.py" in source
        assert 'load_game_save(\\"' in source

    def test_it_reports_how_long_it_waited(self):
        source = _execute_end_turn_source()
        assert "elapsed = time.monotonic() - stall_started" in source
        assert "Waited {elapsed:.0f}s" in source

    def test_the_clock_starts_before_phase_one(self):
        # The wait the message quotes has to be the wait the caller experienced, so the clock is
        # started where the request is sent, not where the long polling begins.
        source = _execute_end_turn_source()
        assert source.index("stall_started = time.monotonic()") < source.index(
            "for _ in range(8):"
        )


class TestTheMcpDoesNotSelfRestart:
    """`report early rather than self-restart` - the other half of the human's decision."""

    def _enabled(self):
        from civ_mcp.server import _hang_self_restart_enabled

        return _hang_self_restart_enabled()

    def test_the_self_restart_is_off_by_default(self, monkeypatch):
        monkeypatch.delenv("CIV_MCP_HANG_SELF_RESTART", raising=False)
        assert self._enabled() is False

    @pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
    def test_it_can_be_switched_back_on_for_an_unattended_run(self, monkeypatch, value):
        monkeypatch.setenv("CIV_MCP_HANG_SELF_RESTART", value)
        assert self._enabled() is True

    @pytest.mark.parametrize("value", ["", "0", "no", "off", "maybe"])
    def test_anything_else_leaves_it_off(self, monkeypatch, value):
        monkeypatch.setenv("CIV_MCP_HANG_SELF_RESTART", value)
        assert self._enabled() is False

    def test_the_hang_recovery_branch_is_gated_on_it(self):
        source = (ROOT / "src" / "civ_mcp" / "server.py").read_text(encoding="utf-8")
        assert "and _hang_self_restart_enabled()" in source
        assert "and not _hang_self_restart_enabled()" in source
        # The report branch must not reach the kill/relaunch: restart_and_load appears only inside
        # the gated block, which the report branch's condition excludes.
        report_at = source.index("and not _hang_self_restart_enabled()")
        restart_at = source.index("restart_result = await game_launcher.restart_and_load(hang_save)")
        assert report_at < restart_at
