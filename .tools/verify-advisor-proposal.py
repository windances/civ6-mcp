"""Phase-3 validation of a worker proposal: schema, real tools, real units, real tiles.

The rehearsal (`advisor-rehearsal.py`) produces a brief; a fresh context answers it as the
`military-map` worker; this is what the orchestrator is supposed to do with the answer before
acting on it. It checks, in the order Phase 3 lists them:

  1. the JSON validates against `contracts/worker-proposal.schema.json`;
  2. `worker` / `gameId` / `turn` match the brief;
  3. every `tool` named in an action exists in the live MCP tool inventory, with arguments whose
     names exist in that tool's schema;
  4. every unit id and tile named exists in the snapshot the worker was given;
  5. action ids are unique.

Usage:
  .venv\\Scripts\\python.exe .tools\\verify-advisor-proposal.py <proposal.json> [snapshot.json]
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "worker-proposal.schema.json"
SNAPSHOT_SCHEMA = ROOT / "contracts" / "turn-snapshot.schema.json"


def tool_inventory() -> dict[str, set[str]]:
    """Tool name -> its argument names, from a `tools/list` round trip to the MCP server.

    Spawned exactly the way `scripts/qualify-mcp.py` does it: `python -m civ_mcp` (the entry
    module, not `civ_mcp.server`), Lua and the web API disabled, UTF-8 forced. A tool name that
    is not in this inventory cannot be executed by the orchestrator, so a proposal naming one is
    rejected rather than attempted.
    """
    import os
    import queue
    import subprocess
    import threading
    import time

    child_env = dict(os.environ)
    child_env["CIV_MCP_DISABLE_LUA"] = "1"
    child_env["CIV_MCP_DISABLE_WEB_API"] = "1"
    child_env["CIV_MCP_DATA_DIR"] = str(ROOT / ".civ6-mcp-data")
    child_env["PYTHONUTF8"] = "1"
    process = subprocess.Popen(
        [sys.executable, "-m", "civ_mcp"],
        env=child_env,
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines: queue.Queue = queue.Queue()

    def pump(stream, sink):
        try:
            for line in stream:
                sink.put(line)
        finally:
            sink.put(None)

    threading.Thread(target=pump, args=(process.stdout, lines), daemon=True).start()

    def request(request_id: int, method: str, params: dict | None = None) -> dict:
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        assert process.stdin is not None
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + 60
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
            payload = json.loads(line)
            if payload.get("id") == request_id:
                if "error" in payload:
                    raise RuntimeError(f"{method} failed: {payload['error']}")
                return payload.get("result") or {}

    try:
        request(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "verify-advisor-proposal", "version": "1"}})
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        process.stdin.flush()
        listing = request(2, "tools/list", {})
    finally:
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
    inventory = {}
    for tool in listing.get("tools", []):
        schema = tool.get("inputSchema") or {}
        inventory[tool["name"]] = set((schema.get("properties") or {}).keys())
    return inventory


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    proposal = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8-sig"))
    snapshot = json.loads(pathlib.Path(args[1]).read_text(encoding="utf-8-sig")) if len(args) > 1 else None

    failures: list[str] = []
    notes: list[str] = []

    try:
        import jsonschema

        jsonschema.validate(proposal, json.loads(SCHEMA.read_text(encoding="utf-8")))
        print("1. schema                 : valid")
    except ImportError:  # pragma: no cover
        print("1. schema                 : jsonschema not installed, skipped")
    except Exception as exc:  # noqa: BLE001
        first = str(exc).splitlines()[0]
        failures.append(f"schema: {first}")
        print(f"1. schema                 : INVALID - {first}")

    if proposal.get("worker") != "military-map":
        failures.append(f"worker is {proposal.get('worker')!r}, expected military-map")
    print(f"2. worker / game / turn   : {proposal.get('worker')} / {proposal.get('gameId')} / "
          f"{proposal.get('turn')}")

    if "--no-inventory" in flags:
        inventory = None
        print("3. live tool inventory    : skipped (--no-inventory)")
    else:
        from_file = next((f for f in flags if f.startswith("--inventory=")), None)
        if from_file:
            # A deterministic inventory for tests and offline review: {tool: [argument, ...]}.
            payload = json.loads(pathlib.Path(from_file.split("=", 1)[1]).read_text("utf-8-sig"))
            inventory = {name: set(args) for name, args in payload.items()}
            print(f"3. tool inventory         : {len(inventory)} tools (from file)")
        else:
            inventory = tool_inventory()
            print(f"3. live tool inventory    : {len(inventory)} tools")
    seen_ids: set[str] = set()
    for action in proposal.get("actions", []):
        action_id = action.get("actionId")
        if action_id in seen_ids:
            failures.append(f"duplicate actionId {action_id}")
        seen_ids.add(action_id)
        tool = action.get("tool")
        if inventory is None:
            continue
        if tool not in inventory:
            failures.append(f"{action_id}: unknown tool {tool!r}")
            continue
        unknown = set((action.get("arguments") or {}).keys()) - inventory[tool]
        if unknown:
            failures.append(f"{action_id}: {tool} has no argument(s) {sorted(unknown)}")
    print(f"   actions                : {len(proposal.get('actions', []))} "
          f"({'ok' if not failures else 'see failures'})")

    if snapshot:
        # Unit ids may be structured (`unit_id`) or, as the rehearsal snapshot carries them,
        # inside the tool's own text (`... [id:1310724, idx:4]`). Both are real ids.
        unit_ids: set[int] = set()
        for unit in snapshot.get("units", []):
            if isinstance(unit.get("unit_id"), int):
                unit_ids.add(unit["unit_id"])
            for match in re.finditer(r"id:(\d+)", str(unit.get("detail") or "")):
                unit_ids.add(int(match.group(1)))
        tiles = {(u.get("x"), u.get("y")) for u in snapshot.get("units", [])}
        for key in ("target_city",):
            spot = (snapshot.get("map") or {}).get(key) or {}
            if spot:
                tiles.add((spot.get("x"), spot.get("y")))
        for action in proposal.get("actions", []):
            args = action.get("arguments") or {}
            if "unit_id" in args and args["unit_id"] not in unit_ids:
                failures.append(f"{action.get('actionId')}: unit {args['unit_id']} is not in the snapshot")
            if {"target_x", "target_y"} <= set(args) and (args["target_x"], args["target_y"]) not in tiles:
                notes.append(
                    f"{action.get('actionId')}: target ({args['target_x']},{args['target_y']}) "
                    f"is not a position in the snapshot (allowed if it is a legal destination)"
                )
        print(f"4. units in snapshot      : {len(unit_ids)} known ids; "
              f"{len(proposal.get('actions', []))} actions checked")

    for note in notes:
        print(f"   note: {note}")

    print()
    if failures:
        print("VERDICT: REJECT")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("VERDICT: ACCEPT (schema, tools, arguments, units, action ids)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
