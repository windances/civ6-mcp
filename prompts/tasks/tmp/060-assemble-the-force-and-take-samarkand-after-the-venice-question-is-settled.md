# TEMP TASK 060 - Assemble the force and take Samarkand, after the Venice question is settled

added:     2026-10-09 (human instruction: 新任务：调集部队拿下撒马尔罕。)
expires:   turn 469 - 25 turn(s) from T444, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 1 city named Samarkand in our cities, with >= 4 shooters having fired on the turn it fell,
           one garrison unit left in it, and the diary saying which target went first and why
overrides: nothing: the corps is shared with task 058, so this file says when Samarkand's turn comes, not that
           Venice is dropped - the two are serialised by the pre-war analysis
scope:     finding Samarkand and its suzerain, the pre-war gates on its tile, the assembled establishment, the
           staging plan for its ring and the fire that takes it; no ram, no tower, no peace

## The instruction (verbatim, 2026-10-08)

"新任务：调集部队拿下撒马尔罕。"

Same three phases as Venice, and the same order: **pre-war analysis** (`tactics/07`), **assembly and
staging** (`tactics/04` + `get_staging_plan`), **execution** (`tactics/06`). Samarkand is a
**city-state**, so its first questions are the city-state questions.

## One thing this file settles before anything else: the corps is shared with Venice

`058` is taking Venice with the same establishment. **Two sieges, one corps.** Do not pretend
otherwise:

- `get_city_states` and `get_target_report` on both targets, then **say in the diary which goes
  first and why** - the closer one, the weaker one, or the one whose suzerain is the smaller risk.
- **Serialise them** unless the corps is genuinely two establishments deep (`get_reinforcements` on
  both shows what is actually available and what nothing covers). The measured lesson from this match
  is that one offensive plus one screen is the affordable shape; two simultaneous sieges is how a
  corps gets eaten.
- Neither task outranks the other: this one says *when it is Samarkand's turn*, not *drop Venice*.

## 1. Pre-war analysis

- **Find it**: `get_city_states` - Samarkand's tile, its **suzerain** (is it us?), its military
  strength. Attacking a city-state we are suzerain of throws away the suzerainty and every envoy in
  it; if the suzerain is another civ with a **defensive pact** (`get_diplomacy`), that civ joins - run
  that gate before the declaration, not after.
- `get_target_report(samarkand_x, samarkand_y)` runs the first three gates in one call and works in
  fog: walls, city centre pool, garrison, defence strength, the enemy units within three tiles, and
  the staging plan with its per-tile `FIRE` / `NO LINE OF SIGHT` verdicts.
- Then the arithmetic: **can we take it, in how many turns, at what cost, can we hold it.** The
  march is part of the cost - a city-state on the far side of the map is a logistics problem before
  it is a siege. If the answer is no, report the numbers and do not start it.

## 2. Assembly and staging

- **Establishment** (`tactics/01`): siege 1-3 by arithmetic, melee 2, anti-cavalry 1, ranged 4,
  cavalry 1, recon 1. **No ram, no tower** - never built, never fielded (human instruction
  2026-09-30: 不生产也不使用撞锤/攻城塔).
- **`get_staging_plan(target)`**: distinct tiles, named conflicts, the turn the assault opens, and
  per-shooter whether the tile can fire. **Fill the farthest firing tile first** (human instruction
  2026-10-08: 远程部队攻击位置优先按射程最大来安排 - a range-3 or range-4 shooter fires from outside the
  city's 2-tile strike and takes no retaliation). Never two units on one tile.
- **Melee and anti-cavalry go adjacent** - only they can take the city - with the guns behind them at
  their own range (`tactics/05`).
- `get_reinforcements(target)` names the opening turn: which unit reaches the rally when, and which
  role nothing covers. Use it, and **not** a guess, to say when the march is complete.

## 3. Execution

- Fire the turn each shooter is in position; read `SIEGE FIRE: n/m` and `SIEGE PROGRESS` in the
  `end_turn` result, not the immediate reply. A siege unit cannot attack units - a defender that
  steps out is ranged and melee work.
- **Melee takes the city** when the pool is empty; resolve it with `city_action(city_id, "keep")`
  (logged as `resolve_city_capture`) or the turn will not end, and leave **one garrison unit**
  (`one-garrison-per-city`) - a fresh city-state conquest with no garrison flips back.
- **No peace, ever.**

## Done when

`count == 1` city named Samarkand in our cities, with `>= 4` shooters having fired on the turn it
fell, one garrison unit left in it, and the diary saying which target went first and why. Report the
march length, the opening turn of the assault, and the fire count that took the pool down.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Assemble the force and take Samarkand, after the Venice question is settled" --instruction 新任务：调集部队拿下撒马尔罕。 --done-when "count == 1 city named Samarkand in our cities, with >= 4 shooters having fired on the turn it fell, one garrison unit left in it, and the diary saying which target went first and why" --overrides "nothing: the corps is shared with task 058, so this file says when Samarkand's turn comes, not that Venice is dropped - the two are serialised by the pre-war analysis" --scope "finding Samarkand and its suzerain, the pre-war gates on its tile, the assembled establishment, the staging plan for its ring and the fire that takes it; no ram, no tower, no peace" --why "take the second city-state with the same three phases, and settle which of the two sieges the corps does first" --turns 25 --cn @.tmp/task060-cn.txt --body @.tmp/task060-body.txt
     at: 2026-10-09T04:55:53+08:00
     chinese backup: prompts/tasks/cn/060-assemble-the-force-and-take-samarkand-after-the-venice-question-is-settled.cn.md
-->
