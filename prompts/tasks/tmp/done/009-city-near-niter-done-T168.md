# TEMP TASK 009 — a city near the Niter

added:     2026-09-26 (human instruction: 在硝石附近建城)
expires:   turn 175 — a Settler is 80 hammers and 007 owns the war city's queue, so this is counted
           from the queue, not the calendar: the declaration is a turn or two out, the third Catapult
           and the melee upgrades come first, and the Settler is the first build after the first city
           falls. 005 expired unused because its clock was written against the calendar; do not
           repeat that.
done when: a **6th city of ours exists and its radius-3 map read contains a NITER tile** (count >= 1),
           the tile is inside that city's borders, and a Builder is assigned to mine it (or the mine
           already stands). Report the city, the tile and the stockpile.
overrides: the per-city build lists **of a city that is not the war city**: a **Settler (80 hammers)**
           may be inserted there, with one escort found from the garrison rotation — never from the
           staging row. It does **not** outrank 007: nothing comes off the assault establishment, no
           unit leaves the (53,34)-(56,37) row, and the declaration is not delayed for it.
scope:     one new city near a Niter tile. No declaration of war, no change to research or civics, no
           peace offer, and nothing pulled off 007's army or 008's sweep.

## Why Niter, and why a city rather than a Builder

Niter is a **strategic** resource, not a bonus tile: it is the line that leads to the Bombard and to
the infantry upgrades, and our stockpile is already moving (**+2/t**, measured T123 onward), which
means at least one Niter tile is owned and mined. The city rows still list a **Niter tile as
unimproved** (上海's and 北京's `Needs builder:` lines both carry it), so there is more than one — and a
tile four or five rings out from an existing city center cannot be worked, only owned. A city center
near it does three things at once: it works the tile, it puts the mine inside a border that can be
defended, and it opens the land around it.

## Where it is — read it, do not trust a note

Two measured hints, neither of them a substitute for a map read:

* the adapter's own comment in `src/civ_mcp/lua/cities.py` records an unimproved **NITER at (58,30)**
  in 北京's row — that reading was from T60, when Niter was *not yet revealed* and the row was a
  phantom that `get_builder_tasks` marked URGENT and a Builder could not mine. The `resVisible` guard
  was written for exactly that. It is the best single candidate we have.
* the live city rows print `NITER, 30` for 上海 and for 北京. The narration prints only the **y**
  coordinate of each unimproved resource (`RICE, 29` is the rice at (58,29), `COCOA, 26` is the one at
  (51,26)), so both readings put the Niter on **y=30**.

So: **sweep the map before choosing the tile.** `get_empire_resources` lists unimproved resources with
their coordinates, `get_map_area` radius 3 around a candidate city site shows the ring it would own,
and `scripts/probe-tile.py x,y` prints the raw tile record. Barren, wrong coordinates copied from an
old note have already cost this campaign once (the camp at (60,30) vs (60,29)).

## The order of work

1. **Locate every Niter tile we can see**, and say which are owned and which are not. A tile in
   nobody's territory is settled *for*; a tile already in 上海's or 北京's borders but outside their
   workable ring is the case this task is about.
2. **Pick the site** the way the settle advisor says, with the Niter inside **radius 1-3**: fresh
   water if a fresh-water tile also has the Niter, otherwise take the food the site can actually
   support (the 成都 lesson: a no-water site caps near pop 5-6 and needs an Aqueduct later). Check
   loyalty (`get_cities` pressure) — a far-flung sixth city is a flip risk if it lands near Russia.
3. **Queue the Settler in a city that is not the war city**, with an escort, and name both in the
   diary on the turn the queue is set. 成都 or 上海 are the candidates; 西安 belongs to the war.
4. **Settle, then mine.** A Niter tile under jungle, forest or marsh needs `remove_feature` first —
   measured twice this game (the forest at (56,28), the jungle at (61,32)) — and a Builder with a
   charge. Read the tile before ordering the mine so the refusal is not a surprise.
5. **Record it**: the city, the turn it was founded, the Niter tile with its coordinates, whether it
   is the first or the second Niter, and the stockpile at that moment.

## What this task is not

Not a reason to delay the war, not a reason to pull a unit off the staging row, and not a repeat of
005 — which expired unused because its expiry was written against the calendar instead of the queue.
It is also not a research task: Niter is already revealed and accumulating, so nothing about the tech
tree changes to satisfy it.
