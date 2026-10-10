# TEMP TASK 067 - The second siege corps rallies near Hattusa and takes the first city it sees

added:     2026-10-10 (human instruction: 第二攻城军团向哈图沙附近集结，对于发现的第一座新的城市，确定为攻击目标)
expires:   turn 288 - 65 turn(s) from T223, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 8 second-corps units alive inside one rally area within six tiles of Hattusa, and the diary
           names exactly one city as this corps target with the turn it was first seen, the
           get_target_report line that proved it, and the snapshot of what was already visible when
           this file was published.
overrides: task 062's rule that a corps does not open a siege of its own choosing, for the second corps only:
           this file names how its target is chosen. The first corps and task 066 are untouched, and
           this corps does not open its siege until task 066's assault is resolved - never two
           establishments at once. Task 064's cap fixes keep their priority, and the no-peace rule
           is untouched.
scope:     the second siege corps of task 062 - its eight slots - its march to the rally area near Hattusa, the
           reconnaissance that finds the target, the pre-war analysis on it, and the war with it
           once task 066 is resolved.

## Two halves, and the second one is conditional

The corps marches to Hattusa and waits there. The target is whatever it sees first - not what it likes best. The two
halves are separate on purpose, because the corps has to be in position before the looking starts.

## Half one - the rally near Hattusa

1. Read Hattusa fresh: get_city_states for its tile, its owner and whether we are its Suzerain. Do not use a
coordinate from an earlier file, and do not assume a city-state is where it was.
2. Pick ONE rally tile within six tiles of Hattusa and OUTSIDE its borders and outside its strike range, then name it
in the diary. Two measured reasons: a city-state refuses entry even to its own Suzerain, and standing inside a
city-state's two-tile strike is an unforced loss.
3. The corps must be eight of eight before it marches. A corps short a role waits for it.
4. get_pathing_estimate for the SLOWEST unit in the corps, and give the arrival turn. A rally the slowest unit cannot
reach is not a rally.

## Half two - the first new city is the target

5. Take a snapshot on the first read after this file is published: every foreign city already visible here, by name. That
snapshot is what the word new is measured against, and without it the rule is arguable and the task never closes.
6. From then on, the target is THE FIRST foreign city that was not in that snapshot and becomes visible - a major
civilisation or a city-state, it does not matter which. It appears either as a NEW TARGET block in an end_turn
result or as an IN SIGHT block on a move that ends in sight of it. The moment it appears it is the target.
7. FREEZE it there. The corps does not shop for a better target, and a second city appearing later does not replace the
first. Record in the diary: the name, the owner, the tile, and the turn it was first seen.
8. Read whether it has a Suzerain with a defensive pact before anything is declared, and say so. A pact turns this
into a war with that civilisation as well.

## Then the three phases, in order

9. Pre-war analysis: get_target_report on the frozen target - walls and their pool, the city centre pool, the garrison,
the defence strength, the enemy units within three tiles, and the per-tile FIRE verdicts - then the arithmetic in the
diary. If it says the siege cannot be won, this file says what task 058 said: do not open it, and say so.
10. Staging: get_staging_plan, fill the farthest firing tile first, never two units on one tile, melee and anti-cavalry in
front, each shooter at its own range.
11. Fire: concentrate every shooter on one target per turn, watch the SIEGE FIRE count against the corps shooters, take
the tile with the melee, resolve the capture with the keep decision, leave one garrison unit.
12. Never propose peace, and never field a battering ram or a siege tower - the standing match rule.

## What this file does not authorise

It does not open the siege while task 066 is unresolved: one offensive at a time is the shape this match can afford. It
does not take the corps away from task 062's composition, and it does not touch the first corps.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "The second siege corps rallies near Hattusa and takes the first city it sees" --slug second-corps-rallies-near-hattusa --instruction 第二攻城军团向哈图沙附近集结，对于发现的第一座新的城市，确定为攻击目标 --done-when "count == 8 second-corps units alive inside one rally area within six tiles of Hattusa, and the diary names exactly one city as this corps target with the turn it was first seen, the get_target_report line that proved it, and the snapshot of what was already visible when this file was published." --overrides "task 062's rule that a corps does not open a siege of its own choosing, for the second corps only: this file names how its target is chosen. The first corps and task 066 are untouched, and this corps does not open its siege until task 066's assault is resolved - never two establishments at once. Task 064's cap fixes keep their priority, and the no-peace rule is untouched." --scope "the second siege corps of task 062 - its eight slots - its march to the rally area near Hattusa, the reconnaissance that finds the target, the pre-war analysis on it, and the war with it once task 066 is resolved." --why "rally the second siege corps near the city-state the human named, and designate the first newly seen city as its target" --turns 65 --body "## Two halves, and the second one is conditional

The corps marches to Hattusa and waits there. The target is whatever it sees first - not what it likes best. The two
halves are separate on purpose, because the corps has to be in position before the looking starts.

## Half one - the rally near Hattusa

