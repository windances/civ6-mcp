"""Keyless MCP launch and tool-discovery qualification.

This test does not require a running Civ VI game because the adapter connects to
FireTuner lazily when a gameplay tool is called.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time


# The server offers 77 tools; CIV_MCP_DISABLE_LUA=1 hides run_lua, leaving 76.
# Keep this in step with baseline/manifest.json's expectedMcpTools, which counts the
# full set - the two numbers differ by exactly that one hidden tool.
EXPECTED_TOOLS_AFTER_LUA_DISABLE = 76
REQUIRED_TOOLS = {
    "get_game_overview",
    "get_units",
    "get_cities",
    "unit_action",
    "set_city_production",
    "end_turn",
}


def _pump(stream, sink: queue.Queue) -> None:
    """Read stdout lines on a thread.

    select() cannot poll a pipe on Windows (WinError 10093), so blocking reads
    on a daemon thread are used instead.
    """
    try:
        for line in stream:
            sink.put(line)
    finally:
        sink.put(None)


def _request(
    process: subprocess.Popen[str],
    lines: queue.Queue,
    request_id: int,
    method: str,
    params: dict | None = None,
) -> dict:
    assert process.stdin is not None
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()

    deadline = time.monotonic() + 15
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"timed out waiting for {method}")
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty:
            raise TimeoutError(f"timed out waiting for {method}") from None
        if line is None:
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
    # The adapter speaks JSON-RPC, which is UTF-8 by definition. Without this the
    # child inherits a non-UTF-8 locale (e.g. cp936) on Windows.
    child_env["PYTHONUTF8"] = "1"

    process = subprocess.Popen(
        [sys.executable, "-m", "civ_mcp"],
        env=child_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        # Decode explicitly: text mode would otherwise use the locale codec
        # (cp936 here) and die on the first non-ASCII byte in a tool description.
        encoding="utf-8",
        errors="replace",
    )
    try:
        assert process.stdout is not None
        lines: queue.Queue = queue.Queue()
        threading.Thread(
            target=_pump, args=(process.stdout, lines), daemon=True
        ).start()
        _request(
            process,
            lines,
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
        response = _request(process, lines, 2, "tools/list", {})
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
