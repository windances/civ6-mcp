"""The MCP qualification gate must not write into the live playthrough.

``scripts/qualify-mcp.py`` is a protocol smoke test: it starts a real ``civ_mcp`` server over
stdio and asks it for ``tools/list``. That server stamps ``heartbeat.write("starting")`` on
startup, and the file lands in whatever ``CIV_MCP_DATA_DIR`` resolves to - which for the live
match is ``<workspace>/.civ6-mcp-data/runs/<civ>-<seed>/``, reached through the ``current``
pointer in the data root (``run_manifest.resolve_data_dir``).

Measured 2026-10-04, with a session playing this match: the gate handed the child the
workspace's own data root, so running ``qualify-mcp.py`` - a static gate, run before every
commit - replaced

    {"phase": "playing", "turn": 347, "pid": 40216, "run_id": "swift-ebony-requiem-96",
     "civ": "china", "seed": -1894041591}

with

    {"phase": "starting", "turn": 0, "civ": "", "seed": 0, "run_id": "obsidian-teal-sabre-02"}

and the pid it named was gone a moment later. Two readers take that file as fact:
``handoff.verdict``, which ``scripts/resume-game.ps1`` is built on, and ``temp_tasks.status``.
It is also the passive signal that says a session is playing, so a gate that overwrites it
tells the human's own handoff command that a fresh session is starting when one is running.

The test runs the gate from a throwaway working directory that holds a fake data root, and
asserts the tree comes back byte for byte. The old code aimed the child at
``os.getcwd()/.civ6-mcp-data``, so this catches the regression - and because the working
directory is temporary, a regression fails the test rather than damaging the real match.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "qualify-mcp.py"

RUN_ID = "china--1894041591"


def _snapshot(root: pathlib.Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _fake_data_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A data root shaped like the workspace's, `current` pointer and all."""
    root = tmp_path / ".civ6-mcp-data"
    run = root / "runs" / RUN_ID
    run.mkdir(parents=True)
    (run / "heartbeat.json").write_text(
        json.dumps(
            {
                "phase": "playing",
                "turn": 347,
                "ts": time.time(),
                "pid": 40216,
                "run_id": "swift-ebony-requiem-96",
                "civ": "china",
                "seed": -1894041591,
            }
        ),
        encoding="utf-8",
    )
    (root / "current").write_text(RUN_ID, encoding="utf-8")
    return root


def test_the_gate_leaves_the_data_root_it_runs_from_alone(tmp_path):
    root = _fake_data_root(tmp_path)
    heartbeat = root / "runs" / RUN_ID / "heartbeat.json"
    assert heartbeat.is_file()
    before = _snapshot(tmp_path)

    result = subprocess.run(
        [sys.executable, str(GATE)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )

    assert result.returncode == 0, result.stderr
    assert "MCP qualification passed" in result.stdout
    after = _snapshot(tmp_path)
    assert after == before, (
        "the qualification gate wrote into the data root it was run from: "
        f"{sorted(set(after) ^ set(before)) or 'same files, changed bytes'}"
    )
