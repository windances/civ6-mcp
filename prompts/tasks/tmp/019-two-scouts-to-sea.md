# TEMP TASK 019 - two Scouts to sea: find the civilizations nobody has met

added:     2026-09-27 (human instruction: 派遣2个侦察兵出海，探索更多文明，30个回合探索任务自动结束，回归默认策略)
expires:   turn 250 - thirty turns from T220, the turn the match stands on (`.civ6-mcp-data/heartbeat.json`
           reads `turn 220` and the newest save holds T220), so the count comes from the clock and not
           from the calendar of any other task. A hard stop: on T250 move this file to
           `done/019-two-scouts-to-sea-expired-T250.md` whatever the map looks like, record in the
           diary's `tooling` line where the two Scouts stood and what they had seen, and let the default
           strategy resume with no residue. If the `done when:` holds earlier, retire it in that turn as
           `019-two-scouts-to-sea-done-T<turn>.md`.
done when: **two units of the Scout line are alive, each on a water tile** (`COAST` or `OCEAN` in
           `get_map_area`, which is what 出海 means here; `UNIT_SCOUT`, or its upgrade `UNIT_RANGER`) **and
           >= 1 major civilization is newly met** - at T220 `get_diplomacy` listed four living majors as
           `not met` (Georgia, Sumer, Phoenicia, India) against one met (the Netherlands), so the
           `not met` line count reads **<= 3**, i.e. **>= 1 new civilization met**. **Pin that baseline
           on the first turn**: read `get_diplomacy`, record the `not met` count in that turn's diary,
           and if it is not 4 then that reading is the baseline and this sentence is the one to correct
           in the diary. Neither half alone is the task: a Scout in port has not gone to sea, and a
           larger revealed map with no new contact has not explored *for civilizations*. Or turn 250,
           whichever comes first.
overrides: **the T220 development plan, and its own closing line.** The T220 10-TURN REVIEW ended the
           conquest half and changed the build order to "housing, the Campus and Industrial lines and
           wonders first, no new units"; this file puts **exactly two units of the Scout line**
           (`UNIT_SCOUT`, or its upgrade `UNIT_RANGER` - the T223 session's pick, because a Scout is
           CS 10 and dies to anything afloat) ahead of that line in up
           to two cities whose queues are not the war front, and authorizes **one replacement for each
           unit lost**, because two afloat is the task. Gold may buy them (the treasury read 208 at
           +34/turn at T220) when production would cost more turns than the gold is worth. It outranks
           queue discipline and the builder backlog **for those two slots only**. **It does not
           override**: the war with the Netherlands (we are already at war - no peace is offered and
           `propose_peace` stays forbidden), `one-garrison-per-city`, `use-your-attacks`, the home
           defence, the research and civic lines, or any other city's queue. It declares no war and
           opens no front - the Scouts are CS 10 and are not a weapon.
scope:     the two Scouts and their replacements, their builds and their orders, and the sea lanes they
           open. Nothing else: no new ships, no third Scout, no army pulled off its post, no attack
           ordered by these two units, and no diplomacy beyond a delegation and `get_deal_options` on
           first contact.

## The position at T220 (a read, not a memory)

| fact | reading | source |
|---|---|---|
| the clock | **T220** | heartbeat `turn 220`; newest save holds T220 |
| map explored | **32%** | T220 diary snapshot, `exploration_pct` |
| Scouts alive | **none** | T220 unit composition: BOMBARD 5, FIELD_CANNON 4, LINE_INFANTRY 3, BUILDER 2, TRADER 7, CROSSBOWMAN 1, CUIRASSIER 1, CAVALRY 1, SPEARMAN 1, GREAT_ENGINEER 1, GREAT_GENERAL 1 - **no SCOUT and no ship** |
| ships | **none** | same composition; the galley killed at (48,21) at T220 was a **barbarian** one, shot by a Field Cannon |
| embark and ocean | **both legal** | the 43-tech read carries `TECH_SAILING`, `TECH_SHIPBUILDING`, `TECH_CELESTIAL_NAVIGATION`, `TECH_CARTOGRAPHY`, `TECH_SQUARE_RIGGING` |
| met major civilizations | **1** - the Netherlands (player 2), at war | T220 `diplo_states`; only that one entry |
| unmet living majors | **4** - Georgia (7 cities, 313), Sumer (9, 499), Phoenicia (5, 343), India (8, 377) | T220 player snapshots; all four alive, all four `not met` |
| gone | Russia (last snapshot T164), Egypt (T217 - eliminated by us at T216) | diary |
| the empire | 19 cities, pop 139, score 799, science ~202, culture ~90, gold 208 (+34/t), faith ~1325, military 838 | T220 diary snapshot |

