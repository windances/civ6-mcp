"""The pre-war target read: a foreign city's walls and defence from `get_diplomacy`.

`tactics/07` step 1 wants four numbers before a declaration — garrison, walls, HP pool, ring — and
three of them come from the city line of `get_diplomacy`. The adapter has always read the wall pool
(`ECITY ... |ecWalls|ecDef`, `diplomacy.py`'s Lua) but the parser collapsed it to a boolean and the
renderer printed it as `[walls]`, which made **"no walls" and "not reported" look identical**.

Measured live on the T97–T115 turns of the current playthrough: the session read 阿斯特拉罕 (54,40)
with a scout two tiles away, saw no wall flag anywhere, and recorded `task 006`'s "target city read
in four numbers" clause as *unsatisfiable before a war* — which is why the task expired at T110 with
no declaration. `walls none` / `walls 100` and the `def` figure (the city's strength, including the
garrison bonus that gate 1's fire arithmetic keys on) are what make that clause answerable at peace.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import narrate  # noqa: E402
from civ_mcp.lua import diplomacy as diplo  # noqa: E402

CIV = "CIV|1|俄罗斯|彼得|1|0|FRIENDLY|0|1|1|1|0|0"


def parse(city_line: str):
    lines = [CIV, city_line, "CIVCITIES|1|3", "MILITARY|1|79|317"]
    civs = diplo.parse_diplomacy_response(lines)
    return next(c for c in civs if c.player_id == 1)


class TestTheWallNumberSurvivesParsing:
    def test_a_wall_less_city_keeps_zero_and_its_defence(self):
        civ = parse("ECITY|1|阿斯特拉罕|54,40|3|100|0.0|0|24")
        vc = civ.visible_cities[0]
        assert vc.has_walls is False
        assert vc.wall_max == 0
        assert vc.defense_strength == 24

    def test_a_walled_city_keeps_its_pool(self):
        vc = parse("ECITY|1|莫斯科|54,40|3|100|0.0|100|35").visible_cities[0]
        assert vc.has_walls is True
        assert vc.wall_max == 100


class TestTheTargetReadIsReadable:
    def test_no_walls_renders_as_walls_none_rather_than_silence(self):
        text = narrate.narrate_diplomacy([parse("ECITY|1|阿斯特拉罕|54,40|3|100|0.0|0|24")])
        assert "阿斯特拉罕 pop 3 (54,40) walls none def 24" in text, text

    def test_a_wall_pool_renders_with_its_number(self):
        text = narrate.narrate_diplomacy([parse("ECITY|1|莫斯科|54,40|3|100|0.0|100|35")])
        assert "walls 100 def 35" in text, text

    def test_the_ambiguous_boolean_flag_is_gone(self):
        text = narrate.narrate_diplomacy([parse("ECITY|1|莫斯科|54,40|3|100|0.0|100|35")])
        assert "[walls]" not in text
