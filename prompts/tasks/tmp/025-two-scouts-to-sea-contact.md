# TEMP TASK 025 - two scouts to sea: find the civilizations we have not met

added:     2026-09-28 (human instruction: 新任务：出两个侦察兵，出海探索更多文明，不恋战，获取到信息就走)
expires:   turn 255 - 30 turn(s) from T225, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **`get_diplomacy` lists a civilization it did not list at turn 220 (it lists five there), and both
           Scout-line units are alive when it does** - the new contact's own line (name, leader,
           cities if visible, military, war state) is written into the diary the turn it is seen,
           with the tile it was seen from, and `get_victory_progress` agrees on the count. Retire it
           the turn that contact is made, or as `-expired-T<n>.md` at the turn 248 hard stop with
           the map delta and everything sighted instead.
overrides: **the human's instruction, 不恋战 above all.** These two units are not being sent to fight: they exist
           to look, and **a contact that costs a scout is a worse outcome than no contact** - the
           instruction says 获取到信息就走, so the run ends with the information, not with a body count.
           **They are authorized to**: leave the map we know, embark, cross water, walk into fog,
           and enter another civilization's territory if it lets them. **They are not authorized
           to**: attack anything (no `attack`, no `condemn`, no city strike), hold a tile (`fortify`
           only to heal, never as a position), garrison a city, or be reinforced by the corps.
           **When something hostile appears**: if the unit is under half HP and an enemy is
           adjacent, withdraw - a living scout that reports is worth more than a dead one that
           traded; if a barbarian camp or a warship blocks the only route, note it and go around.
           **It does not override**: the two tasks in force - 023 (the Dutch campaign) never borrows
           these units and this file never pulls a unit from it, and 024 (Brussels) keeps its own
           train - nor `one-garrison-per-city`, nor the directive's ban on `propose_peace`, nor the
           standing 'no new unit' line for the campaign. **The one thing it may create is these two
           scouts**: the standing army is not touched, and if fewer than two Scout-line units exist,
           building or buying exactly the difference is this file's business and nothing else's. If
           the last contact is made and both scouts are still alive, the task is over and the units
           revert to whatever the directive says about idle scouts.
