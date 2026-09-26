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

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import handoff as h  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(h.main())
