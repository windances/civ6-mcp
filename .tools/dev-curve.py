from _game import require_game, require_game_pair, current_game_key
"""Rebuild the development phase (T1-T115) of the China game from the diary."""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".civ6-mcp-data"
GAME = require_game()

rows = [json.loads(x) for x in (DATA / f"diary_{GAME}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
mine = sorted([r for r in rows if r.get("is_agent")], key=lambda r: r["turn"])
# de-duplicate by turn (the log can repeat a turn)
by_turn = {}
for r in mine:
    by_turn[r["turn"]] = r
mine = [by_turn[t] for t in sorted(by_turn)]

out = []


def say(s=""):
    out.append(str(s))


say("=== development curve (every ~5 turns) ===")
say(f"{'T':>4} {'cities':>6} {'pop':>4} {'sci':>6} {'cul':>6} {'gold':>7} {'faith':>6} {'mil':>5} "
    f"{'dist':>4} {'impr':>4} {'wond':>4} {'tech':>4} {'civ':>4}  research / civic")
prev = None
for r in mine:
    t = r["turn"]
    if t > 115:
        break
    if prev is not None and t - prev < 4 and t not in (1, 25, 42, 51, 91, 111, 114):
        continue
    prev = t
    say(f"{t:>4} {r.get('cities'):>6} {r.get('pop'):>4} {r.get('science'):>6} {r.get('culture'):>6} "
        f"{r.get('gold'):>7} {r.get('faith'):>6} {r.get('military'):>5} {r.get('districts'):>4} "
        f"{r.get('improvements'):>4} {r.get('wonders'):>4} {r.get('techs_completed'):>4} "
        f"{r.get('civics_completed'):>4}  {str(r.get('current_research')).replace('TECH_','')} / "
        f"{str(r.get('current_civic')).replace('CIVIC_','')}")

say("")
say("=== city count milestones ===")
last = None
for r in mine:
    c = r.get("cities")
    if c != last:
        say(f"  T{r['turn']:>4}: {c} cities")
        last = c

say("")
say("=== government changes ===")
last = None
for r in mine:
    g = r.get("government")
    if g != last:
        say(f"  T{r['turn']:>4}: {str(g).replace('GOVERNMENT_','')}")
        last = g

say("")
say("=== era / age ===")
last = None
for r in mine:
    e = (r.get("era"), r.get("age"))
    if e != last:
        say(f"  T{r['turn']:>4}: {str(e[0]).replace('ERA_','')} ({e[1]}), era score {r.get('era_score')}")
        last = e

say("")
say("=== when each city appeared (city diary) ===")
crows = [json.loads(x) for x in (DATA / f"diary_{GAME}_cities.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
first_seen = {}
districts_seen = defaultdict(list)
produced = defaultdict(list)
for cr in crows:
    if cr.get("pid") != 0:
        continue
    city = cr.get("city")
    t = cr.get("turn")
    first_seen.setdefault(city, t)
    for d in cr.get("districts") or []:
        key = (city, d)
        if t not in districts_seen[key]:
            districts_seen[key].append(t)
    p = cr.get("producing")
    if p and p != "NONE":
        produced[p].append((t, city))

for city, t in sorted(first_seen.items(), key=lambda kv: kv[1]):
    say(f"  T{t:>4}  {city}")

say("")
say("=== district completion (first turn each appears) ===")
for (city, d), turns in sorted(districts_seen.items(), key=lambda kv: min(kv[1])):
    say(f"  T{min(turns):>4}  {city:8} {d}")

say("")
say("=== what cities spent production on (first turn seen producing each item) ===")
for item, lst in sorted(produced.items(), key=lambda kv: min(t for t, _ in kv[1])):
    t0, city0 = min(lst)
    say(f"  T{t0:>4}  {item:34} ({len(lst)} rows, first in {city0})")

p = ROOT / ".tools" / "_dev_curve.txt"
p.write_text("\n".join(out), encoding="utf-8")
print("wrote", p, "lines:", len(out))
