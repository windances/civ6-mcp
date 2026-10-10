# TEMP TASK 023 - the Dutch campaign: take every city the Netherlands holds, with the army we have

added:     2026-09-28 (human instruction: 新增任务：利用现有部队，组建攻城兵团，占领所有荷兰的城市)
expires:   turn 272 - fifty-four turns from T218, the position this branch was rolled back to (read from
           the save on 2026-09-28): assemble and upgrade 2-4 turns, then 6-12 turns per city for the
           **six** the Netherlands holds, the span 021 taught us to measure. A hard stop, and the
           arithmetic is the point: 021 expired because its deadline was set without measuring the
           distance. **This is the one number here that is inherited rather than read** - re-count it on
           the first full turn of the campaign from the real coordinates and say in the diary whether
           T272 still holds.
done when: **the Netherlands holds no city.** The proof is `get_diplomacy`'s line for 荷兰 (player 2): it lists
           `Cities (N): name pop P (x,y) walls W` for every city it holds, so the task ends when
           that line names none - and, if the last one falls, when the Netherlands no longer appears
           among the living players. Each city taken is additionally proved on its own tile:
           `[CITY_CENTER]` owned by 中国 with one of our units standing on it, the city in
           `get_cities`, its queue set the same turn and a governor or garrison in place. If any
           Dutch city turns out to be their original capital, the DOMINATION block of
           `get_victory_progress` is the proof of that half. The diary carries the ledger per city:
           the four numbers and which of them came from a probe, the staging table with its
           overrides, the shots per turn and the tile each shot came from, the cost, the loyalty
           reading after the capture, and the turn it fell. Retire it as
           `023-dutch-siege-corps-done-T<n>.md` the turn the last city is ours, or as
           `-expired-T<n>.md` at the hard stop with the cities taken, the cities left, and the
           measured per-city rate.
overrides: **the human's instruction, and the army we already have.** 占领所有荷兰的城市 is the instruction; the file is
           the reason of record for the campaign and the diary records the instruction rather than
           inventing a strategic one, as 016, 020 and 022 did for their cities. **No new unit is
           authorized by this file**: the corps is drawn from the army that exists (table below),
           and the only production it touches is what was already queued for the `siege-train` and
           `ranged-mass` checks. **Gold upgrades of existing units are authorized and expected** -
           an Artillery is 155g under 职业军队, it is the same unit, and `siege-train` stays short
           until it happens. **The Spaceport line is not this file's to raid**: 西安's production,
           its Industrial Zone buildings and its power stay the victory plan, and the science and
           housing queues stay theirs. **The west lane stays a screen** (the directive's standing
           orders put 俄罗斯 first and hold that lane): the units watching it are not pulled
           west-to-east for this campaign; a counter-strike there is its own decision. Two overseas
           expeditions at once caused the T265 bankruptcy on the run that was rolled back - gold hit
           zero and two units were disbanded - so this file runs **one** offensive and one screen,
           never two offensives. **It does not override**: `one-garrison-per-city`,
           `use-your-attacks`, `hold-what-you-take`, the directive's ban on `propose_peace` (the
           Dutch war still ends only by taking their cities), or the policies the hold depends on.
           Every city taken is resolved with `city_action keep` - the instruction says 占领, not raze.
scope:     Every Dutch city, in the order the campaign reaches them, their rings, the units defending them, the
           route to each, and the corps this file names. Not the Netherlands' cities once taken
           (they are ours and `hold-what-you-take` owns them), not 俄罗斯 or the west lane, not a
           city-state, not a barbarian camp, and not a second offensive anywhere.

## This file was written on runs that were rolled back - read every state line that way

Two rollbacks stand behind this file. The corps census and the two sieges below were measured while the
match stood at **T281 of a run that no longer exists** (that run took 哈勒姆 at T271 and 布鲁塞尔 at
T237). Then the attempt that started from **this same T218 save** played to T301 and was rolled back to
T218 as well - and *that* attempt is where the readings in the next table come from; it is also the one
that took 布鲁塞尔, at T224.

