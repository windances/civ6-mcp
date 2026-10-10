# TEMP TASK 026 - a navy: frigates, or the tier above them, from the coastal cities

added:     2026-09-28 (human instruction: 新任务：沿海城市，生产护卫舰，或更高级的舰船)
expires:   turn 277 - 40 turn(s) from T237, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **at least two naval units of the Frigate tier or above are ours (`get_units` names them) and every
           coastal city that can build a ship is building one** - each was laid down in a coastal
           city and that city's queue went straight back to a ship or to its Harbour, the per-city
           production arithmetic is in the diary, and the fleet's first mission is named (escort the
           crossing to the Netherlands, or clear our own coast of the Dutch raiders). Hard stop at
           turn 269, re-counted from the queues the turn they are set.
overrides: **the human's instruction, and the coastal cities' queues for as long as it takes.**
           沿海城市，生产护卫舰，或更高级的舰船 - the instruction names the *place* (coastal cities) and the *unit*
           (Frigate, or better), so **this file owns the queue of every coastal city that can build
           a ship** and nothing else: it outranks the directive's generic build order there, and it
           may spend a coastal city's production on the Harbour/Shipyard chain when that is what
           unlocks or speeds the ships. **It does not override**: the two tasks in force - 023 (the
           Dutch campaign) keeps its army and its gold, and 025 (the two scouts) keeps its units;
           this file neither borrows from them nor vetoes them - nor `one-garrison-per-city`, nor
           `hold-what-you-take`, nor the directive's ban on `propose_peace`, nor 西安's Spaceport line
           (an inland city, and not this file's). **No new land unit is authorized here**, and the
           standing army is not touched: the only production this file claims is naval. **Gold**:
           buying a ship is allowed only when the treasury can pay for it without dropping the
           empire under the directive's gold floor - the measured price is 1120 g for a Frigate
           against a treasury that has been around 300 g, so production is the route and gold is the
           exception, and the diary says which was used and why. **A ship is not the campaign**:
           this file ends when the ships exist, not when the Netherlands does; taking their cities
           stays 023's business.
scope:     The coastal cities (the ones whose production list offers a naval unit), their queue slots, their
           Harbour and Shipyard, the naval units built there, and the water they are ordered to
           hold. Not the inland cities, not the army or the siege train (023's), not the two scouts
           (025's), not a landing, not a war declaration, and not a city's capture.

## Why this instruction, measured

Three readings from this branch, all of them the session's own:

- **We have no warship at all.** Every `UNIT_GALLEY` in the logs is a **Barbarian** one
  (`THREAT: Barbarian UNIT_GALLEY ...`); our own navy is zero, while our cities' production lists
  already offer `UNIT_CARAVEL (240)`, `UNIT_FRIGATE (280)` and `DISTRICT_HARBOR (54)`.
- **The Dutch have been on our coast for fifteen turns with Caravels.** From T221 to T235
  `THREAT: 荷兰 UNIT_CARAVEL CS:55 ... dist:1` repeats nearly every turn, at (74,23), (75,26), (75,28),
  (76,26) - two hulls sitting in the water one tile from our land. Land units can trade with them
  (a Cavalry, then a Field Cannon, each turn) but cannot clear the water, and a city that cannot be
  approached by sea is a city whose coast belongs to whoever has ships.
- **The next tier is one turn of research away.** At T229 `蒸汽动力 (TECH_STEAM_POWER)` read
  **85%, 1 turn**, and its boost is 建造2座造船厂 (2 Shipyards) unlocking 装甲舰 - so
  "或更高级的舰船" is a real choice this session, not a long-term hope.

## Gate 0 - which cities are coastal, and what each can build

**One call per candidate city, and the answer decides everything:**
`get_city_production(city_id)` lists what that city can build *now*, so a naval unit in the list means
the city is coastal **and** the tech and the Harbour are already there. Write the list down:

| city | can build | cost | turns | buy |
|---|---|---|---|---|
| (read it) | `UNIT_FRIGATE` / `UNIT_CARAVEL` / 装甲舰 / `DISTRICT_HARBOR` | as printed | as printed | as printed |

The measured shape at T219-T224: a Frigate was **280 production, 12 turns in the best coastal city and
19-21 turns in the next one**, a Caravel 240 at 11-18 turns, and a Harbour 54 at 8-21 turns. **A city
that can only offer the Harbour is not a shipyard yet** - its queue goes to the Harbour (and then the
Shipyard), and the diary says how many turns that costs before a hull can start.

## The queues

1. **Set every coastal city that offers a ship to build a ship, this turn.** The instruction is about
   production, and a coastal city building a Monument is a coastal city not building a navy.
2. **Prefer the better hull, and say why.** If 装甲舰 (Ironclad) is available or arrives within a few
   turns of Steam Power finishing, it outclasses the Frigate; otherwise build Frigates now and let the
   next hull be the better one. Do not idle a queue waiting for a tech: a Frigate built now is a ship
   that exists.
3. **Never leave those queues empty.** When a ship launches, the same city starts the next hull (or the
   Harbour/Shipyard that makes the next one cheaper) - the `end_turn` blocker will otherwise put
   something else there, and the programme dies quietly.
4. **Count from the queue, not from hope.** At 4-5 production a Frigate is a **60-turn** project; at the
   best coastal city's rate it was 12. **Put the arithmetic in the diary**: city, production per turn,
   cost, turns, and whether T269 still holds.

## The mission is already written by the war

The Dutch war (023) crosses water, and the sea between us is held by their Caravels. So the fleet's
first job, in order:

- **clear our own coast** - a Frigate outranges a Caravel (range 2) and takes no return fire from a
  melee ship it can keep at distance, so it kills raiders without trading hulls;
- **escort the crossing** - the campaign's embarked units are the ones a Caravel eats;
- **bombard the coast** - `[rolled-back run]` a single Frigate took 哈勒姆's 100-point wall pool to 0 in
  six turns from range 2, which is the cheapest wall damage this empire has ever had (the run that
  measured it has been rolled back; the geometry has not).

A ship with no named mission is a ship that will be parked in a harbour, so the diary names one.

## What this file is not

It is not a landing, not a second offensive, and not 023 - the ships serve the campaign that exists and
this file retires when the hulls do. It also does not touch the two scouts of 025: a Frigate is not a
scout any more than a scout is a siege asset.

## Report

Per coastal city: what its list offered, what the queue was set to, the arithmetic, and the turn the
first hull slipped. At the end: the hulls by name and tier, their anchorage, the Dutch raider situation
before and after, and which mission each ship was given. If it expires short of two ships, say which
cities were building what, how many turns each needed, and what took their queue away.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "a navy: frigates, or the tier above them, from the coastal cities" --slug coastal-navy-frigates --instruction @.tmp\t027-instruction.txt --why "build a navy in the coastal cities - frigates, or the next tier the tech tree offers, on the human's instruction" --done-when @.tmp\t027-done.txt --overrides @.tmp\t027-overrides.txt --scope @.tmp\t027-scope.txt --body-file .tmp\t027-body.md --cn @.tmp\t027-cn.md --turns 40 --no-commit
     at: 2026-09-28T19:52:56+08:00
     chinese backup: prompts/tasks/cn/026-coastal-navy-frigates.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 026 --done --turn 261
     at: 2026-09-28T23:36:46+08:00
     status: done at T261
     chinese backup: prompts/tasks/cn/026-coastal-navy-frigates.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 026 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:21+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/026-coastal-navy-frigates.cn.md
-->
