from _game import require_game, require_game_pair, current_game_key
"""Everything the artifacts know about the Kabul city-state in this game."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".civ6-mcp-data"
RUN = "frozen-coral-oracle-79"
GAME = require_game()

out = []


def say(s=""):
    out.append(str(s))


# ---- mapstatic: initial cities / players ----
ms = json.loads((DATA / f"mapstatic_{GAME}_{RUN}.json").read_text(encoding="utf-8"))
say(f"=== mapstatic keys: {sorted(ms.keys())} ===")
say(f"  gridW={ms.get('gridW')} gridH={ms.get('gridH')} initialTurn={ms.get('initialTurn')}")

players = ms.get("players")
say(f"\n=== players ({type(players).__name__}) ===")
if isinstance(players, dict):
    for k, v in players.items():
        say(f"  {k}: {json.dumps(v, ensure_ascii=False)[:220]}")
elif isinstance(players, list):
    for v in players:
        say(f"  {json.dumps(v, ensure_ascii=False)[:220]}")

ic = ms.get("initialCities")
say(f"\n=== initialCities ({type(ic).__name__}, n={len(ic) if ic else 0}) ===")
kabul_entries = []
if isinstance(ic, list):
    for c in ic:
        blob = json.dumps(c, ensure_ascii=False)
        if "ABUL" in blob:
            kabul_entries.append(c)
            say(f"  KABUL: {blob}")
        elif isinstance(c, dict) and str(c.get("name", "")).lower().startswith("kab"):
            kabul_entries.append(c)
            say(f"  KABUL: {blob}")
say(f"  (kabul entries found: {len(kabul_entries)})")

# ---- mapturns: ownership of the Kabul tile over time ----
mt_path = DATA / f"mapturns_{GAME}_{RUN}.jsonl"
mt = [json.loads(x) for x in mt_path.read_text(encoding="utf-8").splitlines() if x.strip()]
say(f"\n=== mapturns rows: {len(mt)} (turns {mt[0]['turn']}..{mt[-1]['turn']}) ===")

# Find Kabul's coordinates from the last snapshot's cities list.
last = mt[-1]
say(f"  keys of a row: {sorted(last.keys())}")
cities = last.get("cities")
say(f"  last row cities type: {type(cities).__name__}")
if isinstance(cities, list):
    for c in cities[:60]:
        blob = json.dumps(c, ensure_ascii=False)
        if "ABUL" in blob:
            say(f"  last-row KABUL: {blob}")
    # print a couple of entries to learn the shape
    say(f"  sample city rows: {[json.dumps(c, ensure_ascii=False)[:120] for c in cities[:3]]}")

# ---- diary: agent notes about Kabul ----
diary = [json.loads(x) for x in (DATA / f"diary_{GAME}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
say(f"\n=== diary rows mentioning Kabul ===")
n = 0
for r in diary:
    blob = json.dumps(r, ensure_ascii=False)
    if "KABUL" in blob or "喀布尔" in blob:
        n += 1
say(f"  rows mentioning it: {n}")

# ---- telemetry: get_city_states / envoy calls ----
log = [json.loads(x) for x in (DATA / f"log_{GAME}_{RUN}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
say(f"\n=== telemetry: city-state / envoy related calls ===")
for o in log:
    if o.get("tool") in ("get_city_states", "send_envoy") or "KABUL" in json.dumps(o, ensure_ascii=False):
        say(f"  T{o.get('turn')} {o.get('tool')} params={json.dumps(o.get('params'), ensure_ascii=False)}")
        txt = str(o.get("result") or o.get("result_summary") or "")
        say(f"      -> {txt[:600]}")

out_path = ROOT / ".tools" / "_kabul.txt"
out_path.write_text("\n".join(out), encoding="utf-8")
print("wrote", out_path)
