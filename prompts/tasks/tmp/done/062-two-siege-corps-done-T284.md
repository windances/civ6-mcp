# TEMP TASK 062 - Two siege corps of eight, wherever they stand

added:     2026-10-11 (human instruction: 组建2个攻城军团，每个军团包含：4个远程部队，2个进程部队，2个高机动部队。按现有部队组建，不足的安排生产。 062任务去掉位置条件。)
expires:   turn 286 - 20 turn(s) from T266, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 2 corps of eight units each - at least four ranged, two melee and two fast in each,
           counting only living units - with the role-by-role roster of both corps written into the
           diary. Where the corps stand is not part of this line.
overrides: its own earlier positional clause: this file used to require both corps to be within three tiles of
           their own rally tile, and that clause is removed. Tasks 069 and 070 ordered the two corps
           into the field, and a corps in the field is never at its rally, so the clause made the
           task unretirable. Nothing else changes - the composition, the build-what-is-missing rule
           and the no-peace rule all stand.
scope:     the empire existing land units, re-assigned by role into the two corps, and the city queues that
           build what the inventory shows missing: four ranged, two melee and two fast per corps.

## What changed

One clause, and it was the clause that mattered: the corps no longer have to be within three tiles of their own rally tile to count as
complete. They were ordered to Hattusa by task 069 and then to take what they find by task 070, and a corps that is taking cities is not a corps
standing at a rally. The old line could never be satisfied by a working army, which is why the task sat three turns from expiry with its purpose
already achieved.

## The finish line now

Two corps of eight, each with at least four ranged, two melee and two fast, counting only living units, with the roster written in the diary role
by role. That is the whole line. Where they stand is not part of it.

## What to do

1. get_units: state the roster of each corps role by role - how many ranged, how many melee, how many fast, and which slots are short. That roster in
the diary is the evidence this task retires on.
2. Fill the shortfall from existing units first. Only what cannot be found in the army is built: one city queue per missing unit, and no queue
taken from task 064 where a cap is firing.
3. A unit counts for a corps once it is alive and assigned, wherever it is on the map - the assignment is a note in the diary, not a march.
4. The exception that still holds: a unit under half strength, or one that is the last garrison of a city we just took, is not a corps unit until it is
replaced or healed. A corps of eight on paper and six in the field is not what this file asks for.
5. Report the two rosters in the diary every turn until both are eight of eight.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --replace --title "Two siege corps of eight, wherever they stand" --slug two-siege-corps --instruction "组建2个攻城军团，每个军团包含：4个远程部队，2个进程部队，2个高机动部队。按现有部队组建，不足的安排生产。 062任务去掉位置条件。" --done-when "count == 2 corps of eight units each - at least four ranged, two melee and two fast in each, counting only living units - with the role-by-role roster of both corps written into the diary. Where the corps stand is not part of this line." --overrides "its own earlier positional clause: this file used to require both corps to be within three tiles of their own rally tile, and that clause is removed. Tasks 069 and 070 ordered the two corps into the field, and a corps in the field is never at its rally, so the clause made the task unretirable. Nothing else changes - the composition, the build-what-is-missing rule and the no-peace rule all stand." --scope "the empire existing land units, re-assigned by role into the two corps, and the city queues that build what the inventory shows missing: four ranged, two melee and two fast per corps." --why "complete the two siege corps as rosters of eight, with the rally-tile position clause removed" --turns 20 --body "## What changed

One clause, and it was the clause that mattered: the corps no longer have to be within three tiles of their own rally tile to count as
complete. They were ordered to Hattusa by task 069 and then to take what they find by task 070, and a corps that is taking cities is not a corps
standing at a rally. The old line could never be satisfied by a working army, which is why the task sat three turns from expiry with its purpose
already achieved.

## The finish line now

Two corps of eight, each with at least four ranged, two melee and two fast, counting only living units, with the roster written in the diary role
by role. That is the whole line. Where they stand is not part of it.

## What to do

1. get_units: state the roster of each corps role by role - how many ranged, how many melee, how many fast, and which slots are short. That roster in
the diary is the evidence this task retires on.
2. Fill the shortfall from existing units first. Only what cannot be found in the army is built: one city queue per missing unit, and no queue
taken from task 064 where a cap is firing.
3. A unit counts for a corps once it is alive and assigned, wherever it is on the map - the assignment is a note in the diary, not a march.
4. The exception that still holds: a unit under half strength, or one that is the last garrison of a city we just took, is not a corps unit until it is
replaced or healed. A corps of eight on paper and six in the field is not what this file asks for.
5. Report the two rosters in the diary every turn until both are eight of eight.
" --cn "中文备份 - 062-two-siege-corps.md 的中文版，仅供人阅读，不得作为指令读取。

## 改了什么

只改了一条，而且是关键的那一条：军团**不再需要位于各自集结点三格以内**才算满编。它们已被 069 派往哈图沙、又被 070 派去各自拿城，**正在攻城的军团不会是站在集结点上的军团**。旧完成线对一支正在作战的部队永远无法成立——所以这个任务在目的已达成的情况下，却只剩三回合就要过期。

## 现在的完成线

两个军团各八人、各至少 4 远程 + 2 近战 + 2 高机动、**只计存活单位**，并把**按角色的名册**写进日记。就这些；**它们站在哪里不算数**。

## 要做的事

1. get_units：按角色报出两个军团各自的名册——几个远程、几个近战、几个高机动、缺哪格。**这份名册就是本任务结账的依据。**
2. 先用现有部队补缺；只有军队里找不到的才生产：每个缺编单位一个队列，且**在 064 踩线的城市里不抢队列**。
3. 单位只要活着并被指派，就算编入——不论它在地图哪里；指派是日记里的一条记录，不是一次行军。
4. 仍然成立的例外：半血以下的单位、以及刚拿下的城里最后一个驻军，在补充或治好之前**不算**军团单位。纸面八人、战场六人，不是本文件要的东西。
5. 每回合在日记里报两份名册，直到两个军团都满编八人。
"
     at: 2026-10-11T01:14:20+08:00
     chinese backup: prompts/tasks/cn/062-two-siege-corps.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 062 --done --turn 284
     at: 2026-10-11T12:14:41+08:00
     status: done at T284
     chinese backup: prompts/tasks/cn/062-two-siege-corps.cn.md
-->
