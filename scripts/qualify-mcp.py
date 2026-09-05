"""Keyless MCP launch and tool-discovery qualification.

This test does not require a running Civ VI game because the adapter connects to
FireTuner lazily when a gameplay tool is called.
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import time


EXPECTED_TOOLS_AFTER_LUA_DISABLE = 75
REQUIRED_TOOLS = {
    "get_game_overview",
    "get_units",
    "get_cities",
    "unit_action",
    "set_city_production",
    "end_turn",
}


def _request(
    process: subprocess.Popen[str],
    request_id: int,
    method: str,
    params: dict | None = None,
) -> dict:
    assert process.stdin is not None
    assert process.stdout is not None
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()

    deadline = time.monotonic() + 15
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([process.stdout], [], [], remaining)[0]:
            raise TimeoutError(f"timed out waiting for {method}")
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(f"civ-mcp exited before replying to {method}")
        response = json.loads(line)
        if response.get("id") == request_id:
            if "error" in response:
                raise RuntimeError(f"{method} failed: {response['error']}")
            return response["result"]


def qualify() -> None:
    child_env = dict(os.environ)
    child_env["CIV_MCP_DISABLE_LUA"] = "1"
    child_env["CIV_MCP_DISABLE_WEB_API"] = "1"
    child_env["CIV_MCP_DATA_DIR"] = os.path.join(os.getcwd(), ".civ6-mcp-data")

    process = subprocess.Popen(
        [sys.executable, "-m", "civ_mcp"],
        env=child_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        _request(
            process,
            1,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "civ6-dsh-qualifier", "version": "1"},
            },
        )
        assert process.stdin is not None
        process.stdin.write(
            '{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
        )
        process.stdin.flush()
        response = _request(process, 2, "tools/list", {})
    finally:
        # This is a protocol smoke test, not a live game session. Force a bounded
        # teardown so unavailable FireTuner background probes cannot hang CI.
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

    names = {tool["name"] for tool in response["tools"]}
    failures: list[str] = []
    if len(names) != EXPECTED_TOOLS_AFTER_LUA_DISABLE:
        failures.append(
            f"expected {EXPECTED_TOOLS_AFTER_LUA_DISABLE} tools, discovered {len(names)}"
        )
    if "run_lua" in names:
        failures.append("run_lua remained visible despite CIV_MCP_DISABLE_LUA=1")
    missing = sorted(REQUIRED_TOOLS - names)
    if missing:
        failures.append(f"required tools missing: {', '.join(missing)}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        raise SystemExit(1)

    print("MCP qualification passed:")
    print("- initialized civ-mcp over stdio")
    print(f"- discovered {len(names)} tools")
    print("- run_lua disabled")
    print(f"- required orchestrator tools present: {len(REQUIRED_TOOLS)}")


if __name__ == "__main__":
    qualify()
