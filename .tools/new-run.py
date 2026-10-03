"""Reconstruct the new run (elder-copper-empire-90) — restart, reload, hang."""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".civ6-mcp-data"
RUN = "elder-copper-empire-90"
GAME = require_game()
LOG = DATA / f"log_{GAME}_{RUN}.jsonl"

rows = [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]


def ts(o):
    return datetime.fromtimestamp(o["ts"]).strftime("%H:%M:%S")


out = []
out.append(f"=== new run {RUN}: {len(rows)} telemetry rows ===")
if rows:
    out.append(f"first: {ts(rows[0])} T{rows[0].get('turn')} {rows[0].get('tool')}")
    out.append(f"last:  {ts(rows[-1])} T{rows[-1].get('turn')} {rows[-1].get('tool')}")

out.append("")
out.append("=== rows mentioning restart / load / hang / error ===")
for o in rows:
    blob = " ".join(
        [str(o.get("tool")), json.dumps(o.get("params"), ensure_ascii=False), str(o.get("result") or "")]
    )
    if any(k in blob for k in ("restart_and_load", "load_game_save", "HANG", "launch_game",
                               "kill_game", "WinError", "not found", "FAILED")):
        out.append(f"---------- {ts(o)} T{o.get('turn')} {o.get('tool')} "
                   f"{json.dumps(o.get('params'), ensure_ascii=False) if o.get('params') else ''}")
        res = (o.get("result") or o.get("result_summary") or "")
        out.append(str(res)[:900])

out.append("")
out.append("=== every end_turn result (first 300 chars) ===")
for o in rows:
    if o.get("tool") != "end_turn":
        continue
    res = str(o.get("result") or o.get("result_summary") or "")
    out.append(f"---------- {ts(o)} T{o.get('turn')}  dur={o.get('duration_ms')}ms")
    out.append(res[:300].replace("\n", " | "))

out.append("")
out.append("=== did the strategy directive get delivered in this run? ===")
for o in rows:
    res = str(o.get("result") or "")
    if "=== STRATEGY" in res:
        idx = res.index("=== STRATEGY")
        out.append(f"{ts(o)} T{o.get('turn')} {o.get('tool')} HAS STRATEGY BLOCK:")
        out.append(res[idx:idx + 200].replace("\n", " | "))
out.append("(end of strategy check)")

p = ROOT / ".tools" / "_new_run.txt"
p.write_text("\n".join(out), encoding="utf-8")
print("wrote", p)