1. Read Hattusa fresh: get_city_states for its tile, its owner and whether we are its Suzerain. Do not use a
coordinate from an earlier file, and do not assume a city-state is where it was.
2. Pick ONE rally tile within six tiles of Hattusa and OUTSIDE its borders and outside its strike range, then name it
in the diary. Two measured reasons: a city-state refuses entry even to its own Suzerain, and standing inside a
city-state's two-tile strike is an unforced loss.
3. The corps must be eight of eight before it marches. A corps short a role waits for it.
4. get_pathing_estimate for the SLOWEST unit in the corps, and give the arrival turn. A rally the slowest unit cannot
reach is not a rally.

## Half two - the first new city is the target

5. Take a snapshot on the first read after this file is published: every foreign city already visible here, by name. That
snapshot is what the word new is measured against, and without it the rule is arguable and the task never closes.
6. From then on, the target is THE FIRST foreign city that was not in that snapshot and becomes visible - a major
civilisation or a city-state, it does not matter which. It appears either as a NEW TARGET block in an end_turn
result or as an IN SIGHT block on a move that ends in sight of it. The moment it appears it is the target.
7. FREEZE it there. The corps does not shop for a better target, and a second city appearing later does not replace the
first. Record in the diary: the name, the owner, the tile, and the turn it was first seen.
8. Read whether it has a Suzerain with a defensive pact before anything is declared, and say so. A pact turns this
into a war with that civilisation as well.

## Then the three phases, in order

9. Pre-war analysis: get_target_report on the frozen target - walls and their pool, the city centre pool, the garrison,
the defence strength, the enemy units within three tiles, and the per-tile FIRE verdicts - then the arithmetic in the
diary. If it says the siege cannot be won, this file says what task 058 said: do not open it, and say so.
10. Staging: get_staging_plan, fill the farthest firing tile first, never two units on one tile, melee and anti-cavalry in
front, each shooter at its own range.
11. Fire: concentrate every shooter on one target per turn, watch the SIEGE FIRE count against the corps shooters, take
the tile with the melee, resolve the capture with the keep decision, leave one garrison unit.
12. Never propose peace, and never field a battering ram or a siege tower - the standing match rule.

## What this file does not authorise

It does not open the siege while task 066 is unresolved: one offensive at a time is the shape this match can afford. It
does not take the corps away from task 062's composition, and it does not touch the first corps.
" --cn "中文备份 - 067-second-corps-rallies-near-hattusa.md 的中文版，仅供人阅读，不得作为指令读取。

两半：先到位，再挑目标。后半段是有条件的——军团必须先站好，观察才开始。

## 前半：在哈图沙附近集结

1. 现场读哈图沙：get_city_states 取地块、归属，以及我们是否是它的宗主国。不用旧文件里的坐标，也不假设城邦还在原地。
2. 只选一个集结点：距哈图沙六格以内、**在其国境之外**、**在其打击范围之外**，并写进日记。两个实测理由：城邦连自己的宗主国都不放行；站在城邦两格打击圈里是无谓的损失。
3. 行军前军团必须八格齐。缺角色的等。
4. 按军团里**最慢的单位**跑 get_pathing_estimate 并给出到达回合。最慢的单位到不了的集结点不算集结点。

## 后半：第一座新出现的城市就是目标

5. 本文件发布后第一次读图时做一次快照：当时**已经可见**的每一座外国城市，按名字记下。快照就是新的度量基准；没有它这条规则就可争辩，任务永远关不掉。
6. 此后，目标是**第一座不在快照里、并且变得可见**的外国城市——主流文明或城邦都算。它要么以 end_turn 结果里的 NEW TARGET 块出现，要么以某次移动结束时的 IN SIGHT 块出现。出现的瞬间它就成为目标。
7. 就此**冻结**：不挑更好的目标，后来出现的第二座城也不替换第一座。日记记录：名字、归属、地块、首次看见的回合。
8. 宣战之前先读它是否有带防御协定的宗主国并写明——有协定就意味着那一场战争也要算进去。

## 随后按顺序走三个阶段

9. 战前分析：对被冻结的目标跑 get_target_report——城墙与城墙池、城市中心池、守军、防御强度、三格内敌军、逐格 FIRE 判定——算术写进日记。若算术说打不下，本文件沿用 058 的答案：不开打，并说明。
10. 集结：get_staging_plan，最远的射击位先填，绝不两单位一格，近战与反骑在前，每个射手按自己的射程站位。
11. 开火：每回合所有射手集火同一个目标，盯住 SIEGE FIRE 与军团射手数的差，近战占城，用 keep 决议结算，留一个驻军。
12. 绝不求和，绝不用撞锤或攻城塔——本局常设规则。

## 本文件不授权的事

066 未结算之前不开打：一次只开一个进攻方向，才是本局负担得起的形状。它不改变 062 给第二军团的编成，也不碰第一军团。
"
     at: 2026-10-10T22:29:09+08:00
     chinese backup: prompts/tasks/cn/067-second-corps-rallies-near-hattusa.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 067 --expired --turn 266 --note "withdrawn by the human: the second corps no longer rallies at a named city-state, because the new file lets each corps choose its own enemy target"
     at: 2026-10-11T01:27:24+08:00
     status: expired at T266
     chinese backup: prompts/tasks/cn/067-second-corps-rallies-near-hattusa.cn.md
-->