scope:     The two Scout-line units, the water and the fog they can reach, the civilizations they meet, and the
           tiles they sight on the way. Not a barbarian camp (report its tile and leave it), not a
           city-state (report it and do not envoys-and-leave it - envoys are `get_city_states`'
           business, not this file's), not a war, not a siege, not a garrison, and no unit of the
           standing army.

## What this instruction is

出两个侦察兵，出海探索更多文明，不恋战，获取到信息就走 - two scouts, out to sea, to find civilizations
we have not met; do not get drawn into a fight; take the information and go.

This is the same ask as task 019 on the run that was rolled back (`done/019-two-scouts-to-sea-expired-T250.md`,
dispatched at T220 and expired at T250 with its thirty-turn window), re-issued for this position with one
thing made explicit that the earlier file left to judgement: **不恋战**. 019's finish line was "two units of the
Scout line are alive, each on a water tile"; this one's is a *contact*, because that is what the instruction
is for.

## The two units

- **Read `get_units` first.** The Scout line here is `UNIT_SCOUT` and its upgrade `UNIT_RANGER`; if two of
  them exist, this file creates nothing. If one or none exists, **build or buy exactly the difference** -
  a Scout is the cheapest unit in the game and any of our cities with a free queue slot can produce one;
  `purchase_item(city_id, "UNIT", "UNIT_SCOUT")` is the instant route when the treasury allows it.
- **Drive them with `automate`** (`unit_action(action="automate")` - "Auto-explore, Scouts only"): it is
  written for exactly this job, it does not seek fights, and AGENTS.md's Exploration section endorses it.
  Hand-drive them instead when a specific hole in the map matters more than the general sweep, or when an
  automated scout is about to walk into something we can see (`get_map_area` radius 2 around its tile).
- **They are not part of the corps.** 023's train never gets them and never gives them up; if a scout is
  the nearest unit to a Dutch city it is still not a siege asset - it is a scout.
- A land unit embarks with a plain move order and needs no ship: measured T219, Cavalry #5177368 was
  ordered to a water tile and answered `MOVING_TO|74,28|now_at:74,29|STOPPED_MID_PATH` - it was at sea.
  Scouts are slower (3 movement) but the same rule applies, and `TECH_SHIPBUILDING` is long behind us.

## 不恋战 - the rules of engagement

1. **Never attack.** No `attack`, no `condemn`, no city strike, with either scout, ever. A scout that has
   traded a hit has stopped being a scout.
2. **Do not hold ground.** `fortify` is for healing only; never leave a scout parked on a tile as a picket
   for turns on end - if it is not moving it is not finding anything.
3. **Withdraw from a losing position.** An enemy adjacent and the scout under half HP: move away this turn,
   even into fog, rather than trade. Speed is its armour.
4. **Route around what blocks.** A barbarian camp, a barbarian warship (T220: one Galley at 17 HP and one at
   full, both on our southern coast), or a city-state that refuses passage: note the tile, note the refusal,
   and take the other way. None of them is this task's objective.
5. **Fog is the point, not the map we already own.** Prefer the unexplored water and coastlines; a scout
   re-walking known ground is a wasted scout.

## What counts as information

The deliverable is not "a scout moved"; it is what a scout *saw*, written into the diary **the turn it is
seen** - the turn matters, because the next session reads the diary as memory:

- **a new civilization**: its name and leader from `get_diplomacy` (the line that appears when contact is
  made - name, leader, war/peace state, `Cities (N)`, military strength vs ours), its agenda if the line
  shows one, and whether anyone we already know is at war with it;
- **its cities**, if any are visible: `name pop P (x,y) walls W` - the same shape task 023's Gate 0 needs;
- **the map**: the tiles that stopped being fog, and `exploration_pct` from `get_game_overview` - report
  the delta, not the absolute;
- **what it implies**: whether a landmass is reachable, where a strait is, and whether the 5-civilization
  list we had at T220 is short because the world is big or because we never looked.

## Where to go first

`get_diplomacy` at T220 lists **five** civilizations and 荷兰 is the only war; the sea route the Dutch sit
across was opened by the Cavalry at T219. So the first sweep is the water north and north-east of 塞纳 and
布鲁塞尔 - the same water the Dutch campaign is about to cross - and then wherever the coastline stops being
fog. **Do not follow 023's army**: two scouts going the same way as the corps learn nothing the corps will
not learn anyway.

## Reporting

Per contact, the turn, the tile the sighting was made from, and the full `get_diplomacy` line. At the end:
the civilization count before and after (five at the start), the `exploration_pct` delta, how many turns
each scout survived, and which parts of the map are still dark - that list is the next task's starting
point. If it expires without a contact, say where each scout stood, what it had seen, and what stopped it
(a refused strait, a barbarian wall, a dead end) - an honest dead end is a result.

## Why this is a file, and not a turn-check rule

No metric carries "made contact and came back". `get_victory_progress` counts what we have met but has no
opinion on whether we are *trying*, and `exploration_pct` rises for a scout that wanders in circles. What
this instruction adds to the machine is a **purpose** for two cheap units and a **rule about fights** that
no check can express - which is what a task file is for.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "two scouts to sea: find the civilizations we have not met" --slug two-scouts-to-sea-contact --instruction @.tmp\t025-instruction.txt --why "two scouts to sea, on the human's instruction: make contact with civilizations we have not met, and do not get drawn into a fight" --done-when @.tmp\t025-done.txt --overrides @.tmp\t025-overrides.txt --scope @.tmp\t025-scope.txt --body-file .tmp\t025-body.md --cn @.tmp\t025-cn.md --turns 30 --replace --no-commit
     at: 2026-09-28T19:11:39+08:00
     chinese backup: prompts/tasks/cn/025-two-scouts-to-sea-contact.cn.md
-->
