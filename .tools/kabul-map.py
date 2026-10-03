from _game import require_game, require_game_pair, current_game_key
"""Is Kabul in China's way, and what do the 6 envoys currently pay?"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".civ6-mcp-data"
GAME = require_game()
RUN = "frozen-coral-oracle-79"
GAMEDIR = Path(r"D:\SteamLibrary\steamapps\common\Sid Meier's Civilization VI\Base\Assets\Gameplay\Data")

out = []


def say(s=""):
    out.append(str(s))


# ---- militaristic envoy production amounts ----
leaders = (GAMEDIR / "Leaders.xml").read_text(encoding="utf-8", errors="replace").splitlines()
for mid in (
    "MINOR_CIV_MILITARISTIC_PRODUCTION_FOR_CAPITAL",
    "MINOR_CIV_MILITARISTIC_PRODUCTION_FOR_ENCAMPMENT",
):
    say(f"--- {mid} ---")
    for i, ln in enumerate(leaders):
        if f"<ModifierId>{mid}</ModifierId>" in ln:
            j = i
            while j < len(leaders) and "</Row>" not in leaders[j + 1] if j + 1 < len(leaders) else False:
                j += 1
            for k in range(i, min(i + 20, len(leaders))):
                s = leaders[k].strip()
                if s.startswith(("<ModifierType>", "<Name>", "<Value>", "<YieldType>", "<Amount>")):
                    say("    " + s)
                if s == "</Row>" and k > i + 3:
                    break
            break

# ---- map around Kabul ----
ms = json.loads((DATA / f"mapstatic_{GAME}_{RUN}.json").read_text(encoding="utf-8"))
grid_w, grid_h = ms["gridW"], ms["gridH"]
terrain = ms["terrain"]
owners = ms.get("initialOwners")
say(f"\n=== terrain/owner encoding ===")
say(f"  terrain type={type(terrain).__name__} len={len(terrain) if hasattr(terrain,'__len__') else '?'}")
say(f"  initialOwners type={type(owners).__name__}")
if isinstance(terrain, list):
    say(f"  terrain sample: {terrain[:8]}")
if isinstance(owners, list):
    say(f"  owners sample: {owners[:12]}")


def idx(x, y):
    return y * grid_w + x


KX, KY = 51, 19
say(f"\n=== tiles around Kabul ({KX},{KY}) ===")
for dy in range(-2, 3):
    row = []
    for dx in range(-2, 3):
        x, y = KX + dx, KY + dy
        if not (0 <= x < grid_w and 0 <= y < grid_h):
            row.append("   .   ")
            continue
        t = terrain[idx(x, y)] if isinstance(terrain, list) else "?"
        o = owners[idx(x, y)] if isinstance(owners, list) else "?"
        row.append(f"{o:>3}/{str(t)[:3]:<3}")
    say(f"  y={KY+dy:2d}  " + " ".join(row))
say("  (owner/terrain; owner 12 = Kabul, 0 = China)")

# ---- current ownership from the newest mapturn ----
mt = [json.loads(x) for x in (DATA / f"mapturns_{GAME}_{RUN}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
last = mt[-1]
say(f"\n=== newest mapturn: turn {last['turn']} ===")
say("  our cities:")
for c in last["cities"]:
    if c["pid"] == 0:
        say(f"    {c['name'].replace('LOC_CITY_NAME_',''):12} ({c['x']:2d},{c['y']:2d}) pop {c['pop']}")
say("  city-states still alive:")
for c in last["cities"]:
    if c["pid"] >= 8 and c["pid"] != 62:
        say(f"    pid {c['pid']:2d} {c['name'].replace('LOC_CITY_NAME_',''):14} ({c['x']:2d},{c['y']:2d}) pop {c['pop']}")
say("  free cities / others:")
for c in last["cities"]:
    if c["pid"] >= 20 and c["pid"] != 62:
        say(f"    pid {c['pid']} {c['name']} ({c['x']},{c['y']}) pop {c.get('pop')}")

# Ownership changes over time for Kabul
say("\n=== did Kabul ever change hands? ===")
seen = set()
for row in mt:
    for c in row["cities"]:
        if "KABUL" in c["name"] or (c["x"], c["y"]) == (KX, KY):
            seen.add((row["turn"], c["pid"], c["pop"]))
for t, p, pop in sorted(seen):
    say(f"    T{t}: pid {p} pop {pop}")

# Our own cities ever captured?
say("\n=== all pids present in the newest mapturn ===")
say("  " + ", ".join(sorted({str(c["pid"]) for c in last["cities"]})))

p = ROOT / ".tools" / "_kabul_map.txt"
p.write_text("\n".join(out), encoding="utf-8")
print("wrote", p)
