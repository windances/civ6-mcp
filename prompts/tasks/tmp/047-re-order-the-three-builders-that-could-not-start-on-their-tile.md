# TEMP TASK 047 - Re-order the three builders that could not start on their tile

added:     2026-10-06 (human instruction: 建造者走到目标地块后，如果把 2 点移动力用完了（moves 0/2），当天不能再下 improve —— 引擎会回
           `CANNOT_IMPROVE|Builder has no moves remaining this turn`。2026-10-06 人类确认：这种情况不要在同回合
           重复尝试；下一回合先把它们重新开工，再按 get_builder_tasks 继续派工。)
expires:   turn 365 - 30 turn(s) from T361, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: a MINE at (61,35), a CAMP at (28,9) and a FARM at (79,18) as read by get_map_area, or
           get_builder_tasks no longer names any of the three as a 0-tile idle builder
overrides: nothing: it re-issues work the builder-task list already ranks, and changes no queue and no unit
           beyond those three builders
scope:     three builders only: the ones that walked onto their target tile and could not start that turn

## Why this exists

Measured on this match at T360: of 21 builder orders, five started an improvement the same turn, seven
are still walking (`STOPPED_MID_PATH (moves exhausted)`), and **three were refused** -

```
id:12648465  IMPROVEMENT_MINE  -> Error: CANNOT_IMPROVE|Builder has no moves remaining this turn
id:13172742  IMPROVEMENT_CAMP  -> Error: CANNOT_IMPROVE|Builder has no moves remaining this turn
id:13238329  IMPROVEMENT_FARM  -> Error: CANNOT_IMPROVE|Builder has no moves remaining this turn
```

Each of the three had just walked onto the tile it was sent to and spent both movement points; Civ VI
does not let a builder with 0 movement start an improvement, so the tile stayed bare and the UI showed
the builder standing still.

## What to do next turn

1. Read `get_builder_tasks` first, as every turn. Those three tiles appear with a **0-tile** idle
   builder, which is the signal that the builder is already standing on the tile and only the order is
   missing.
2. Re-issue the three `improve` orders before dispatching anything new: `MINE` at (61,35), `CAMP` at
   (28,9), `FARM` at (79,18). A builder standing on its tile with 2/2 moves starts the improvement the
   same turn, so these land immediately.
3. Then carry on down the list as usual (URGENT > HIGH > NORMAL, nearest idle builder).

## The rule this is standing in for

Before ordering `improve`, look at the builder's `moves` in the `get_units` read:

- **`moves >= 1`** - order the improvement now; it starts this turn.
- **`moves 0`** - do not order it. Either it is mid-walk (leave it; it will arrive with movement next
  turn) or it is already on the tile (the next turn's `get_builder_tasks` names it at 0 tiles). An
  `improve` on 0 movement is a guaranteed refusal, and three of them per turn is context spent on a
  call that cannot do anything.

## Done when

The three tiles carry their improvement - a `MINE` at (61,35), a `CAMP` at (28,9) and a `FARM` at
(79,18) as read by `get_map_area` - or `get_builder_tasks` no longer names any of the three as a task
with a 0-tile idle builder.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Re-order the three builders that could not start on their tile" --instruction @.tmp/task047-instruction.txt --done-when "a MINE at (61,35), a CAMP at (28,9) and a FARM at (79,18) as read by get_map_area, or get_builder_tasks no longer names any of the three as a 0-tile idle builder" --overrides "nothing: it re-issues work the builder-task list already ranks, and changes no queue and no unit beyond those three builders" --scope "three builders only: the ones that walked onto their target tile and could not start that turn" --why "re-order the builders that arrived with no movement and could not start their improvement" --expires-turn 365 --body @.tmp/task047-body.txt --cn @.tmp/task047-cn.txt --no-commit
     at: 2026-10-06T22:16:30+08:00
     chinese backup: prompts/tasks/cn/047-re-order-the-three-builders-that-could-not-start-on-their-tile.cn.md
-->
