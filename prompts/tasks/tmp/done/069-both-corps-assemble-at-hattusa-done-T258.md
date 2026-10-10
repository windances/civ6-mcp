# TEMP TASK 069 - Both corps assemble at Hattusa, under strength if that is what they are

added:     2026-10-10 (human instruction: 目前两个军团的部队向哈图沙集结，不满编也执行)
expires:   turn 273 - 45 turn(s) from T228, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 6 units of the two siege corps, at least two of them from each corps, alive inside one
           rally area near Hattusa, with the role-by-role strength each corps marched with recorded
           in the diary.
overrides: tasks 062 and 067 and 068: both corps assemble toward Hattusa now, and under strength is the order
           of the day - the eight-of-eight precondition and the rule that the second corps alone
           goes there are lifted. Nothing else is lifted: the arithmetic still decides whether a
           siege can be won, the three phases still run in order, no battering ram and no siege
           tower, and no peace ever.
scope:     both siege corps of task 062, their march to the rally area near Hattusa and their assembly there
           before any assault, plus the city queues that finish the slots they are short of while
           they march.

## The order

Both corps march to Hattusa and assemble there. Not one of them waiting on the other, and neither waiting to be
whole: a corps that arrives at seven of eight is a corps that is present, and presence is what this move buys.

## One rally area, two rally tiles

1. Read Hattusa fresh: get_city_states for its tile, its owner, and whether we are its Suzerain. A coordinate from an
earlier file, session or note has already been wrong once on this match.
2. Choose ONE rally area within six tiles of Hattusa and OUTSIDE its borders and outside its two-tile strike range.
Two measured reasons: a city-state refuses entry even to its own Suzerain, and standing inside its strike is an unforced
loss.
3. Inside that area, give each corps its OWN rally tile. Two corps, two tiles, never two units on one tile - the area
is shared, the tiles are not.
4. get_pathing_estimate for the SLOWEST unit of each corps and record the arrival turn of each. A rally tile the slowest
unit cannot reach is not a rally tile.

## Under strength is the order

5. State the strength of each corps role by role in the diary before the first move: ranged, melee, fast, and which
slots are short. Then march with what exists.
6. Work around what is missing rather than pretending it is there: with no anti-cavalry the fast pair screens; with fewer
ranged than four, say so and note that the fire takes more turns.
7. Keep the short slots in the queues while the corps march. A corps that starts short should not arrive short for no reason.
8. The first corps comes from the city it has just taken; it does not go back to garrison duty there unless a task says so.

## What happens at the rally

9. Both corps at the rally area is the end of this file. The next move is an assault, and an assault is opened only after
the pre-war analysis passes: get_target_report on the target, the arithmetic in the diary, the staging table with its
per-tile FIRE verdicts, then concentrated fire.
10. Task 067 still decides how the second corps target is chosen - the first foreign city that becomes visible and was not in
the snapshot. The first corps may join that fight; two corps on one city is allowed now.
11. Never propose peace. Never field a battering ram or a siege tower.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Both corps assemble at Hattusa, under strength if that is what they are" --slug both-corps-assemble-at-hattusa --instruction 目前两个军团的部队向哈图沙集结，不满编也执行 --done-when "count >= 6 units of the two siege corps, at least two of them from each corps, alive inside one rally area near Hattusa, with the role-by-role strength each corps marched with recorded in the diary." --overrides "tasks 062 and 067 and 068: both corps assemble toward Hattusa now, and under strength is the order of the day - the eight-of-eight precondition and the rule that the second corps alone goes there are lifted. Nothing else is lifted: the arithmetic still decides whether a siege can be won, the three phases still run in order, no battering ram and no siege tower, and no peace ever." --scope "both siege corps of task 062, their march to the rally area near Hattusa and their assembly there before any assault, plus the city queues that finish the slots they are short of while they march." --why "march both siege corps to the rally area near the city-state the human named, under strength, on the human instruction" --turns 45 --body "## The order

Both corps march to Hattusa and assemble there. Not one of them waiting on the other, and neither waiting to be
whole: a corps that arrives at seven of eight is a corps that is present, and presence is what this move buys.

