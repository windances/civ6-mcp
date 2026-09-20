"""Tests for the turn-regression warning.

The check exists to catch an *accidental* wrong-save load (for example the agent
loading the T1 scenario save). It cannot tell that apart from a *deliberate*
rollback, and on 2026-09-20 it told the agent to reload the newer save twice,
against the human's intent both times. It now reports both readings and asks,
rather than instructing, and it warns once instead of every turn.
"""

import pytest

from civ_mcp.end_turn import _turn_regression_allowed, _turn_regression_message


class TestAllowTurnRegressionFlag:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " on "])
    def test_truthy_values_enable_it(self, monkeypatch, value):
        monkeypatch.setenv("CIV_MCP_ALLOW_TURN_REGRESSION", value)
        assert _turn_regression_allowed() is True

    @pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "maybe"])
    def test_other_values_leave_the_check_on(self, monkeypatch, value):
        monkeypatch.setenv("CIV_MCP_ALLOW_TURN_REGRESSION", value)
        assert _turn_regression_allowed() is False

    def test_unset_means_off(self, monkeypatch):
        monkeypatch.delenv("CIV_MCP_ALLOW_TURN_REGRESSION", raising=False)
        assert _turn_regression_allowed() is False


class TestMessageIsAdvisory:
    def test_reports_the_regression_with_both_turns(self):
        msg = _turn_regression_message(171, 59, "0_MCP_0171")
        assert "171" in msg and "59" in msg

    def test_states_both_readings(self):
        msg = _turn_regression_message(171, 59, "0_MCP_0171")
        assert "If that was deliberate" in msg
        assert "If it was NOT deliberate" in msg

    def test_does_not_order_a_reload(self):
        msg = _turn_regression_message(171, 59, "0_MCP_0171")
        # The old wording commanded a reload; that is what broke the rollbacks.
        assert not msg.startswith("CRITICAL")
        assert "Do not reload by reflex" in msg

    def test_names_the_newer_save_as_an_option_not_an_instruction(self):
        msg = _turn_regression_message(171, 59, "0_MCP_0171")
        assert "0_MCP_0171" in msg
        # Mentioned as what it is, rather than as the thing to do.
        assert "the newest position is 0_MCP_0171" in msg

    def test_tells_the_agent_to_record_its_conclusion(self):
        assert "your diary" in _turn_regression_message(100, 20, "0_MCP_0100")
