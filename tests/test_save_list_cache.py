"""`load_save` must be able to load the index a listing gave it.

Measured on the A5 handover, 2026-09-30: `list_saves()` returned the **filesystem** scan (capped at 25,
newest first) and the shared start save was absent from it until its mtime was touched; once listed it
was filesystem index **1**, and `load_save(1)` answered `Error: No save list cached. Call list_saves()
first.` - because `list_saves` returns the filesystem scan early and never runs the Lua query that
populates `ExposedMembers.MCPSaveList`, which is the only thing `load_save` reads. Driving that query by
hand listed the same save at Lua index **12**, and `load_save(12)` loaded it.

So the two functions do not share an order *and* the cache is usually empty. `load_save` now populates
the cache when it is missing instead of refusing.
"""

from __future__ import annotations

import asyncio
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import game_lifecycle as gl  # noqa: E402
from civ_mcp.lua._helpers import SENTINEL  # noqa: E402

LISTING = [
    "COUNT|2",
    "SAVE|1|0_MCP_0071.Civ6Save",
    "SAVE|12|ATTEMPT-A1-T1-settled.Civ6Save",
    SENTINEL,
]


class FakeConn:
    """Answers the four Lua shapes the load path sends, and records them."""

    def __init__(self, cached: bool, count: int = 12) -> None:
        self.cached = cached
        self.count = count
        self.sent: list[str] = []

    async def execute_write(self, lua_code: str, timeout: float = 5.0) -> list[str]:
        self.sent.append(lua_code)
        if "MCPSaveQueryDone" in lua_code:
            return LISTING
        if "QuerySaveGameList" in lua_code:
            return ["QUERY_SENT", SENTINEL]
        if "MCPSaveList then print" in lua_code:
            return [("CACHED" if self.cached else "EMPTY"), SENTINEL]
        if "Network.LoadGame" in lua_code:
            match = re.search(r"local idx = (\d+)", lua_code)
            index = int(match.group(1)) if match else 1
            if index > self.count:
                return [f"ERR:INDEX_OUT_OF_RANGE|{self.count}", SENTINEL]
            return ["LOADING|ATTEMPT-A1-T1-settled.Civ6Save", SENTINEL]
        return [SENTINEL]


def _drove_the_lua_query(conn: FakeConn) -> bool:
    return any("QuerySaveGameList" in lua for lua in conn.sent)


def test_load_save_populates_the_cache_it_needs():
    conn = FakeConn(cached=False)
    result = asyncio.run(gl.load_save(conn, 12))
    assert _drove_the_lua_query(conn), (
        "the cache `load_save` reads is only filled by the Lua query, and `list_saves` never runs it - "
        "so `load_save` has to fill it rather than refuse with 'No save list cached'"
    )
    assert result.startswith("Loading save: ATTEMPT-A1-T1-settled")


def test_load_save_does_not_requery_a_populated_cache():
    conn = FakeConn(cached=True)
    result = asyncio.run(gl.load_save(conn, 12))
    assert not _drove_the_lua_query(conn)
    assert result.startswith("Loading save: ATTEMPT-A1-T1-settled")


def test_an_index_out_of_range_still_reports_the_count():
    conn = FakeConn(cached=True, count=2)
    result = asyncio.run(gl.load_save(conn, 99))
    assert "out of range" in result and "1-2" in result


def test_the_cached_check_survives_a_dead_connection():
    class Dead:
        async def execute_write(self, lua_code: str, timeout: float = 5.0) -> list[str]:
            raise RuntimeError("no connection")

    assert asyncio.run(gl._save_list_cached(Dead())) is False, (
        "a probe that raises must read as 'not cached', not as an exception out of the load path"
    )
