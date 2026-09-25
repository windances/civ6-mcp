# TEMP TASK 005 — found a city on the copper

added:     2026-09-26 (human instruction: 在铜矿附近建城)
expires:   turn 115 — extended from T95 on 2026-09-26: this one runs only *after* the iron city, whose
           Settler alone completes at ~T95, so a T95 expiry made the copper city impossible by design.
           Retire this file by T115 whatever happens.
done when: a **6th city of ours exists and its radius-3 map read contains a COPPER tile** (count >= 1,
           read with `get_cities` plus `get_map_area` around the new city)
overrides: whatever per-city build list is running: a **second Settler (80 hammers)** may be inserted
           after the iron city's Settler, and this instruction raises the expansion count to **six** —
           which is the directive's own ceiling ("four to six cities, then stop expanding"), so this is
           the last city this plan allows. Nothing else changes.
scope:     one new city. No declaration of war, no change to research or civics, and nothing pulled off
           an existing post.

## What the copper actually is — read this before spending a Settler

**Copper is a BONUS resource, not a strategic one.** The T83 resource read lists it as
`[B] COPPER at (50,33) — 3 tiles from 长沙`: it is unclaimed, and the `[B]` is the whole point. Compare
`[S] IRON at (60,32)`, which is strategic and gates Swordsmen, Knights and Trebuchets. Copper gives no
unit, no stockpile and no unlock — a Mine on it is worth about **+2 Gold**.

So the copper alone does **not** justify a city. What makes this worth doing is the pair:

- **A mine is a mine.** The Wheel's boost is "mine a mineral resource" and **Apprenticeship's is "build
  3 mines"** — a copper mine counts toward both. This empire already needs three mines for Apprenticeship
  and has been poor at mines (its first two improvements were a lumber mill and a camp).
- **The site has to stand on its own**: fresh water (housing is this empire's hard stop — 上海 sat at pop
  3 for forty turns), a workable iron-free tile set, loyalty inside 9 tiles of a city, and no theft of
  长沙's best tiles. If the ranking comes out bad, **say so in the diary and do not found the city**; a
  sixth city that costs 80 hammers and returns +2 gold is a loss. Record the decision either way.

## Order

**Task 004 (the iron city) outranks this one.** Iron is strategic and there is none in the empire
(`IRON 0/50`); copper is +2 gold. The iron Settler is already in production in 西安 as this file is
written — finish that city, mine the iron, and only then queue the copper Settler. If the treasury or
the turn budget makes one of the two impossible before turn 95, the iron city is the one that happens.

## What to do

1. **Find the copper on the map, do not trust this file.** The T83 read puts it at **(50,33)**, 3 tiles
   from 长沙; verify with `get_map_area` and check whether a second copper tile exists nearer a better
   site. (A coordinate copied from an old note has already been wrong once in this game — the camp.)
2. **Rank the site with the settle advisor, then check what it does not score**: the copper inside the
   new city's **workable radius of 3**, **fresh water** if any is available, **loyalty** (it is close to
  长沙, so this should be safe — confirm), and **tile overlap** with 长沙, which is the smallest city in
   the empire and cannot afford to lose its best two tiles.
3. **Build the Settler, do not buy it.** 80 hammers in the highest-production city; the gold price is
   several hundred and the treasury is committed to a Catapult (480 gold) first. Never train a Settler in
   a city of size one.
4. **Escort it.** A Settler is a civilian and any barbarian captures it; read `get_map_area` radius 2
   around the destination before the final move — the check the civilian rule in AGENTS.md asks for — and
   keep a military unit on or next to it for the last two tiles. The south side near 长沙 is where the
   barbarian galleys have been operating.
5. **Settle, then mine.** Found the city, then send a Builder to the copper: **clear the feature first if
   the tile carries jungle, forest or marsh** (`play-turn.py clear`), then `IMPROVEMENT_MINE`. Count it
   toward Apprenticeship's three mines and say in the diary how many mines the empire now has.
6. **Garrison it and name it.** One unit on the new city's tile, and the diary carries the city, its
   tile, the copper's tile, the mine's turn, and the empire's city count (six is the ceiling — after this,
   a Settler is a mistake unless the directive changes).

## When it is done

When the 6th city stands with copper inside its radius, move this file to
`../tmp/done/005-city-near-copper-done-T<turn>.md` and record in the diary's `tooling` line: the city and
tile, the copper tile, whether the mine is built, the mine count, and what it cost. At **turn 95** retire
it regardless, as `005-city-near-copper-expired-T95.md`, and say whether the iron city landed first and
why the copper city did not.