**Why this instruction is the right one at exactly this point.** The T220 entry's own hypothesis is
this task: *"with 32% of the map explored the remaining four civilizations are almost certainly across
water we would need a fleet for - which the +34 gold/turn and a 119 gold/turn army bill do not fund."*
The conquest half of the directive has run out of targets that are not across an ocean: the war with
the Netherlands cannot be prosecuted because **their six cities have never been seen**, and
`tactics/07` Gate 0 - "a candidate city is actually visible" - cannot be answered for any of them. Two
Scouts are the cheapest instrument that can answer it, and they cost two 30-hammer builds against an
empire producing 19 cities.

## Update at T229 - the file has been picked up, and the instrument is the Scout's upgrade

- **It reached the turn loop**: every planning block from T223 to T229 opens "still under task 019
  (expires T250)", so the `IN FORCE NOW` line did its job.
- **The instrument is two Rangers**, in build at 上海 and 阿拜多斯 and due about **T238** - the Scout's
  upgrade, picked because a Scout at CS 10 dies to the first thing it meets afloat. That is why the
  `done when:` above names the Scout line rather than `UNIT_SCOUT` alone; the intent (two reconnaissance
  units, at sea) is unchanged.
- **The eastern bearing is the productive one, for a second reason now**: the Dutch navy has worked our
  eastern shore since T223 (T224: five of our units damaged and three farms pillaged around 亚历山大 and
  塞纳), which is proof that there is reachable land - a Dutch port - out there. The north-west bearing
  is closed (its barbarian Quadrireme was killed at T227).
- **The clock is the binding constraint**: `exploration_pct` is 33 at T229 against 32 at T220, and the
  two Rangers launch about T238, leaving roughly twelve turns of sailing before T250.
- **This file is the session's only offensive instrument against the Dutch**, whose six cities are still
  unseen; 塞纳's walls and the coastal Field Cannons are the defensive half of that war.

## What to do

1. **Build or buy the two Scouts on the turn this file is first read.** The token is `UNIT_SCOUT`
   (`get_city_production` prints its cost in the queue). Put them in **two different cities** if the
   empire has two whose queues are not the war front, so one queue is not held for two builds, and
   record in the diary which cities and whether gold was used. At T220 the treasury was 208 at
   +33.7/turn, so one purchase is affordable; `purchase_item(city_id, item_type, item_name)` buys it
   instantly and is worth it if the queue would otherwise take more than a handful of turns.
2. **Confirm the two gates before ordering a move, and write the answer in the diary.** A land unit
   cannot embark at all without `TECH_SHIPBUILDING`, and ocean tiles need `TECH_CARTOGRAPHY` - the
   T220 read says both are held, which is why this task is possible now and was not at T83. Re-read
   the tech list; if it disagrees, **that reading is the fact** and this line is the one to correct in
   the diary.
3. **Pick two bearings, never one lane.** Start from `get_strategic_map` (fog per city, unclaimed
   resources) and from the map area around the coastal cities: choose the **two largest fog boundaries
   the empire can reach by water**, on two different coasts if it has two, and send one Scout each. The
   T220 world read is the starting point and not the plan: the east is still opening (Cavalry #5177368
   reached (79,34) at T220), the north-west bearing was held by a Field Cannon, the north coast belongs
   to the city-state 布鲁塞尔 whose suzerain is the Netherlands, and the four unmet majors are, on the
   T220 hypothesis, across water.
