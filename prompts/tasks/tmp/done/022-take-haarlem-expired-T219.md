# TEMP TASK 022 - take Haarlem: locate the Dutch city, analyse it, stage and concentrate fire

added:     2026-09-28 (human instruction: 增加任务：占领哈勒姆)
expires:   turn 288 - 31 turn(s) from T257, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **Haarlem is ours** - the tile at its own (x,y) reads `[CITY_CENTER]` owned by 中国 with one of our
           units standing on it (`hold-what-you-take`), Haarlem appears in `get_cities`, and the
           Netherlands' city count in `get_diplomacy` has fallen by one. If Haarlem turns out to be
           the Dutch original capital, the proof is `get_victory_progress`'s DOMINATION block: it
           reads `荷兰: holds own capital` before and does not after. The diary carries the ledger -
           the four numbers re-read at war and which of them came from a probe attack, the staging
           table with its overrides, the shots per turn and the tile each shot came from, the cost
           paid, and the hold plan. Retire it as `022-take-haarlem-done-T<n>.md` the turn the city
           is ours, or as `-expired-T<n>.md` at the hard stop with where the force stood and what
           blocked it.
overrides: **the human's instruction is the reason of record for this one city.** 占领哈勒姆 was given at the turn
           this file was added (T257), while the standing plan was the science line and 021's Sumer
           expedition; this file puts Haarlem ahead of that plan **for the force and the queues
           named below only**, and the diary records the instruction as the reason rather than
           inventing a strategic one - the same treatment 016 gave 埃里温 and 020 gave 布鲁塞尔. **021
           keeps its expedition**: the units already at sea on the west lane (Bombards #4128794,
           #5636108, #4325376, #4980745, Field Cannons #6291469, #4784149, Line Infantry #4456464,
           #5111819, Pike&Shot #6815776, Cuirassier #6029340, Cavalry #5177368, 圣女贞德) and 021's
           Frigate are **not** recalled, diverted or re-tasked; this file's force is the home slice,
           at most **four new builds**, and gold. **No new war is declared**: the Netherlands is
           already at war (diplomatic state 6), so an attack needs no declaration and no waiting
           turn - the combat engine is already synced - and Sumer stays 021's business and neutral
           here. Gold purchases are authorized for the units this file names (the treasury read 699
           at +89/turn at T254), and any city's queue except 西安's may be used. **It does not
           override**: `one-garrison-per-city`, `use-your-attacks`, the eastern-shore defence of 塞纳
           and 亚历山大, 西安's Rocketry-and-Spaceport line, 021's scope and its own T270 deadline, the
           housing and Sewer line, or the directive's ban on `propose_peace` - the Dutch war still
           has no exit but the capture of its cities.
scope:     Haarlem, its ring, the Dutch units defending it, the route to it, and the force this file names. Not
           the Netherlands' other six cities - each of those is its own decision under the directive
           - not Sumer or anything on 021's west lane, not a city-state, not a barbarian camp, and
           not a third front opened by this file.

## What is known at T254, and the one call nobody has made

| fact | reading | source |
|---|---|---|
| the Netherlands | **7 cities**, score 431, **military 3**, at war with us (diplomatic state 6, grievances -116) | T254 diary snapshot; `diplo_states` |
| their war | **frozen since about T228** - their navy raided our eastern shore at T223-T224 (five units damaged, three farms pillaged) and has not been seen since; the Dutch front has been a phony war for twenty-five turns | T223-T228 diary |
| Haarlem | **never read - not one Dutch city name appears anywhere in the diary** | the whole `diary_china_-1894041591.jsonl`, searched |
| where it can be read | **`get_diplomacy`**: for every civilization we have met it prints `Cities (N): <name> pop <P> (<x>,<y>) walls <W>; ...` and a count of cities still in fog (`src/civ_mcp/narrate.py:805-814`) | Egypt's list was read exactly that way at T213 |
| what that walls figure is | a **static maximum**, not the current wall HP: it read `walls 100` for 诺夫哥罗德 while its walls stood at 0 | T165 (`docs/task-history.md`) |
| the real wall number | comes from the **first melee attack's own result line** - a city tile can print `[fog]` while its whole ring is visible | 016, re-measured at 布鲁塞尔 T235 |

**So Gate 0 begins with a call this session has never made for the Netherlands.** Everything else in
this file is the machinery that 016, 018 and 020 already paid for.

## The force: what 021 took, and what is left at home

021's legion is **at sea** on the west lane (list in `overrides:`) and stays there. From the T254 unit
composition, what this file has to work with is:

| available | notes |
|---|---|
| 1 Bombard, 3 Field Cannons | the siege and ranged half of the home slice; the shooters that are left |
| 1 Line Infantry | the melee the capture needs, plus any garrison that can be spared without breaking `one-garrison-per-city` |
| 2 Rangers, 1 Cavalry | the eyes; the east Ranger is at (82,6), the west one at (30,22) |
| 9 Builders, 10 Traders | not combat units, and not to be thrown at a city |
| gold 699 at +89/turn | enough for a Frigate (1120) inside three turns |

**At most four new builds**, and every one of them must have a stated role before it is queued: a
**naval escort** (read `get_city_production` for the strongest available; a Frigate is affordable by
about T258), **one or two siege or melee units** (upgrade what the tree and the resources allow rather
than building from scratch), and **replacements for losses**. 西安 is the Spaceport city and is not
this file's to spend.

## Gate 0 - reconnaissance (侦察), before any move

1. **`get_diplomacy` for the Netherlands' city list** - Haarlem's coordinate, its population and its
   wall maximum. Write the coordinate down; a coordinate copied from an old diary has already been
   wrong once (`done/001-clear-the-camp-done-T84.md`).
2. **`get_map_area` radius 2 around it** if any of it is in vision: the ring, the terrain, and whether
   there is land on our side of the water.
3. **GROUND gate - land or sea.** The Dutch are across water (their navy reached our eastern shore),
   so the likely answer is a sea leg. If it is sea-only: the **escort leads**, and the train does not
   sail unescorted - "it's critical to accompany embarked land units with a strong naval defense"
   (`manual:883`) - and an embarked land unit cannot make a ranged attack at all (T225). If a land
   route exists, take it and leave the escort at home.
4. **Expect the city to be the whole defence.** Their military is **3**: no field army will come. What
   the approach has to survive is the city's own strike (2 tiles), its walls, and whatever it builds
   while we sail.
5. **Is it their capital?** Read `get_victory_progress`'s DOMINATION block before anything: if Haarlem
   is the Dutch **original** capital, this capture advances Domination and the block is the proof of it
   - record both readings, before and after.

## 战前分析 - the gates (tactics/07), once it is visible

The human's instruction is unconditional, so the analysis does **not** decide whether; it decides
**how**, and it decides what the assault will cost:

1. **The four numbers**, each with the source that produced it: walls / HP pool / garrison (the city
   tile's own unit list, or our own attack list while it is fogged - that is how 布鲁塞尔's Builder
   garrison was found at T235) / ring.
2. **Defenders by class and HP within two tiles**, and the counter for each - and remember a Bombard
   **cannot attack a unit at all**, so any Dutch unit is the Field Cannons' and the melee's work.
3. **The turn count, said out loud from shots that have landed**, not from the plan.
4. **Can we hold it?** A captured Dutch city arrives with an empty queue (an end-turn blocker), low
   loyalty, and Dutch cities around it: a governor or a garrison goes in the turn it falls, and its
   queue is set the same turn (`hold-what-you-take`).
5. **Write the cost down** and, if the numbers say the first wave cannot do it, say what the second
   wave needs - more shooters, or the escort back from 021's lane once that task closes.

## 攻城集结 - the staging, in this order

Run **`get_staging_plan(haarlem_x, haarlem_y)`** and write one row per unit - where it is, its
movement, the one tile it goes to, the `get_pathing_estimate` cost, its arrival turn, its role, and
whether it can fire from there - **before the first `unit_action`**. Calling the tool is not writing
the table. The three staging rules: never two units on one tile, name the corridor, fill the **last**
firing tile first (`prompts/tactics/04-staging-out-of-range.md` step 3b). The six overrides this map
has already measured all still bind:

- a **siege unit posted at d1 is refused** (it fires from d2 and dies at d1, T163);
- **`arrive T+n` does not know our own units jam the corridor** - one move per call, `get_units`
  between them (T159/T161; eight units stopped mid-path at T234);
- **a firing tile is a proposal until a shot from it succeeds** - and a refusal is not a verdict on
  the tile (T194);
- **a shooter that spends its move arriving cannot fire** (`NO_MOVES|Ranged attacks require movement`,
  T236);
- **entering a Zone of Control costs that turn's attack** (T194);
- **a unit id is not durable across an upgrade** - re-read `get_units` after every `upgrade_unit`
  (T200, T234).

## 集火 - the fire order, from the sieges this empire has already fought

1. **Walls first, then the pool.** The wall number comes from the first melee attack's result line.
2. **The melee on d1 is worth a Bombard against walls**: at 布鲁塞尔 a Cavalry attack took **50 points
   off the wall pool and took no retaliation** (T236) - so the screen breaks walls, it is not
   decoration. A **d2 tile is not a d1 tile**: the Cuirassier ordered from (68,30) answered
   `STOPPED_SHORT ... 2 tiles away` while only (69,28)/(69,30) were real d1 (T237).
3. **Every shooter that can bear fires the same turn** (`use-your-attacks`), and the pooled
   `walls:` / `city hp:` fields are the record - the prose beside them is stale even when the numbers
   moved (T236, T237). Re-read the city a call later rather than trusting the immediate reply.
4. **Cut the supply line or the city outheals you**: six hexes, 6/6 cut, or roughly twenty HP a turn
   comes back (T235-T237).
5. **Take it with the d1 unit the turn the pool empties**, resolve it with `city_action` the same turn
   or the turn will not end, and make **one capture attack per tile per turn** - a second attack after
   the flip hits our own city (T216).

## Hold it, and report

Governor or garrison the turn it falls, set its empty queue the same turn, and report: the four numbers
with their sources, the staging table with its overrides, the shots per turn and the tile each came
from, the capture resolution and the tile the capturing unit stood on, the cost in units and turns, the
DOMINATION line before and after if Haarlem is the Dutch capital, and the loyalty reading in the turns
that follow. If it expires, say where the force stood, what Haarlem read, and what blocked it - the
voyage, the walls, or 021's claim on the escort.

## Why this is a file and not a turn-check rule

Every mechanical half already has a rule or a tactic - `siege-train`, `screen-the-siege`,
`mass-on-contact`, `take-the-city`, `hold-what-you-take`, `use-your-attacks`, `finish-the-wounded`,
`cut-the-supply`, and `tactics/07` for the analysis. What no metric carries is **which city is the
objective**: the standing directive is fighting a frozen war and chasing a science victory, and a
named enemy city is a choice that has to travel to the turn loop as a file with the human's instruction
written in it as the reason of record.

**One risk to state plainly**: this is a second overseas front while 021's legion is at sea. What makes
it affordable is the Netherlands' military of **3**. If the two compete for production, gold or the
Frigate, **021 keeps its expedition and this file takes what is left** - the `overrides:` line says so,
and the diary should record which of the two the session chose whenever they collide.

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 022 --done --turn 241
     at: 2026-09-28T22:12:15+08:00
     status: done at T241
     chinese backup: prompts/tasks/cn/022-take-haarlem.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 022 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:18+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/022-take-haarlem.cn.md
-->
