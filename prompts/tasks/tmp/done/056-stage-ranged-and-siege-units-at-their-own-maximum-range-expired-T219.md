# TEMP TASK 056 - Stage ranged and siege units at their own maximum range

added:     2026-10-09 (human instruction: 远程部队攻击位置优先按射程最大来安排，这样减少被攻击风险，比如部分升级后的部队射程4，大于守城部队2的攻击距离。)
expires:   turn 451 - 20 turn(s) from T431, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 lines in prompts/tactics that state range 2 as the placement rule for ranged or siege
           units, and the staging and target tools report a firing verdict computed from each unit's
           own range
overrides: the range 2 placement rule in tactics/05, tactics/04 and tactics/01: a unit with range 3 or 4 fires
           from 3 or 4 tiles, because a city strike reaches only 2
scope:     the placement rule in prompts/tactics, the FIRE verdict in get_staging_plan and get_target_report,
           and the SIEGE FIRE counter in end_turn; not the city's own strike, which is correctly
           range 2

## The instruction (verbatim, 2026-10-08)

"远程部队攻击位置优先按射程最大来安排，这样减少被攻击风险，比如部分升级后的部队射程4，大于守城部队2的攻击距离。"

Position ranged units at their **own maximum range** first. A city strike reaches exactly 2 tiles
(`src/civ_mcp/lua/cities.py:595` - "city attack range is 2"), so a unit with range 3 or 4 that fires
from 3-4 tiles takes **no retaliation at all**. Promotions are the case that makes this concrete: a
Rocket Artillery with Advanced Rangefinding (+1 range) outranges every city it will ever meet, and
the current doctrine parks it inside the strike ring anyway.

## What the doctrine says today, and what it must say instead

Measured, line by line - every one of these has to change:

| File | Today | Instead |
|---|---|---|
| `prompts/tactics/05-formation-and-screening.md:10,11` | `ranged (range 2)`, `siege (range 2)` | the unit's own range, 2 only as the floor |
| `:16` | "**Ranged and siege stand behind them** at range 2" | behind the screen, at the **farthest tile that can fire** |
| `:21` | "Range 2 is where a Catapult belongs, and it is the range it was built for" | true for an unpromoted Catapult; **wrong for anything with +1 range** |
| `:42` | "marks `FIRE`, not ... `NO LINE OF SIGHT` (range 2 without a line ...)" | the `FIRE` test is per unit and per its own range |
| `prompts/tactics/01-unit-production.md:72` | "ranged to fire from range 2" | the farthest firing tile the unit has |
| `prompts/tactics/04-staging-out-of-range.md:392,396` | "inside range 2", `SIEGE FIRE: n/m` | count every unit inside **its own** range |

The rule to write: **fill the farthest firing tile first** (this also replaces "fill the **last**
firing tile first" in `04` step 3b), take a range-2 tile only when the longer ones are occupied,
blocked by line of sight, or do not exist - and keep the melee/anti-cavalry screen adjacent to the
city, because they are the only units that can take it.

## The tool side: measured, and one gap still open

- **`end_turn.py:1669`** frames the whole block as `SIEGE POSTURE (T{turn}) - front line in front,
  siege behind, at range 2:` and **`end_turn.py:1699`** counts `... inside range 2 of the target`.
  That counter therefore **undercounts a promoted unit firing from 3**: the block's own comment at
  `:1686` records a measured case where "one siege unit was inside range 2 while two stood at
  distance **4 and 6** for three turns" - those two were firing or able to fire and were not counted.
- **`cities.py:593,595`** hard-code 2 for the **city's** strike, and that is correct - a city strikes
  at 2. Do not "fix" that one.
- **Still to check (first step of this task):** whether `get_staging_plan` / `get_target_report`
  compute each shooter's own range (`unit:GetRange()` / `AttackRange`) or a constant 2. `spatial.py`
  showed no range handling in a first pass, so find the function that decides `FIRE` / `FIRE?` /
  `NO LINE OF SIGHT` and make it per-unit. Until that is done, the plan a session reads can call a
  perfectly good 3-tile firing position `NO LINE OF SIGHT`.

## Done when

`count == 0` lines in `prompts/tactics/` that state range 2 as the placement rule for ranged or siege
units, the staging and target tools report a firing verdict computed from the unit's own range, and
the `SIEGE FIRE` counter no longer says "inside range 2". Record the measured before/after on one
promoted unit - its range, the tile it was moved to, and whether the city could reach it.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Stage ranged and siege units at their own maximum range" --instruction 远程部队攻击位置优先按射程最大来安排，这样减少被攻击风险，比如部分升级后的部队射程4，大于守城部队2的攻击距离。 --done-when "count == 0 lines in prompts/tactics that state range 2 as the placement rule for ranged or siege units, and the staging and target tools report a firing verdict computed from each unit's own range" --overrides "the range 2 placement rule in tactics/05, tactics/04 and tactics/01: a unit with range 3 or 4 fires from 3 or 4 tiles, because a city strike reaches only 2" --scope "the placement rule in prompts/tactics, the FIRE verdict in get_staging_plan and get_target_report, and the SIEGE FIRE counter in end_turn; not the city's own strike, which is correctly range 2" --why "keep ranged units outside the range the city can answer at, by using the range they actually have" --turns 20 --cn @.tmp/task056-cn.txt --body @.tmp/task056-body.txt
     at: 2026-10-09T02:56:20+08:00
     chinese backup: prompts/tasks/cn/056-stage-ranged-and-siege-units-at-their-own-maximum-range.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py --root . retire 056 --done --turn 441
     at: 2026-10-09T04:42:48+08:00
     status: done at T441
     chinese backup: prompts/tasks/cn/056-stage-ranged-and-siege-units-at-their-own-maximum-range.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 056 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:35+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/056-stage-ranged-and-siege-units-at-their-own-maximum-range.cn.md
-->