So at the position this branch now holds: 哈勒姆 is theirs, **布鲁塞尔 is an independent city-state
again**, and the Dutch hold **six** cities. What carries over is the **instruction**, the **shape of the
corps**, the **deadline accounting**, and the **lessons** (the six staging overrides, the d1 shot,
walls-versus-pool, the stale post-combat prose). What does **not** carry over is any statement about
whose city something is, or what a check reads. Every line below that comes from a run other than this
one is marked `[rolled-back run]` or `[previous attempt]` and is evidence, not state - the state is
whatever this turn's own reads say, and **the first job is to read them**.

## What has been read at this position - by the attempt that was rolled back

| fact | reading | source |
|---|---|---|
| the Netherlands | **6 cities**, military **176** vs our **824** (0.2x), at war with us: `荷兰 (威廉明娜) — WAR (-35) **AT WAR** [player 2]` | `get_diplomacy` at T220, the previous attempt - re-read it |
| the only Dutch city seen | **乌得勒支 - pop 6, (74,23), walls 200** - and five more still in fog: the line reads `Cities (6): 乌得勒支 pop 6 (74,23) walls 200 + 5 in fog` | `get_diplomacy` at T220, the previous attempt |
| 哈勒姆 | **theirs.** The T271 capture is the rolled-back run's record (`done/022-take-haarlem-done-T271.md`); nothing of theirs has fallen at this position | this position's `get_diplomacy` list |
| a forward base on their side | **none yet.** 布鲁塞尔 was taken at T224 on the previous attempt, the capture move coming from (69,28) - but at this position it is a city-state again, so **the first city taken here becomes the base** | T224 log of the previous attempt; task 024 |
| our treasury and size | **289g at +16/t**, 69 units, 19 cities | `get_game_overview` at T219, the previous attempt - re-read it |
| their coast battery | `[rolled-back run]` a Bombard working (70,19)-(70,20) that killed five of our units, fired on by our Battleship and by Haarlem's walls | that run's T276-T281 diary |
| our corps' standards | **re-read this turn** - `siege-train` and `ranged-mass` are the two checks that decide the shape of the corps. The values the other run recorded (2/3 and 2/4) are that run's, at T281 | this turn's `end_turn` result |
| their interior | **never read at this position** - one city is visible and five are not, so the target list, the distances and the deadline are all still measurements to make | `get_diplomacy` at T220, the previous attempt |

**Gate 0 is one call nobody has made for the whole campaign: `get_diplomacy`'s list for 荷兰.**
It prints every city the Netherlands holds as `name pop P (x,y) walls W` (`src/civ_mcp/narrate.py:805-814`),
which is how the one city above was found after the earlier `6 (all in fog)`. **Write that list into
the diary on the first turn of the campaign, with each city's distance from our nearest base** - it is
the target list *and* the measurement the deadline is re-counted from. Then keep at least one unit
moving through their fog every turn, because a city we have not seen is a city whose distance, walls
and garrison we cannot price.

## The corps, drawn from the army we already have (利用现有部队)

The table is **a census taken at T281 of the rolled-back run**; re-count it from `get_units` this
session. The shape is the point, not the numbers: a siege train, a ranged mass, melee that can take a
city, a fast arm, and the naval battery.

