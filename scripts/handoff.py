"""Can a fresh session take this match over, and from which save?

    .venv\\Scripts\\python.exe scripts\\handoff.py              # the report a human reads
    .venv\\Scripts\\python.exe scripts\\handoff.py --json       # facts + verdict + report
    .venv\\Scripts\\python.exe scripts\\handoff.py --task .civ6-mcp-data/resume-task.txt

Read-only and passive: it never launches, never loads, and does not touch the FireTuner
unless nothing else holds it (FireTuner serves one connection, so a probe from here would
compete with a session that is playing). Exit code 0 means a session can take over now.

The logic lives in ``civ_mcp.handoff`` so it can be tested without a game; this is the CLI.
"""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Point at the workspace data root and then at the current run, in that order, before anything
# imports a module that reads the variable at import time. Without it this script reads the home
# default (`~/.civ6-mcp`), finds no `runs/` there, and reports the identity from the stale heartbeat
# instead of from the run manifest - which is exactly the disagreement the manifest exists to settle.
from civ_mcp import run_manifest  # noqa: E402

os.environ.setdefault("CIV_MCP_DATA_DIR", str(ROOT / ".civ6-mcp-data"))
os.environ["CIV_MCP_DATA_DIR"] = str(run_manifest.resolve_data_dir())

from civ_mcp import handoff as h  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(h.main())
