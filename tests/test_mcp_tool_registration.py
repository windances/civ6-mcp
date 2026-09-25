"""Every tool-shaped function in the MCP server is registered, and nothing else is.

`@mcp.tool` is a bare decorator on the next `def`, which makes it easy to lose and easy to give to
the wrong function. Both happened in `cc1c4a1` (2026-09-21), when `_clamp_diary_to_turn` was inserted
between the decorator and `get_diary`:

    @mcp.tool(annotations={"readOnlyHint": True})   # meant for get_diary
    def _clamp_diary_to_turn(...): ...              # a private helper that returns a tuple
    async def get_diary(...): ...                   # the tool the skill's Phase 1 calls first

The decorator stayed behind on the helper, so `get_diary` was not in the tool list at all — the tool
count did not move, which is why the count gates in `baseline/manifest.json` (78) and
`scripts/qualify-mcp.py` (77 with `run_lua` hidden) stayed green — and every session since reported
"`get_diary` does not exist on this MCP server" in its `tooling` line while re-deriving its whole
baseline from the game instead of reading its own memory. Measured live at T94-T96 of the current
playthrough; restored 2026-09-26.

The rules below are deliberately narrow, because the server has exactly two kinds of top-level
function: a tool (`async def`, public, `@mcp.tool`) and a helper (private, or the `lifespan`).
"""

from __future__ import annotations

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVER = ROOT / "src" / "civ_mcp" / "server.py"

# The ASGI lifespan is public and async but is not a tool; it is decorated with
# `@asynccontextmanager`. Everything else public and async is offered to the client.
NOT_A_TOOL = {"lifespan"}


def functions() -> list[ast.AST]:
    tree = ast.parse(SERVER.read_text(encoding="utf-8-sig"))
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def is_tool(node: ast.AST) -> bool:
    return any("mcp.tool" in ast.unparse(dec) for dec in node.decorator_list)  # type: ignore[attr-defined]


class TestToolRegistration:
    def test_every_public_async_function_is_a_registered_tool(self):
        missing = [
            node.name
            for node in functions()
            if isinstance(node, ast.AsyncFunctionDef)
            and not node.name.startswith("_")
            and node.name not in NOT_A_TOOL
            and not is_tool(node)
        ]
        assert not missing, (
            "these public async functions are not exposed to the client - they are missing their "
            f"@mcp.tool decorator, which is how get_diary disappeared in cc1c4a1: {missing}"
        )

    def test_no_private_helper_carries_the_tool_decorator(self):
        stray = [node.name for node in functions() if node.name.startswith("_") and is_tool(node)]
        assert not stray, (
            "these private helpers are registered as tools, which means a decorator meant for the "
            f"tool below them stayed behind: {stray}"
        )

    def test_the_documented_tools_are_registered(self):
        # The tools AGENTS.md and the skill tell a session to call; `get_diary` is the one that was
        # silently absent.
        registered = {node.name for node in functions() if is_tool(node)}
        for name in (
            "get_diary",
            "get_game_status",
            "get_game_overview",
            "get_units",
            "get_cities",
            "unit_action",
            "set_city_production",
            "end_turn",
            "search_knowledge",
        ):
            assert name in registered, f"{name} is documented but not registered"

    def test_the_registered_count_is_the_declared_baseline(self):
        # qualify-static.mjs and qualify-mcp.py both hold this number; a tool that moves in or out
        # without moving them is the failure this pins.
        import json

        manifest = json.loads((ROOT / "baseline" / "manifest.json").read_text(encoding="utf-8-sig"))
        declared = manifest["civ6Mcp"]["expectedMcpTools"]
        registered = sum(1 for node in functions() if is_tool(node))
        assert registered == declared, (
            f"server.py registers {registered} tools but baseline/manifest.json declares {declared}; "
            "update the manifest, scripts/qualify-mcp.py and SETUP-WINDOWS.md together"
        )
