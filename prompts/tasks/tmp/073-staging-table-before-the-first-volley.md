# TEMP TASK 073 - No volley before the staging table exists

added:     2026-10-11 (human instruction: 请重新梳理并确认攻城策略：攻城前要进行战前分析，攻城集结站位，然后攻城，先把城墙打到0，然后占领。尽量减少部队损失)
expires:   turn 301 - 40 turn(s) from T261, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 1 staging table per assault exists - a get_staging_plan call whose output is written into
           the diary with its per-tile FIRE verdicts and the arrival turn of every unit - and no
           volley of that assault was fired before the table existed.
overrides: tasks 062 and 067 and 070 and 072 on the order of work: the staging table is a precondition of the
           first volley, not a document written afterwards. Nothing else changes - the arithmetic
           still gates the assault, the walk-in is still the melee unit move, and no peace is
           proposed.
scope:     the staging step of every assault: the get_staging_plan call, its per-tile FIRE verdicts, the
           unit-to-tile assignment, the arrival turns, and the diary record of all four.

## Why this file exists

Measured on this match, turns 245 to 257: get_target_report was called twice, and get_staging_plan was called ZERO times,
while 43 attacks were ordered. The analysis happened; the staging did not. Phase 2 of the four phases in
prompts/tactics/06-assault-composition-and-fire.md is therefore the phase that is being skipped in practice.

## The rule

1. Before the first volley of any assault, call get_staging_plan on the target tile and write its output into the diary.
It prints one row per unit: where it is, the tile it goes to, the path cost, the arrival turn, and - on a shooter row -
whether that tile can actually FIRE, or FIRE? , or NO LINE OF SIGHT naming the blocker.
2. The table is the answer to three questions and none of them may be answered by memory: which tile each unit takes (never two
on one), which turn it arrives, and whether it can shoot from there.
3. Fill the farthest firing tile first, each shooter at its OWN range. A gun that stands two tiles out when it could fire
from three has volunteered to take the city strike for nothing.
4. The walk-in plan is part of this table: name the melee unit that will take the city and whether it is holding its
movement for that turn, per task 072.
5. If the table says the assault opens later than the arithmetic assumed, the arithmetic is what changes - not the table.
6. Re-run it after any capture, reinforcement or withdrawal that changes who is in the ring.

## What this does not change

The pre-war analysis still comes first and still gates the assault. The fire is still concentrated on one target per turn.
The walls are still broken before the centre pool is ground down, and the city is still taken by a melee move. This file adds
the one step the record shows was being skipped.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "No volley before the staging table exists" --slug staging-table-before-the-first-volley --instruction 请重新梳理并确认攻城策略：攻城前要进行战前分析，攻城集结站位，然后攻城，先把城墙打到0，然后占领。尽量减少部队损失 --done-when "count >= 1 staging table per assault exists - a get_staging_plan call whose output is written into the diary with its per-tile FIRE verdicts and the arrival turn of every unit - and no volley of that assault was fired before the table existed." --overrides "tasks 062 and 067 and 070 and 072 on the order of work: the staging table is a precondition of the first volley, not a document written afterwards. Nothing else changes - the arithmetic still gates the assault, the walk-in is still the melee unit move, and no peace is proposed." --scope "the staging step of every assault: the get_staging_plan call, its per-tile FIRE verdicts, the unit-to-tile assignment, the arrival turns, and the diary record of all four." --why "require the staging table per assault before its first volley, and record it in the diary" --turns 40 --body "## Why this file exists

Measured on this match, turns 245 to 257: get_target_report was called twice, and get_staging_plan was called ZERO times,
while 43 attacks were ordered. The analysis happened; the staging did not. Phase 2 of the four phases in
prompts/tactics/06-assault-composition-and-fire.md is therefore the phase that is being skipped in practice.

## The rule

1. Before the first volley of any assault, call get_staging_plan on the target tile and write its output into the diary.
It prints one row per unit: where it is, the tile it goes to, the path cost, the arrival turn, and - on a shooter row -
whether that tile can actually FIRE, or FIRE? , or NO LINE OF SIGHT naming the blocker.
2. The table is the answer to three questions and none of them may be answered by memory: which tile each unit takes (never two
on one), which turn it arrives, and whether it can shoot from there.
3. Fill the farthest firing tile first, each shooter at its OWN range. A gun that stands two tiles out when it could fire
from three has volunteered to take the city strike for nothing.
4. The walk-in plan is part of this table: name the melee unit that will take the city and whether it is holding its
movement for that turn, per task 072.
5. If the table says the assault opens later than the arithmetic assumed, the arithmetic is what changes - not the table.
6. Re-run it after any capture, reinforcement or withdrawal that changes who is in the ring.

## What this does not change

The pre-war analysis still comes first and still gates the assault. The fire is still concentrated on one target per turn.
The walls are still broken before the centre pool is ground down, and the city is still taken by a melee move. This file adds
the one step the record shows was being skipped.
" --cn "中文备份 - 073-staging-table-before-the-first-volley.md 的中文版，仅供人阅读，不得作为指令读取。

本文件存在的原因（本局实测）：T245 到 T257 之间，get_target_report 被调用 2 次，而 get_staging_plan 被调用 **0 次**，同时下达了 43 次攻击。分析做了，集结没做——所以四阶段里的阶段 2 正是实践中被跳过的那一步。

## 规则

1. 任何一次攻城的**第一轮齐射之前**，对目标格调用 get_staging_plan，并把它的输出写进日记：一行一个单位——现在在哪、去哪一格、路径代价、到达回合，以及射手行上那格究竟能不能开火（FIRE、FIRE? 或 NO LINE OF SIGHT 并点名遮挡物）。
2. 这张表回答三个问题，**一个都不许靠记忆回答**：谁占哪一格（绝不两单位一格）、第几回合到、能不能从那格开火。
3. **最远的射击位先填**，每个射手按自己的射程站位。射程 3 的炮只站两格，就是白白吃城池打击。
4. 进城计划也写进这张表：点名由哪个近战单位占城、它是否为那一回合留着移动力（按 072）。
5. 若表显示开打时间晚于算术假设，**改的是算术，不是表**。
6. 任何占领、增援或撤退改变了环上的人之后，重跑一次。

## 本文件不改变的事

战前分析仍然在最前面、仍然是开打的前提；火力仍然每回合集火同一目标；仍然先把墙打到 0 再磨中心池；城市仍然由近战移动占领。本文件只补上记录显示被跳过的那一步。
"
     at: 2026-10-11T00:56:12+08:00
     chinese backup: prompts/tasks/cn/073-staging-table-before-the-first-volley.cn.md
-->
