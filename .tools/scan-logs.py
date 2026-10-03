"""Scan every MCP session log for the features added on 2026-09-26.

Usage:  .venv\\Scripts\\python.exe .tools\\scan-logs.py [keyword ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KEYS = ["SIEGE FIRE", "SIEGE POSTURE", "STALLED", "UNUSED ATTACK", "REFUSED|",
        "get_staging_plan", "RECON", "CUT THE SUPPLY LINE", "supply line", "idle3:"]


def main() -> int:
    keys = sys.argv[1:] or KEYS
    logs = sorted(Path(".civ6-mcp-data").glob("log_*.jsonl"))
    print(f"{'log':<52} " + " ".join(f"{k[:11]:>12}" for k in keys))
    for log in logs:
        rows = []
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        turns = [r.get("turn") for r in rows if isinstance(r.get("turn"), int)]
        counts = []
        for k in keys:
            counts.append(sum(1 for r in rows if k in str(r.get("result") or "")))
        name = log.name.replace(f"log_{GAME}_", "").replace(".jsonl", "")
        span = f"T{min(turns)}-T{max(turns)}" if turns else "?"
        print(f"{name[:30]:<30}{span:<10} " + " ".join(f"{c:>12}" for c in counts))

    for k in ("SIEGE FIRE", "CUT THE SUPPLY LINE", "get_staging_plan"):
        if k not in keys:
            continue
        print(f"\n### context for {k!r}")
        for log in logs:
            for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                if k not in line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                res = str(r.get("result") or "")
                i = res.find(k)
                print(f"  {log.name[-28:]} T{r.get('turn')} {r.get('tool')}:"
                      f" …{res[max(0, i - 120):i + 200]}…".replace("\n", " | "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