| unit | count then | role in the corps |
|---|---|---|
| BOMBARD | 2 | the siege train - **upgrade both to Artillery** (155g each under 职业军队) and `siege-train` clears |
| FIELD_CANNON | 3 (+1 building, 10t) | the ranged mass; the fourth clears `ranged-mass` |
| INFANTRY | 2 | the melee that takes cities and, `[rolled-back run]` measured at 布鲁塞尔, breaks walls as well as a Bombard |
| LINE_INFANTRY | 2 | second melee / garrison pool for what is taken |
| CAVALRY + CUIRASSIER | 1 + 1 | the fast arm: reconnaissance, the supply hexes, and a capture unit that arrives first |
| AT_CREW | 1 | anti-cavalry cover for the train |
| BATTLESHIP + FRIGATE | 1 + 1 | **the naval battery**: `[rolled-back run]` a Frigate alone took 哈勒姆's 100 walls to 0 in six turns from d2; the Battleship is the strongest shooter we own |
| RANGER | 1 | eyes ahead of the column |
| GREAT_GENERAL | 2 | **keep both alive, do not activate them**: +5 CS and +1 movement to land units in range, passively |

No new unit is built for this (see `overrides:`). What the corps needs beyond the army is **gold**:
the two Artillery upgrades and, if a city proves to be inland, nothing else - a march is measured
before it is ordered, not paid for.

## What the two sieges measured - and which run measured them

1. **Coastal and near beats inland and far, by a lot.** `[rolled-back run]` 哈勒姆 - five tiles away,
   coastal, walls 100 - fell in **thirteen turns from Gate 0**, six of them the naval wall phase.
   `[rolled-back run]` 021's target was thirty to forty tiles inland and its artillery was still 13-22
   tiles out when its thirty-three-turn window expired, with `get_staging_plan` reporting nine units
   `TOO FAR` and "0 shooter(s) in position". Neither of those runs is this one; the lesson is the
   distance, and this branch's distances are unread.
2. **The naval battery is a first-class siege asset.** `[rolled-back run]` walls 100 -> 0 under Frigate
   fire alone (T261-T266, ~22 a turn). A city on the coast of a sea we control is the cheap kind of
   target.
3. **A siege unit firing from d1 works**: `[rolled-back run]` 哈勒姆's Bombard resolved
   `RANGE_ATTACK ... dist:1`. The old note that d1 is refused is corrected - what is true is that a
   **d2 tile is not a d1 tile for melee** (`[rolled-back run]` T237: `STOPPED_SHORT ... 2 tiles away`).
4. **Walls are permanent; the pool is not.** A city heals about twenty points a turn, so the ring is
   the landing party's first job: `[rolled-back run]` 哈勒姆's supply line was cut 3/6 and still healed
   while it was fired on.
5. **The four numbers are three until a probe** - a city's own tile can stay `[fog]` while its whole
   ring is visible. But **we are already at war with the Netherlands** (state above), so our own
   attack list reads the garrison for free, which is how 布鲁塞尔's was found on this branch.
6. **The post-combat prose is stale; the pooled `walls:` / `city hp:` fields are the record**, and a
   later read is the fact.
7. **`[previous attempt]` The nearest worked example is 布鲁塞尔, taken at T224 on the attempt this
   position was rolled back from**, with the capture move from (69,28) - the tile north of the centre,
   one tile out - after the train assembled from this same T218 save. Read its ledger in the diary
   (`docs/task-history.md` has the prose record) before planning the next city: it is the most recent
   siege of this map, and the city is a city-state again here.

## Gate 0, per city, as the corps arrives

`get_map_area` radius 3 for the ring and the supply hexes; the four numbers with the source named;
`get_staging_plan(city_x, city_y)` and the written table **before the first `unit_action`**. The six
overrides this map has already paid for live in `prompts/tactics/04-staging-out-of-range.md` step 3b-1 -
read them there rather than restating them, and note that **the d1 note is corrected**: a siege unit
firing from d1 works (`[rolled-back run]`, `RANGE_ATTACK ... dist:1`), while a d2 tile is not a d1 tile
for the capture move.

## Sequencing - and it is a proposal until the list is read

