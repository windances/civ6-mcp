# TEMP TASK 058 - Assemble the siege corps and take Venice: analysis, staging, then fire

added:     2026-10-09 (human instruction: 新任务：调集攻城军团攻打威尼斯，注意战前分析，集结站位和攻城策略实施。)
expires:   turn 462 - 20 turn(s) from T442, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 1 city named Venice in get_cities under China, with >= 4 shooters having fired on the turn
           it fell and one garrison unit left in it
overrides: the general builder and economy dispatch order for the units the corps needs, and the standing rule
           that a war that cannot be won is not started: this task runs tactics/07 first and reports
           a refusal with numbers if the gates fail
scope:     locating Venice and its suzerain, the pre-war gates on its tile, assembling the establishment, the
           staging plan for its ring and the fire that takes it; no ram, no tower, no peace

## The instruction (verbatim, 2026-10-08)

"新任务：调集攻城军团攻打威尼斯，注意战前分析，集结站位和攻城策略实施。"

Three phases, in this order, and the human named all three: **pre-war analysis** (`tactics/07`),
**assembly and staging** (`tactics/04`, `get_staging_plan`), **execution** (`tactics/06`, fire).
Do not skip to the third one - an army in the right shape with the target still in fog has no
analysis to make.

## 1. Pre-war analysis - Gate 0 first, and Venice is a city-state

**Find it before you plan anything.** Venice is a **city-state**, not a rival civ's city, so the
first questions are different from a normal war:

- `get_city_states` - is Venice on the list, who is its **suzerain**, and **are we**? Attacking a
  city-state we are suzerain of **throws away the suzerainty and every envoy** we have in it; if that
  is the trade, say so in the diary in one line rather than discovering it after the declaration.
- A suzerain can be a civ with a **defensive pact** (`get_diplomacy` shows them): that is the "who
  else joins" gate, and it decides whether the corps must be split.
- `get_target_report(venice_x, venice_y)` runs the first three gates in one call and works in fog: it
  returns the tile and the city on it (walls, city centre pool, the garrison, defence strength), the
  enemy units within three tiles, and the staging plan with its per-tile `FIRE` / `NO LINE OF SIGHT`
  verdicts, saying whether the tile is `visible`, `revealed` or `fog`.
- Then the arithmetic `tactics/07` asks for: **can we take it, in how many turns, at what cost, and
  can we hold it.** If the answer is "no", the task is to say so with the numbers, not to bleed the
  corps - "打不赢的攻城战不开打" is a standing instruction.

## 2. Assembly and staging - the establishment, then the table

- **Establishment** (`tactics/01`): siege **1-3 by arithmetic**, melee 2, anti-cavalry 1, ranged 4,
  cavalry 1, recon 1. A ram or a tower is **never** built, never fielded (human instruction
  2026-09-30: 不生产也不使用撞锤/攻城塔) - a ram the empire already owns stays a garrison.
- **`get_staging_plan(target)` builds the table** from the game's own pathfinding: distinct tiles,
  the conflicts named, the turn the assault opens, and on each shooter's row whether that tile can
  actually fire. **Fill the farthest firing tile first** (human instruction 2026-10-08: 远程部队攻击位置
  优先按射程最大来安排 - a unit with range 3 or 4 fires from outside the city's 2-tile strike and takes
  no retaliation), never two units on one tile, name the corridor.
- **Melee and anti-cavalry go adjacent** - they are the only units that can take the city - and the
  guns stay behind them at their own range, per `tactics/05`.
- If the corps is not assembled yet, `get_reinforcements(target)` says which turn each unit still in
  a queue reaches the rally and which roles nothing covers; use it to name the opening turn.

## 3. Execution - fire, then take, then keep

- Every shooter fires the turn it is in position (`unit_action(action="attack", ...)`); the
  `end_turn` result's `SIEGE FIRE: n/m` and `SIEGE PROGRESS` are the numbers to read, never the
  immediate reply. A **siege unit cannot attack units** - if a defender steps out, ranged and melee
  handle it.
- **Melee takes the city** when the pool is empty, and the capture is resolved with
  `city_action(city_id, "keep")` (the run log labels it `resolve_city_capture`) or the turn will not
  end. An ungarrisoned new city flips - leave one unit in it (`one-garrison-per-city`).
- No peace, ever (the directive's rule, and the tool refuses it anyway). A city-state that is taken
  is taken.

## Done when

`count == 1` city named Venice in `get_cities` under China, with `>= 4` shooters having fired on the
turn it fell, and one garrison unit in it. Report the three phases' numbers: the pre-war verdict and
its turn cost, the staging table's opening turn, and the fire count that took the pool down.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Assemble the siege corps and take Venice: analysis, staging, then fire" --instruction 新任务：调集攻城军团攻打威尼斯，注意战前分析，集结站位和攻城策略实施。 --done-when "count == 1 city named Venice in get_cities under China, with >= 4 shooters having fired on the turn it fell and one garrison unit left in it" --overrides "the general builder and economy dispatch order for the units the corps needs, and the standing rule that a war that cannot be won is not started: this task runs tactics/07 first and reports a refusal with numbers if the gates fail" --scope "locating Venice and its suzerain, the pre-war gates on its tile, assembling the establishment, the staging plan for its ring and the fire that takes it; no ram, no tower, no peace" --why "take the city-state the file names with the pre-war analysis, the staging table and the fire the doctrine asks for" --turns 20 --cn @.tmp/task058-cn.txt --body @.tmp/task058-body.txt
     at: 2026-10-09T04:48:01+08:00
     chinese backup: prompts/tasks/cn/058-assemble-the-siege-corps-and-take-venice-analysis-staging-then-fire.cn.md
-->
