# TEMP TASK 053 - Fire the first volley: Tsageri, this turn

added:     2026-10-08 (human instruction: 查看攻城策略是否被执行 -> 结论是没有执行；发布一份点名目标城与第一个动作的任务，让会话本回合就开火)
expires:   turn 391 - 3 turn(s) from T388, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: get_target_report(19,45) was run this turn, >= 4 Rocket Artillery fired at the city on that tile,
           and the Rocket Artillery east of x=49 are no longer carrying [SENTRY] or [HOLD]
overrides: the drift into in-turn administration: this outranks promotions, policy, congress and governor
           chores until the first volley has been fired; it does not change the goal of task 050
scope:     the six Rocket Artillery and three Machine Guns in front of the Georgian front, the Modern AT with
           them, and the eight Rocket Artillery still east of x=49; one target city, one volley,
           three calls; no new war, no peace, no change to the build queues

## Why this file exists

Measured on turn 387-388 of this match: the session that took over held the tuner for 21 tool calls
and issued **no `unit_action` at all** - no move, no attack, not one of the eight guns in the rear
was advanced either. What it did was administration: 4 `get_unit_promotions`, 3 `promote_unit`,
`get_policies`, `get_world_congress`, `get_governors`, `get_pending_trades`, `get_diplomacy`,
`get_tech_civics`, then `end_turn`. The turn advanced; the war did not.

The reason is the shape of the standing tasks: 050 names a goal (take every remaining city) and 051
names a condition (no unit left asleep), and **neither names a first action**. This file is that
first action. It is deliberately narrow: one target, one volley, three calls.

## The position it starts from (read it again, do not trust these numbers)

Georgia holds seven cities, all walled except one; its army is 91 against our 2829:

| City | pop | tile | walls |
|---|---|---|---|
| Tsageri | 8 | (19,45) | 100 |
| **Akhalkalaki** | 3 | (35,44) | **none** |
| Omalo | 3 | (25,45) | 400 |
| Tskhumi | 9 | (28,43) | 400 |
| Telavi | 3 | (28,39) | 400 |
| Batumi | 19 | (25,33) | 400 |
| Gori | 11 | (32,42) | 400 |

Our massed guns sit in front of them: six Rocket Artillery at (18,40), (20,40), (22,39), (23,40),
(23,43), (24,42), with three Machine Guns and a Modern AT on (21,38). Eight more Rocket Artillery are
still east of x=49 with `[OPERATION]` set, and they are the half task 051 was written for.

## Do this, in this order, this turn

1. **`get_target_report(19,45)`** - Tsageri, walls 100 and population 8: the cheapest wall in the
   theatre and the closest to the massed guns. It answers the tile, the walls, the garrison, the
   defence strength and the firing tiles in one call. Read the `FIRE` / `NO LINE OF SIGHT` column
   before moving anything.
2. **`get_staging_plan(19,45)`** - the staging table for that city. Fill the **last** firing tile
   first, never two units on one tile, and take a tile the reply marks `FIRE` (a tile at distance 2
   with the line blocked is not a firing position).
3. **Fire.** `unit_action(action="attack", target_x=19, target_y=45)` for every Rocket Artillery that
   the plan puts in a firing tile. `SIEGE FIRE: n/m` in the `end_turn` result is the count that
   matters; do not read progress off the immediate reply alone.
4. **Keep the rear moving.** Every Rocket Artillery still east of x=49 moves west this turn - one
   tile is enough; `[OPERATION]` is set on them and staying still is the failure 051 was published
   to stop. If any of them still carries `[SENTRY]` or `[HOLD]`, that order wakes it.
5. **Then** the turn's administration - promotions, policy, congress, governors. **A promotion is
   never instead of an attack** (manual: `EXPENDING XPS`; a promotion consumes the whole turn), so
   the shots come first.

## What this file does not change

`050` still owns the goal and `051` still owns the rear half. This file only says which city to hit
first and that the first volley happens **this turn**. No new war, no peace, no change to the
builds in the queues.

## Done when

`get_target_report(19,45)` was run this turn, >= 4 of our Rocket Artillery fired at Tsageri, and the
Rocket Artillery east of x=49 are no longer carrying `[SENTRY]` or `[HOLD]`. Then retire this file
and let 050 carry the war: the next target is whichever of the seven is nearest the guns after
Tsageri falls, with Akhalkalaki (35,44) the only one needing no wall work at all.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Fire the first volley: Tsageri, this turn" --instruction "查看攻城策略是否被执行 -> 结论是没有执行；发布一份点名目标城与第一个动作的任务，让会话本回合就开火" --done-when "get_target_report(19,45) was run this turn, >= 4 Rocket Artillery fired at the city on that tile, and the Rocket Artillery east of x=49 are no longer carrying [SENTRY] or [HOLD]" --overrides "the drift into in-turn administration: this outranks promotions, policy, congress and governor chores until the first volley has been fired; it does not change the goal of task 050" --scope "the six Rocket Artillery and three Machine Guns in front of the Georgian front, the Modern AT with them, and the eight Rocket Artillery still east of x=49; one target city, one volley, three calls; no new war, no peace, no change to the build queues" --why "fire the first volley of the siege that is already staged, against the city the file names" --turns 3 --body @.tmp/task053-body.txt --cn @.tmp/task053-cn.txt
     at: 2026-10-08T02:29:17+08:00
     chinese backup: prompts/tasks/cn/053-fire-the-first-volley-tsageri-this-turn.cn.md
-->
