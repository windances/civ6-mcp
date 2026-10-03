"""The session line: which directory, which match, and how old the diary is.

This is the one screen of output that makes a split or a stale diary visible, so it gets tests
rather than trust. The failure it is for (measured 2026-10-03): a session wrote
``turn-checks-state.json`` into ``~/.civ6-mcp`` while the diary for the same match sat in
``.civ6-mcp-data``, last written 40 turns earlier, and nothing anywhere said so.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp import diary as diary_mod  # noqa: E402
from civ_mcp import session_info  # noqa: E402


def row(turn: int, is_agent: bool = True) -> str:
    return json.dumps({"turn": turn, "is_agent": is_agent, "cities": 4, "wonders": 2})


@pytest.fixture
def session(tmp_path, monkeypatch):
    """A data directory of our own, a home that is somewhere else, and a diary we control."""

    def build(rows: list[str] | None, home_state: dict | None = None):
        data = tmp_path / "workspace-data"
        data.mkdir(exist_ok=True)
        home = tmp_path / "home"
        (home / ".civ6-mcp").mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data))
        monkeypatch.setattr(diary_mod, "DIARY_DIR", data)
        monkeypatch.setattr(session_info, "_home", lambda: home)
        if rows is not None:
            (data / diary_mod.diary_path("china", 911679432).name).write_text(
                "\n".join(rows) + "\n", encoding="utf-8"
            )
        if home_state is not None:
            (home / ".civ6-mcp" / "turn-checks-state.json").write_text(
                json.dumps(home_state), encoding="utf-8"
            )
        return data, home

    return build


class TestTheLineItself:
    def test_it_names_the_directory_the_match_and_the_diarys_last_turn(self, session):
        session([row(75), row(76), row(76, is_agent=False)])
        line = session_info.banner("china", 911679432, live_turn=76)[0]
        assert "data_dir=" in line and "workspace-data" in line
        assert "match=china_911679432" in line
        assert "last_agent_turn=76" in line

    def test_a_non_agent_row_does_not_count_as_the_diarys_position(self, session):
        """Other players' rows share the file; the agent's own turn is what a resume quotes."""
        session([row(80, is_agent=False), row(12)])
        line = session_info.banner("china", 911679432)[0]
        assert "last_agent_turn=12" in line

    def test_a_missing_diary_says_absent_rather_than_zero(self, session):
        session(None)
        lines = session_info.banner("china", 911679432, live_turn=116)
        assert "diary=absent" in lines[0]
        assert any("no diary row" in ln for ln in lines)

    def test_no_note_when_the_diary_is_current(self, session):
        session([row(116)])
        lines = session_info.banner("china", 911679432, live_turn=116)
        assert len(lines) == 1, "a diary that is up to date is not worth a second line"


class TestTheStalenessNote:
    def test_it_counts_the_turns_and_names_the_remedy(self, session):
        """The gap is a missed step, not a missing capability: record-turn.py is what writes rows."""
        session([row(76)])
        lines = session_info.banner("china", 911679432, live_turn=116)
        note = next(ln for ln in lines if ln.startswith("NOTE"))
        assert "40 turn(s) behind" in note
        assert "T76" in note and "T116" in note
        assert "record-turn.py" in note

    def test_without_a_live_turn_it_still_reports_the_position(self, session):
        session([row(76)])
        lines = session_info.banner("china", 911679432, live_turn=None)
        assert len(lines) == 1 and "last_agent_turn=76" in lines[0]


class TestTheSplitDirectoryWarning:
    def test_the_other_directory_holding_this_match_is_named(self, session):
        session([row(76)], home_state={"china_911679432": {"dynasty-cycle-wonder": 116}})
        lines = session_info.banner("china", 911679432, live_turn=116)
        warning = next(ln for ln in lines if ln.startswith("WARNING"))
        assert "china_911679432" in warning
        assert ".civ6-mcp" in warning

    def test_another_match_in_the_other_directory_is_not_our_problem(self, session):
        session([row(76)], home_state={"china_-1894041591": {"x": 1}})
        lines = session_info.banner("china", 911679432, live_turn=116)
        assert not any(ln.startswith("WARNING") for ln in lines)

    def test_no_warning_when_the_home_default_is_the_data_directory(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        data = home / ".civ6-mcp"
        data.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("CIV_MCP_DATA_DIR", str(data))
        monkeypatch.setattr(diary_mod, "DIARY_DIR", data)
        monkeypatch.setattr(session_info, "_home", lambda: home)
        (data / "turn-checks-state.json").write_text(
            json.dumps({"china_911679432": {"x": 1}}), encoding="utf-8"
        )
        assert session_info.other_data_dirs() == []
