# TEMP TASK 004 — found a city on the iron

added:     2026-09-26 (human instruction: 在铁矿附近建城)
expires:   turn 95 — retire this file by then whatever happens
done when: a **5th city of ours exists and its radius-3 map read contains an IRON tile** (count >= 1,
           read with `get_cities` plus `get_map_area` around the new city). The mine is the follow-up,
           not the completion test.
overrides: whatever per-city build list is running: a **Settler (80 hammers)** may be inserted in the
           highest-production city ahead of the next Builder or Campus, and this instruction raises the
           expansion count to **five** (the directive allows four to six; we are at four). Nothing else
           in the plan changes.
scope:     one new city. No declaration of war, no change to research or civics, and no unit pulled
           off a post it is holding.

## Why

The empire has **no iron at all** — the stockpile read `IRON 0/50` at T83 — and iron is the gate on the
whole armoured line: Swordsmen, Knights, Trebuchets. The directive's rule is "mine every strategic
resource inside your borders; never plan around an imported resource", and an import ends the moment a
war starts. There is an **unclaimed IRON tile at (60,32)** next to 北京 (T83 read; verify it against the
map before committing, and look for a second one — the earlier note also named (57,42)). Claiming it
with a city also delivers **Iron Working's boost** ("build an Iron Mine"), which on this branch is
worth about half that tech.

## What to do

1. **Find the iron on the map, do not trust this file.** Read `get_map_area` around the candidate site
   and confirm the plot's resource is `IRON`. A coordinate copied from an old note has already been
   wrong once in this game (the camp), so the map read is the source of truth, and iron can only be
   seen because Bronze Working revealed it.
2. **Rank candidates with the settle advisor, then check the three things it does not score:**
   `get_settle_advisor` / `get_global_settle_advisor` rank tiles by yields — they do not tell you
   whether the iron is inside the new city's **workable radius (3 tiles)**, whether the site has **fresh
   water** (housing is a hard stop in this empire: 上海 was frozen at pop 3 for forty turns), or whether
   the tile is **loyalty-safe** (within 9 tiles of our cities, or expect a governor requirement from
   `hold-what-you-take`).
3. **Build the Settler, do not buy it.** 80 hammers in the highest-production city (西安) is roughly
   six turns; the gold price is around 680 and the treasury was 76 at +28/t, so buying is not the route.
   **Never train a Settler in a city of size one** (none of ours is, but check). If 马格努斯 Magnus is
   established in that city, take 给养保障 Provision first so the Settler costs no population — if he is
   not there, accept the one-population cost and say so in the diary.
4. **Escort it in barbarian country.** A Settler is a civilian: any barbarian unit captures it, and
   barbarians are active (the camp beside 北京 was cleared at T84, and a cleared camp does not stop new
   ones). Read `get_map_area` radius 2 around the **destination** before the final move — the same check
   the AGENTS.md civilian rule asks for — and keep a military unit on or next to the Settler for the last
   two tiles.
5. **Settle, then mine.** Found the city on the tile the advisor ranked best among those that keep the
   iron workable. Then send a Builder to the iron: **clear the feature first if the tile carries jungle
   or forest** (`play-turn.py clear`), then `IMPROVEMENT_MINE`. That mine is Iron Working's boost and the
   start of a stockpile; an iron tile inside our borders that is never mined is the exact failure this
   empire already made once (iron was still unmined at T130 on the abandoned line).
6. **Garrison it and name it.** One unit on the new city's tile (`one-garrison-per-city` once a war is
   on, and the standing army before that), and write the city's name, its tile, the iron's tile and the
   mine's turn into the diary so the next session does not have to rediscover any of it.

## When it is done

When the 5th city stands with iron inside its radius, move this file to
`../tmp/done/004-city-near-iron-done-T<turn>.md` and record in the diary's `tooling` line: the city and
tile, the iron tile, whether the mine is built, and what it cost (the Settler's city and turns, the
population if any). At **turn 95** retire it regardless, as `004-city-near-iron-expired-T95.md`, and say
in the diary why the city was not founded — a Settler still walking is not a founded city.