## One rally area, two rally tiles

1. Read Hattusa fresh: get_city_states for its tile, its owner, and whether we are its Suzerain. A coordinate from an
earlier file, session or note has already been wrong once on this match.
2. Choose ONE rally area within six tiles of Hattusa and OUTSIDE its borders and outside its two-tile strike range.
Two measured reasons: a city-state refuses entry even to its own Suzerain, and standing inside its strike is an unforced
loss.
3. Inside that area, give each corps its OWN rally tile. Two corps, two tiles, never two units on one tile - the area
is shared, the tiles are not.
4. get_pathing_estimate for the SLOWEST unit of each corps and record the arrival turn of each. A rally tile the slowest
unit cannot reach is not a rally tile.

## Under strength is the order

5. State the strength of each corps role by role in the diary before the first move: ranged, melee, fast, and which
slots are short. Then march with what exists.
6. Work around what is missing rather than pretending it is there: with no anti-cavalry the fast pair screens; with fewer
ranged than four, say so and note that the fire takes more turns.
7. Keep the short slots in the queues while the corps march. A corps that starts short should not arrive short for no reason.
8. The first corps comes from the city it has just taken; it does not go back to garrison duty there unless a task says so.

## What happens at the rally

9. Both corps at the rally area is the end of this file. The next move is an assault, and an assault is opened only after
the pre-war analysis passes: get_target_report on the target, the arithmetic in the diary, the staging table with its
per-tile FIRE verdicts, then concentrated fire.
10. Task 067 still decides how the second corps target is chosen - the first foreign city that becomes visible and was not in
the snapshot. The first corps may join that fight; two corps on one city is allowed now.
11. Never propose peace. Never field a battering ram or a siege tower.
" --cn "中文备份 - 069-both-corps-assemble-at-hattusa.md 的中文版，仅供人阅读，不得作为指令读取。

## 命令

两个军团都向哈图沙集结。不是一支等另一支，也不是等满编：七格到位的军团就是到位的军团，而这次移动买到的正是「在场」。

## 一个集结区，两个集结点

1. 现场读哈图沙：地块、归属，以及我们是否其宗主国。旧文件、旧会话或笔记里的坐标在本局已经错过一次。
2. 选一个集结区：距哈图沙六格以内、在其国境之外、在其两格打击范围之外。两个实测理由：城邦连宗主国都不放行；站在其打击圈里是无谓的损失。
3. 区内给每个军团各自的集结点。两个军团、两个点，绝不两单位一格——区域共享，点不共享。
4. 按各军团最慢的单位跑 get_pathing_estimate，并记录各自的到达回合。最慢单位到不了的点不算点。

## 不满编也执行

5. 第一次移动之前，在日记里按角色报出两个军团各自的兵力：远程、近战、高机动，缺哪一格。然后用现有的兵力出发。
6. 缺什么就绕开什么，而不是假装它在：没有反骑就让高机动那对做屏护；远程不足四个就明说，并注明开火需要更多回合。
7. 行军期间把缺的那几格留在队列里。开局就不满编的军团，不该无缘无故地满编到达。
8. 第一军团从它刚拿下的城出发；除非另有任务，它不回那座城做驻军。

## 到达之后

9. 两军团在集结区就位，是本文件的终点。下一步是攻城，而攻城只在战前分析通过之后才开始：get_target_report、算术写进日记、逐格 FIRE 判定的集结表，然后集火。
10. 第二军团的目标仍由 067 决定——第一座在快照之外变得可见的外国城市。第一军团可以加入那场战斗；现在允许两个军团打同一座城。
11. 绝不求和。绝不用撞锤或攻城塔。
"
     at: 2026-10-10T22:48:39+08:00
     chinese backup: prompts/tasks/cn/069-both-corps-assemble-at-hattusa.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 069 --done --turn 258 --note "both siege corps have assembled at the rally area near Hattusa, confirmed by the human"
     at: 2026-10-11T00:41:12+08:00
     status: done at T258
     chinese backup: prompts/tasks/cn/069-both-corps-assemble-at-hattusa.cn.md
-->