4. **Route them like the civilians they are.** `get_map_area` (radius 2) around the destination is
   worth the query: an embarked Scout is CS 10 and dies to anything, and losing one costs the build
   plus its whole voyage. Hills, forest and jungle cost 2 movement and stack; `get_pathing_estimate`
   is the game's own pathfinding - use it rather than assuming a strait is a wall. Two units on one
   tile is illegal, so the two bearings must not converge on the same staging tile. **Two traps this
   session already measured**: a blind `move` can embark a unit with **no warning at all** (T225 - the
   only sign was the destination tile's own yield line, `F:1 P:0 G:1`), and **an embarked land unit
   cannot make a ranged attack** (T225: the shot resolved as `MELEE_ATTACK` and did nothing while the
   unit kept its movement). A Ranger at sea is a passenger, not a shooter - read the destination tile
   before ordering a coastal move.
5. **`automate` is allowed for a Scout and is the sane default, but it is not a reason to stop
   looking.** Read the reveal every turn. A Scout that has been circling, standing still, or walking
   back through ground it already uncovered gets a bearing instead - a direct move, one per call.
6. **Bank the first contact.** On meeting a major civilization send a **delegation (25 gold)**, then
   call `get_deal_options(player_id)`: it hands over their city list with populations, which city is
   their original capital, their strategic and luxury stockpiles and their gold per turn - with no
   open borders, no war, and no Scout reaching anything. That is `tactics/07` Step 0 reconnaissance for
   free, and it is the real prize of this task. Write in the diary: **who, where, on which turn, by
   which Scout, and whether it was a major civilization or a city-state.**
7. **Start nothing with them.** First contact is information: no declaration, no demand, no
   aggression. The directive's rule stands - a war you cannot finish is a war you must not start - and
   the point of finding these four is to know which of them is worth planning against later.
8. **Two afloat at all times.** A Scout lost - to a barbarian galley, to the Dutch at war, or to a
   city-state's borders - is replaced within the next few turns by another `UNIT_SCOUT`, build or gold.
   Record each loss and its cause: a Scout that dies to the same hazard twice is a routing mistake, not
   bad luck.

## What this task is not

- **Not a navy.** No Caravel, Frigate or Ironclad is authorized by this file. If the session believes a
  ship is the better instrument, that is a recommendation for the human and a diary line, not an order
  this file licenses.
- **Not a war and not reconnaissance for one.** No unit fires, no city is attacked, no front is opened
  by these two Scouts.
- **Not a substitute for the directive.** Everything else - the war with the Netherlands, the housing
  fixes, the Campus and Industrial lines, the builder backlog - continues exactly as the T220 plan set
  it out.

## Report when it is done

The `exploration_pct` before (32 at T220) and after; every civilization met, with the turn, the tile,
and which Scout made the contact; what `get_deal_options` revealed for each; which of the four unmet
majors are still unmet and the bearing the next session should try; and the unit ids of the two Scouts
afloat. **On expiry** (T250) report the same numbers plus what blocked it - no ocean route, Scouts lost
and replaced, or the war - and say in the diary that the default strategy resumes.

## Why this is a file and not a turn-check rule

No metric the running server computes carries either half of this task's finish line. The checks file's
rules read metrics the scan already produces (a camp is `IMPROVEMENT_BARBARIAN_CAMP`, a garrison is a
unit on a city tile); "two Scouts are on water tiles" and "a civilization that was `not met` is now
met" are neither. A rule naming a metric the server does not compute reports `un-evaluable` every turn
and nobody can satisfy it, and new rules are staged in `prompts/checks/pending/` until a server
computing their metric is running - so this instruction travels as a file, which the turn loop reads,
until T250 retires it.
