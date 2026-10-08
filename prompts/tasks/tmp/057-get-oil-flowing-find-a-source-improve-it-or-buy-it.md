# TEMP TASK 057 - Get oil flowing: find a source, improve it, or buy it

added:     2026-10-09 (human instruction: 新任务：没有石油了，开采石油。)
expires:   turn 456 - 20 turn(s) from T436, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 unimproved oil tiles inside our borders, and the resource line shows OIL >= 1 per turn,
           with the builder order that did it named
overrides: the general builder dispatch order: an unimproved oil tile outranks the other 100 builder tasks, and
           a builder with moves >= 1 is reserved for it
scope:     locating oil (get_empire_resources, get_strategic_map, get_map_area), building the well or the
           offshore improvement, buying a tile that is one ring outside our borders, and a trade
           only if no source is reachable; no change to the war

## The instruction (verbatim, 2026-10-08)

"新任务：没有石油了，开采石油。"

Oil is a strategic resource and a **stock**, not a rate: when the pool reads 0 the units that burn it
(Modern Armor, Mechanized Infantry, oil power plants) stop being buildable, upgradable and
replaceable. The human's report is that the pool is empty. Verify it from the game's own resource
line before acting - `end_turn` prints it, and `get_empire_resources` names every source with its
state - then get a source onto our books.

## Find the oil, in this order

1. **`get_empire_resources`** - every strategic resource we know, each source tile, and whether it is
   improved. Oil shows as `RESOURCE_OIL`; an unimproved one is the cheapest fix in the game.
2. **`get_strategic_map`** - the same question over the whole empire: which oil tiles are inside our
   borders and bare, and which are just outside them. **A tile one ring outside is a `purchase_tile`
   away** (gold) and that is usually faster than waiting for a border to grow.
3. **`get_map_area` around each candidate** before sending anyone - the tile may be on hills, in
   forest or jungle (a feature has to come off first: `remove_feature`, then `improve`), or inside
   another civ's territory, in which case it is a trade question, not a builder question.
4. **`get_builder_tasks`** for the nearest builder to each tile. **Check `moves` before ordering
   `improve`** (measured T434, this match: 3 of 4 `improve` orders that turn died with
   `CANNOT_IMPROVE|Builder has no moves remaining this turn`). Order only a builder with
   `moves >= 1`, and if the list's nearest builder has 0, take the next one - a wasted order costs
   the turn, not just the call.

## What to build

- **Land oil**: a Builder builds an **Oil Well** on the resource tile (`IMPROVEMENT_OIL_WELL`). It
  needs the tile, a builder with a charge, and the tech that reveals and works oil.
- **Offshore oil**: a Builder on the water tile builds the offshore improvement; a land unit cannot
  reach it without `TECH_SHIPBUILDING` (measured: "water tile - land units need Shipbuilding tech to
  embark"), so use a builder that is already able, or a city's own coastal tile.
- **If no source is ours and none is buyable**: oil is then a **trade** question -
  `get_trade_options(player_id)` on a civ with a surplus, `propose_trade(..., mode="test")` first to
  see the counter-offer, then `send`. This is the fallback, not the first move.

## What this is for

Report at the end which source we gained, on which tile, the turn it came online, and what the pool
reads afterwards - the point of the task is a **positive oil income**, not a builder standing on a
tile. If the pool cannot be made positive this window, say which source is closest to ready and the
turn it lands, so the next window starts there.

## Done when

The resource line shows `OIL` with a **positive per-turn income** (or a stock that is no longer
falling) and at least one oil tile of ours is improved, with the builder order that did it named and
the `moves` check recorded. Then retire this file.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Get oil flowing: find a source, improve it, or buy it" --instruction 新任务：没有石油了，开采石油。 --done-when "count == 0 unimproved oil tiles inside our borders, and the resource line shows OIL >= 1 per turn, with the builder order that did it named" --overrides "the general builder dispatch order: an unimproved oil tile outranks the other 100 builder tasks, and a builder with moves >= 1 is reserved for it" --scope "locating oil (get_empire_resources, get_strategic_map, get_map_area), building the well or the offshore improvement, buying a tile that is one ring outside our borders, and a trade only if no source is reachable; no change to the war" --why "put a source of oil on our books, because the pool is empty and the units that burn it cannot be replaced" --turns 20 --cn @.tmp/task057-cn.txt --body @.tmp/task057-body.txt
     at: 2026-10-09T04:15:52+08:00
     chinese backup: prompts/tasks/cn/057-get-oil-flowing-find-a-source-improve-it-or-buy-it.cn.md
-->