**Nearest and coastal first**, one city at a time, and **each captured city becomes the next forward
base**: there is none yet - 布鲁塞尔 was the previous attempt's base and is a city-state again at this
position, so the first city taken here is the one to garrison, queue and heal from (read its walls and
its strike the turn it falls rather than assuming either: a captured city's walls come down with the
capture). 乌得勒支 (74,23) is the one city we have seen, walls 200 and pop 6, and it is therefore the
default first target - but write the planned order from the actual `(x,y)`
coordinates and the measured distances, not from this file's guess, and re-count the deadline from it
(below).

## 集结 and 集火

Run `get_staging_plan(x, y)` and write the table - one row per unit: where it is, its movement, the one
tile it goes to, the `get_pathing_estimate` cost, its arrival turn, its role, whether it can fire from
there. Then, in order:

1. **Cut the supply ring** on the approach - the pool heals about twenty a turn otherwise.
2. **Walls first.** The naval battery and the d2 shooters work them; the wall number comes from the
   first melee attack's result line when the tile is fogged.
3. **The d1 melee is worth a Bombard against walls** (`[rolled-back run]` T236: 50 off the wall pool,
   no retaliation) and takes the city the turn the pool empties - `city_action keep` the same turn or
   the turn will not end, and **one capture attack per tile per turn**.
4. **Concentrate**: every shooter that can bear fires the same turn; nothing sits idle with a legal
   attack.
5. **Re-read the city a call later** rather than trusting the immediate reply, and keep the pooled
   fields as the ledger.

## Hold - the half this position has not started

**Nothing of theirs has been held here yet**: the previous attempt held 布鲁塞尔 from T224 until it was
rolled back, so its loyalty line is the one that attempt watched and this one has to start watching from
the first capture. `[rolled-back run]` 哈勒姆 at T281 read **loyalty 44/100 at -0.5 a turn**, with a
governor (维克多), an Infantry garrison and the `殖民地办事处` policy already in place - that is the
shape of the treatment, not this position's numbers. Every city this campaign takes gets it
**the turn it falls**: `city_action keep`, its queue set, a governor or a garrison, and the anti-flip
policy where it fits. A city that flips back is a campaign loss to report with its numbers, not a
detail to leave out. **The durable answer to Dutch loyalty pressure is another Dutch city**, which is
also this instruction.

## The deadline is a measurement, not a hope

`expires: turn 272` is fifty-four turns from T218: assembly and the two upgrades 2-4, then **6-12 turns
per city** measured from `[rolled-back run]` 哈勒姆's thirteen (six of them the naval wall phase) for
the **six** cities the Netherlands holds here. **021 expired because its deadline was set without
measuring the distance**, and the lesson is written into the task-history for exactly this reason. So:
**on the first full turn of the campaign, after the city list is read, re-count this deadline from the
real coordinates and say in the diary whether T272 still holds.** If it does not, report the measured
per-city rate and the cities left - do not slide the deadline silently.

## Report when it is done

For the campaign: the city list as read, the order taken and why, and the turn each fell. For each
city: its four numbers with their sources, the staging table with its overrides, the shots per turn and
the tile each came from, the capture resolution, the cost, and the loyalty reading after the capture.
At the end: whether the Netherlands still exists, what `get_victory_progress`'s DOMINATION block reads
before and after if their original capital was among them, and the state of the treasury and the two
checks. If it expires: the cities taken, the cities left, and the measured per-city rate.

## Why this is a file and not a turn-check rule

`siege-train` and `ranged-mass` are the rules and they decide the shape of the corps; `tactics/07` owns
the analysis and `tactics/06` the fire. What no rule carries is **the campaign itself** - that every
Dutch city is the objective, that the corps is drawn from the existing army rather than built, that the
west lane stays a screen, and that the deadline is a measurement to be re-counted rather than a date to
be trusted.

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 023 --done --turn 259
     at: 2026-09-28T23:29:58+08:00
     status: done at T259
     chinese backup: prompts/tasks/cn/023-dutch-siege-corps.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 023 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:19+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/023-dutch-siege-corps.cn.md
-->
