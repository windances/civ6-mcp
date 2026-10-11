# TEMP TASK 074 - Each siege corps picks its own enemy city and takes it

added:     2026-10-11 (human instruction: 两个攻城军团，各自挑选敌国目标城市，并占领)
expires:   turn 318 - 40 turn(s) from T278, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 2 enemy cities have been captured since this file was published, at least one by each siege
           corps, and the diary carries one get_target_report reading for each city taken, written
           on or before the turn its first volley was fired.
overrides: its own earlier discovery-shaped text: the picking is still each corps own, but the first three
           calls of every assault are now named, because the previous thirteen turns produced zero
           get_target_report readings and zero captures while the queues and the unit sweep did the
           work. The four phases, the staging table, the taking unit arithmetic, the concentration
           of fire, no battering ram, no siege tower and no peace all stand.
scope:     both siege corps - the target report on their candidates, the city each one chooses, the staging
           table and the siege - plus the city queues that finish the slots they are short of.

## Measured, before anything else

The log of the last session, turns 266 to 278: 39 city production changes, 50 units swept by one skip call, 5 research changes,
and - of the calls this task is about - ZERO get_target_report readings and ZERO captures. The corps sat while the home front was
adjusted. That is what this revision fixes: the first calls are named, so there is nothing to administrate around.

## The three calls, in this order, this turn

1. get_target_report on the nearest enemy city to EACH corps. Two calls if the two corps have two candidates. Both readings go into the
diary the same turn: the walls and their pool, the city centre pool, the garrison, the defence strength, the enemy units within three tiles.
2. Choose, and say which and why: the nearest city whose numbers the corps can break. Distance decides among the winnable, never over them.
3. get_staging_plan on the chosen city, and write the table in the diary: row per unit, the tile, the arrival turn, and whether that tile can FIRE.

Only then does the first volley count. A volley fired without those three calls in the diary is not this file being executed - it is the same
administration the log above recorded.

## Then the four phases

4. The walls to zero, then the city centre pool to zero, then the walk-in: a melee unit moves onto the city tile. Ranged and siege never capture.
5. The taking unit attack counts as pool damage and the walk-in needs movement left - the choice is written out in task 072.
6. Resolve with the keep decision, leave one garrison unit, and the corps moves to its next target. Never a battering ram, never a siege tower,
never peace.

## The record, per city

The two get_target_report readings, the reason the city was chosen, the staging table with its FIRE verdicts, the SIEGE FIRE count per turn, the
turn it fell, the garrison left behind, and which corps took it.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --replace --title "Each siege corps picks its own enemy city and takes it" --slug each-corps-picks-its-own-city --instruction 两个攻城军团，各自挑选敌国目标城市，并占领 --done-when "count >= 2 enemy cities have been captured since this file was published, at least one by each siege corps, and the diary carries one get_target_report reading for each city taken, written on or before the turn its first volley was fired." --overrides "its own earlier discovery-shaped text: the picking is still each corps own, but the first three calls of every assault are now named, because the previous thirteen turns produced zero get_target_report readings and zero captures while the queues and the unit sweep did the work. The four phases, the staging table, the taking unit arithmetic, the concentration of fire, no battering ram, no siege tower and no peace all stand." --scope "both siege corps - the target report on their candidates, the city each one chooses, the staging table and the siege - plus the city queues that finish the slots they are short of." --why "name the first three calls of each assault so the corps cannot be administered around" --turns 40 --body "## Measured, before anything else

The log of the last session, turns 266 to 278: 39 city production changes, 50 units swept by one skip call, 5 research changes,
and - of the calls this task is about - ZERO get_target_report readings and ZERO captures. The corps sat while the home front was
adjusted. That is what this revision fixes: the first calls are named, so there is nothing to administrate around.

## The three calls, in this order, this turn

1. get_target_report on the nearest enemy city to EACH corps. Two calls if the two corps have two candidates. Both readings go into the
diary the same turn: the walls and their pool, the city centre pool, the garrison, the defence strength, the enemy units within three tiles.
2. Choose, and say which and why: the nearest city whose numbers the corps can break. Distance decides among the winnable, never over them.
3. get_staging_plan on the chosen city, and write the table in the diary: row per unit, the tile, the arrival turn, and whether that tile can FIRE.

Only then does the first volley count. A volley fired without those three calls in the diary is not this file being executed - it is the same
administration the log above recorded.

## Then the four phases

4. The walls to zero, then the city centre pool to zero, then the walk-in: a melee unit moves onto the city tile. Ranged and siege never capture.
5. The taking unit attack counts as pool damage and the walk-in needs movement left - the choice is written out in task 072.
6. Resolve with the keep decision, leave one garrison unit, and the corps moves to its next target. Never a battering ram, never a siege tower,
never peace.

## The record, per city

The two get_target_report readings, the reason the city was chosen, the staging table with its FIRE verdicts, the SIEGE FIRE count per turn, the
turn it fell, the garrison left behind, and which corps took it.
" --cn "中文备份 - 074-each-corps-picks-its-own-city.md 的中文版，仅供人阅读，不得作为指令读取。

## 先说实测

上一个会话 T266 到 T278 的日志：39 次城市生产调整、一次 skip 扫掉 50 个单位、5 次研究变更——而本任务真正相关的调用是：**get_target_report 0 次、占领 0 次**。军团在场上待着，内政被调来调去。这次修订就是针对这件事：把**头几个调用点名**，让会话没有可绕的余地。

## 三个调用，按这个顺序，本回合就做

1. 对**每个军团各自最近的**敌国城市跑 get_target_report（两个军团有两个候选就跑两次）。**两行读数当回合写进日记**：城墙与城墙池、城市中心池、守军、防御强度、三格内敌军。
2. 选定，并写明选谁、为什么：挑**算术打得下的最近那座**。距离只在打得下的范围里做决定，绝不越过它。
3. 对选定的城跑 get_staging_plan，把表写进日记：一行一个单位、去哪格、第几回合到、那格能不能 FIRE。

**只有做完这三个调用，第一轮齐射才算数。**没有这三份记录的齐射，不是本文件被执行，而是上面日志里记的那种行政。

## 然后走四个阶段

4. 先把墙打到 0，再把中心池打到 0，然后走进城：**由近战单位移动到城格**。远程与攻城永远不能占领。
5. 占城部队的攻击计入池伤害，进城需要留有移动力——选择写在 072 里。
6. 用 keep 决议结算、留一个驻军，军团转向下一个目标。绝不用撞锤、绝不用攻城塔、绝不求和。

## 每座城的记录

两行 get_target_report 读数、选它的理由、逐格 FIRE 的集结表、每回合 SIEGE FIRE 计数、陷落回合、留下的驻军、以及是哪支军团拿下的。
"
     at: 2026-10-11T11:22:35+08:00
     chinese backup: prompts/tasks/cn/074-each-corps-picks-its-own-city.cn.md
-->
