"""Record a turn's diary rows from a session driven straight through the adapter.

The diary is written by the MCP's `end_turn`: it takes `GameState.get_diary_snapshot()`, builds one
row per player and one per city, and appends them (`server.py`, the "Write one row per player"
block). A session that talks to the game through `GameState` directly — no MCP tool calls — writes
**no diary at all**, and that matters beyond bookkeeping: the directive's answer to a failing rule
is "fix the gap, or record in the diary why it is being accepted", so a rule accepted on purpose
has nowhere to be recorded and the acceptance is invisible to the next session.

This writes the same rows, with the same field names, from the same snapshot. Keep it in step with
that block: if the row shape changes there, it changes here.

The directory comes from `CIV_MCP_DATA_DIR` **at import time**, and the default
(`~/.civ6-mcp`) is outside this sandbox, so point it at the workspace:

    $env:CIV_MCP_DATA_DIR = ".civ6-mcp-data"
    .venv\\Scripts\\python.exe scripts\\record-turn.py --reflections t99.json
    .venv\\Scripts\\python.exe scripts\\record-turn.py --show

`--reflections` takes a JSON object with the five contract fields (tactical, strategic, tooling,
planning, hypothesis). All five are required and must be non-empty: a row with empty reflections
is worse than no row, because it looks like the turn was reflected on.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from civ_mcp import run_manifest  # noqa: E402
# The directory is read from CIV_MCP_DATA_DIR at *import* time. Default it to the workspace copy
# the DSH overlay uses, so a script-driven session cannot silently write the diary to ~/.civ6-mcp
# (denied by the sandbox) or, worse, read nothing there and report rules as un-evaluable.
os.environ.setdefault(
    "CIV_MCP_DATA_DIR", str(ROOT / ".civ6-mcp-data")
)
# The data root holds one directory per playthrough plus a `current` pointer; the modules that
# resolve stored paths must be pointed at the run, not at the root that contains it.
os.environ["CIV_MCP_DATA_DIR"] = str(
    run_manifest.resolve_data_dir(os.environ["CIV_MCP_DATA_DIR"])
)

from civ_mcp import diary as diary_module  # noqa: E402
from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

REFLECTION_FIELDS = ("tactical", "strategic", "tooling", "planning", "hypothesis")


def require_reflections(data: dict) -> dict:
    """Validate one reflections object: the five contract fields, all non-empty."""
    missing = [f for f in REFLECTION_FIELDS if not str(data.get(f, "")).strip()]
    if missing:
        raise SystemExit(
            f"refused: missing {', '.join(missing)}; the diary contract wants all of "
            f"{', '.join(REFLECTION_FIELDS)} non-empty"
        )
    return {f: str(data[f]).strip() for f in REFLECTION_FIELDS}


def append_rows(path: pathlib.Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n")


def show(path: pathlib.Path, cities: pathlib.Path, tail: int) -> int:
    entries = diary_module.read_diary_entries(path)
    agents = [entry for entry in entries if entry.get("is_agent")]
    print(f"{path} -- {len(entries)} row(s), {len(agents)} agent row(s)")
    for entry in agents[-tail:]:
        print(diary_module.format_diary_entry(entry))
    print(f"{cities} -- {len(diary_module.read_diary_entries(cities))} row(s)")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reflections", type=pathlib.Path, help="JSON with the five fields")
    parser.add_argument("--show", action="store_true", help="print the tail of the diary and exit")
    parser.add_argument("--tail", type=int, default=1, help="rows to print with --show")
    parser.add_argument(
        "--retro",
        type=pathlib.Path,
        help="JSON list of {turn, reflections} written as retrospective rows (reflection-only)",
    )
    args = parser.parse_args()

    conn = GameConnection()
    await conn.connect()
    gs = GameState(conn)
    try:
        civ, seed = await gs.get_game_identity()
        path = diary_module.diary_path(civ, seed)
        cities = path.with_name(f"{path.stem}_cities.jsonl")

        if args.show:
            return show(path, cities, args.tail)

        if args.retro:
            # Retrospective rows for turns played before this tool existed: reflection-only, marked
            # `retro`, with no live stats - the snapshot is today's, not that turn's, and putting
            # today's numbers on a past turn would be worse than leaving them out. Sixteen turns of
            # the Moscow campaign had no row at all, which is the memory the doctrine is read from.
            entries = json.loads(args.retro.read_text(encoding="utf-8"))
            pid_line = await gs.execute_lua("print(Game.GetLocalPlayer())", "gamecore")
            local_pid = int(pid_line.strip().splitlines()[-1])
            stamp = datetime.now(timezone.utc).isoformat()
            rows = []
            for entry in entries:
                rows.append(
                    {
                        "pid": local_pid,
                        "is_agent": True,
                        "turn": int(entry["turn"]),
                        "game": f"{civ}_{seed}",
                        "timestamp": stamp,
                        "v": 1,
                        "retro": True,
                        "reflections": require_reflections(entry["reflections"]),
                    }
                )
            append_rows(path, rows)
            print(f"wrote {len(rows)} retrospective row(s): {[r['turn'] for r in rows]}")
            print(f"  {path}")
            return 0

        if not args.reflections:
            print("nothing to do: pass --reflections, --retro or --show")
            return 0

        reflections = require_reflections(
            json.loads(args.reflections.read_text(encoding="utf-8"))
        )
        overview = await gs.get_game_overview()
        snapshot = await gs.get_diary_snapshot()
        pid_line = await gs.execute_lua("print(Game.GetLocalPlayer())", "gamecore")
        local_pid = int(pid_line.strip().splitlines()[-1])
        game_id = f"{civ}_{seed}"
        stamp = datetime.now(timezone.utc).isoformat()

        rows: list[dict] = []
        for player in snapshot.players:
            row = dataclasses.asdict(player)
            row.update(v=1, turn=overview.turn, game=game_id, timestamp=stamp)
            if player.pid == local_pid:
                agent = snapshot.agent
                row.update(
                    is_agent=True,
                    diplo_states=agent.diplo_states,
                    suzerainties=agent.suzerainties,
                    envoys_available=agent.envoys_available,
                    envoys_sent=agent.envoys_sent,
                    gp_points=agent.gp_points,
                    governors=agent.governors,
                    trade_routes={
                        "capacity": agent.trade_capacity,
                        "active": agent.trade_active,
                        "domestic": agent.trade_domestic,
                        "international": agent.trade_international,
                    },
                    reflections=reflections,
                    agent_client="script",
                    agent_model="script-driven",
                )
            rows.append(row)

        city_rows = []
        for city in snapshot.cities:
            row = dataclasses.asdict(city)
            row.update(v=1, turn=overview.turn, game=game_id, timestamp=stamp)
            city_rows.append(row)

        append_rows(path, rows)
        append_rows(cities, city_rows)
        print(f"wrote {len(rows)} player row(s) + {len(city_rows)} city row(s) for turn {overview.turn}")
        print(f"  {path}")
        print(f"  {cities}")
    finally:
        await conn.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
