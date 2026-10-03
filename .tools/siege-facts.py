from _game import require_game, require_game_pair, current_game_key
"""Final facts for the siege write-up."""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".civ6-mcp-data"
GAME = require_game()

out = []


def say(s=""):
    out.append(str(s))


# 1. latest diary row for us
d = [json.loads(x) for x in (DATA / f"diary_{GAME}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
mine = sorted([r for r in d if r.get("is_agent")], key=lambda r: r.get("turn", 0))
last = mine[-1]
say(f"=== our latest diary row: T{last['turn']} ===")
for k in ("cities", "pop", "science", "culture", "gold", "military", "era", "government",
          "current_research", "current_civic", "era_score", "unit_composition", "stockpiles", "luxuries"):
    say(f"  {k}: {last.get(k)}")
say(f"  techs ({len(last.get('techs') or [])}): {last.get('techs')}")
say(f"  civics ({len(last.get('civics') or [])}): {last.get('civics')}")

# 2. city ownership history for Russia (pid 1) and us (pid 0)
mt = [json.loads(x) for x in (DATA / f"mapturns_{GAME}_elder-copper-empire-90.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
# also fold in every mapturns file to get the widest run
allmt = []
for p in DATA.glob(f"mapturns_{GAME}_*.jsonl"):
    allmt += [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
seen = {}
for row in allmt:
    seen.setdefault(row["turn"], row)
say("")
say("=== city ownership over time (Russian + ours) ===")
for turn in sorted(seen):
    row = seen[turn]
    rus = [f"{c['name'].replace('LOC_CITY_NAME_','')}({c['x']},{c['y']})" for c in row["cities"] if c["pid"] == 1]
    ours = [f"{c['name'].replace('LOC_CITY_NAME_','')}({c['x']},{c['y']})" for c in row["cities"] if c["pid"] == 0]
    line = f"  T{turn:3}  us={len(ours)} {ours}   |   Russia={len(rus)} {rus}"
    say(line)

# 3. any city-capture notifications anywhere
say("")
say("=== any capture / loyalty-flip notification in results ===")
import re
for p in sorted(DATA.glob(f"log_{GAME}_*.jsonl")):
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        res = str(o.get("result") or "")
        if re.search(r"captured|CAPTURED|flipped|忠诚度|叛离|revolt|City captured", res):
            head = res[:160].replace("\n", " | ")
            say(f"  T{o.get('turn')} {o.get('tool')} {head}")

p = ROOT / ".tools" / "_siege_facts.txt"
p.write_text("\n".join(out), encoding="utf-8")
print("wrote", p, "lines:", len(out))
