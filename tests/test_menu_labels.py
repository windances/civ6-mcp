"""Tests for localized menu-label matching in the OCR navigation path.

The launcher drives the Civ VI front end by OCR'ing literal button labels.
On this machine the game runs with DisplayLanguage=zh_Hans_CN, so the English
literals never appear — every OCR recovery attempt failed with
"Could not find 'Single Player' on main menu".

Two things make the localized labels work, and both are covered here:

1. A label table joining each logical control to every spelling it can appear
   under (the Chinese strings come from the game's own
   Vanilla_zh_Hans_CN.xml, joined by Tag).
2. Whitespace-insensitive comparison, because the Windows OCR engine returns
   ``单 人 模 式`` with a space between every CJK glyph.
"""

from civ_mcp.game_launcher import (
    _find_text,
    _game_text_language,
    _label_display,
    _menu_labels,
)

# What the Windows OCR engine actually returns for the Chinese main menu.
OCR_MAIN_MENU = [
    ("单 人 模 式", 300, 500, 120, 20),
    ("多 人 模 式", 300, 560, 120, 20),
    ("额 外 内 容", 300, 620, 120, 20),
    ("游 戏 选 项", 300, 680, 120, 20),
]

OCR_LEADER_SCREEN = [
    ("秦 始 皇", 900, 300, 200, 40),
    ("继 续", 700, 1400, 80, 30),
]


class TestMenuLabels:
    def test_logical_key_yields_english_and_chinese(self):
        labels = _menu_labels("single_player")
        assert "Single Player" in labels
        assert "单人模式" in labels

    def test_every_navigated_control_has_a_chinese_label(self):
        for key in ("single_player", "load_game", "continue", "autosaves"):
            assert any(not lbl.isascii() for lbl in _menu_labels(key)), key

    def test_unknown_key_passes_through(self):
        # Callers may hand _menu_labels either a logical key or a literal.
        assert _menu_labels("Some Literal") == ("Some Literal",)
        assert _menu_labels("Autosaves") == ("Autosaves",)

    def test_labels_are_the_games_own_strings(self):
        # Joined from Vanilla_zh_Hans_CN.xml by Tag, not transliterated.
        assert _menu_labels("single_player")[1] == "单人模式"  # LOC_SINGLE_PLAYER
        assert _menu_labels("load_game")[1] == "加载游戏"  # LOC_LOAD_GAME
        assert _menu_labels("autosaves")[1] == "自动保存"  # LOC_AUTOSAVES
        assert _menu_labels("continue")[1] == "继续"  # LOC_CONTINUE

    def test_display_is_readable(self):
        assert _label_display("single_player") == "Single Player | 单人模式"


class TestFindTextLocalized:
    def test_exact_match_ignores_cjk_glyph_spacing(self):
        match = _find_text(OCR_MAIN_MENU, _menu_labels("single_player"), exact=True)
        assert match is not None
        assert match[0] == "单 人 模 式"
        assert match[1:3] == (300, 500)

    def test_continue_matches_on_leader_screen(self):
        match = _find_text(OCR_LEADER_SCREEN, _menu_labels("continue"))
        assert match is not None
        assert match[0] == "继 续"

    def test_continue_prefers_the_button_over_a_paragraph(self):
        # 继续 is an ordinary Chinese word, so the leader-screen intro text can
        # contain it. The button is the bottom-most match, which is why the
        # navigation looks for it with prefer_bottom.
        results = [
            ("请 点 击 继 续 以 开 始", 100, 200, 500, 20),
            ("继 续", 700, 1400, 80, 30),
        ]
        first = _find_text(results, _menu_labels("continue"))
        bottom = _find_text(results, _menu_labels("continue"), prefer_bottom=True)
        assert first is not None and first[0] == "请 点 击 继 续 以 开 始"
        assert bottom is not None and bottom[0] == "继 续"

    def test_main_menu_detection_during_continue_wait(self):
        # The CONTINUE poll aborts when it sees the main menu instead.
        assert _find_text(OCR_LEADER_SCREEN, _menu_labels("single_player")) is None
        assert _find_text(OCR_MAIN_MENU, _menu_labels("single_player")) is not None

    def test_label_list_accepts_an_english_or_chinese_hit(self):
        english_only = [("Single Player", 10, 20, 5, 5)]
        assert _find_text(english_only, _menu_labels("single_player"), exact=True)
        chinese_only = [("单 人 模 式", 10, 20, 5, 5)]
        assert _find_text(chinese_only, _menu_labels("single_player"), exact=True)

    def test_no_match_returns_none(self):
        assert _find_text(OCR_MAIN_MENU, _menu_labels("load_game"), exact=True) is None


class TestFindTextStillEnglishFirst:
    """The English path must behave exactly as it did before localization."""

    def test_exact_match(self):
        results = [("Single Player", 1, 2, 3, 4), ("Multiplayer", 5, 6, 7, 8)]
        match = _find_text(results, "Single Player", exact=True)
        assert match is not None and match[0] == "Single Player"

    def test_exact_is_still_exact(self):
        results = [("Single Player Mode", 1, 2, 3, 4)]
        assert _find_text(results, "Single Player", exact=True) is None

    def test_substring_match_default(self):
        results = [("== Load Game ==", 1, 2, 3, 4)]
        match = _find_text(results, "Load Game")
        assert match is not None and match[0] == "== Load Game =="

    def test_prefer_bottom_picks_lowest(self):
        results = [("Load Game", 1, 10, 3, 4), ("Load Game", 1, 900, 3, 4)]
        match = _find_text(results, "Load Game", exact=True, prefer_bottom=True)
        assert match is not None and match[2] == 900

    def test_target_normalisation_still_applies(self):
        # Underscores in the target match spaces in OCR output (save names).
        results = [("0 MCP 0111", 1, 2, 3, 4)]
        assert _find_text(results, "0_MCP_0111") is not None


class TestGameTextLanguage:
    def test_returns_a_string(self):
        # Best effort: "" when AppOptions.txt is absent, never an exception.
        assert isinstance(_game_text_language(), str)


class TestHangWindowUnfocused:
    """The hang path only retries in place when the window really lost focus."""

    @staticmethod
    def _check(diag):
        from civ_mcp.server import _hang_window_unfocused

        return _hang_window_unfocused(diag)

    def test_backgrounded_window_is_flagged(self):
        assert self._check(
            {"window": {"found": True, "foreground": False, "minimised": False}}
        )

    def test_minimised_window_is_flagged(self):
        assert self._check(
            {"window": {"found": True, "foreground": True, "minimised": True}}
        )

    def test_focused_window_is_not_flagged(self):
        assert not self._check(
            {"window": {"found": True, "foreground": True, "minimised": False}}
        )

    def test_missing_window_is_not_flagged(self):
        assert not self._check({"window": {"found": False}})
        assert not self._check({})
