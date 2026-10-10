# TEMP TASK 070 - Each siege corps takes what it finds, one city at a time

added:     2026-10-10 (human instruction: 两个攻城军团，对于发现的敌国城市，各自行动，发现一个占领一个，注意遵循攻城策略)
expires:   turn 297 - 60 turn(s) from T237, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 4 enemy cities have been taken since this file was published, each with its three phases
           recorded in the diary - the gates that were run, the staging table with per-tile FIRE
           verdicts, and the SIEGE FIRE count per turn - and on no turn has a corps sat idle while a
           winnable enemy city was visible to it.
overrides: tasks 062 and 067 and 069 on target selection: each corps now chooses from the enemy cities it
           discovers, and takes them one at a time, rather than waiting for one named target. Task
           069 still says where they start. Nothing else is lifted - the arithmetic still decides
           whether a siege can be won, the three phases still run in order, task 064 keeps priority
           over queues, no battering ram and no siege tower, and no peace ever.
scope:     both siege corps of task 062, the reconnaissance that finds enemy cities worth taking, the sieges
           each opens in turn, and the city queues that finish the slots they are short of while
           they campaign.

## A standing order, not a single target

The two corps stop waiting for a target to be handed to them. Each one looks around itself, picks the enemy city it can
actually take, takes it, and looks again. Discovery and capture alternate, one city at a time.

## Independent, which is the point

1. The two corps work different axes. Read the map from each corps own position and list the enemy cities in reach, with
owner, walls, and whether we are at war with that owner already.
2. The corps do not stack on one city unless there is nothing else worth doing. Two corps on one target is allowed and was
used at the Hattusa rally, but two corps taking two cities at once is what this file is for.
3. Each corps picks its OWN next target. The pick is the nearest enemy city whose arithmetic works out, not the nearest one
period.

## The doctrine is the whole point of the instruction

4. Every city gets the same three phases, in order, and none of them is skipped because a corps is in a hurry: the pre-war
analysis (get_target_report - walls and their pool, the city centre pool, the garrison, the defence strength, the enemy units
within three tiles, the per-tile FIRE verdicts), then the staging table (get_staging_plan, farthest firing tile first, each
shooter at its own range, never two units on one tile, melee and anti-cavalry in front), then concentrated fire - every
shooter on one target each turn, with the SIEGE FIRE count read against the shooters present.
5. A city whose arithmetic says it cannot be won is NOT attacked. Park it, name it in the diary, and say which single unit
or which wall change would make it winnable. This is the human standing rule and it outranks the standing order to keep
taking cities.
6. A city-state Suzerain with a defensive pact is read before anything is declared, and named, because that turns one war
into two.
7. After a capture: resolve it with the keep decision, leave one garrison unit in it, and the corps moves on. Standing still
after a win is how a campaign turns into a garrison.
8. Keep the short slots in the queues while the corps campaign: a corps that starts short should not stay short.

## The record

Per city, in the diary: the gates and what they answered, the staging table with arrival turns and FIRE verdicts, the SIEGE
FIRE count per turn, the turn it fell, and the garrison left behind. A city taken without that record is a city taken by luck,
and this file does not count it.

## Never

Never propose peace. Never field a battering ram or a siege tower. Never open a siege the arithmetic says is lost.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Each siege corps takes what it finds, one city at a time" --slug each-corps-takes-what-it-finds --instruction 两个攻城军团，对于发现的敌国城市，各自行动，发现一个占领一个，注意遵循攻城策略 --done-when "count >= 4 enemy cities have been taken since this file was published, each with its three phases recorded in the diary - the gates that were run, the staging table with per-tile FIRE verdicts, and the SIEGE FIRE count per turn - and on no turn has a corps sat idle while a winnable enemy city was visible to it." --overrides "tasks 062 and 067 and 069 on target selection: each corps now chooses from the enemy cities it discovers, and takes them one at a time, rather than waiting for one named target. Task 069 still says where they start. Nothing else is lifted - the arithmetic still decides whether a siege can be won, the three phases still run in order, task 064 keeps priority over queues, no battering ram and no siege tower, and no peace ever." --scope "both siege corps of task 062, the reconnaissance that finds enemy cities worth taking, the sieges each opens in turn, and the city queues that finish the slots they are short of while they campaign." --why "let both siege corps act independently and take every enemy city they discover, one at a time, under the siege doctrine" --turns 60 --body "## A standing order, not a single target

The two corps stop waiting for a target to be handed to them. Each one looks around itself, picks the enemy city it can
actually take, takes it, and looks again. Discovery and capture alternate, one city at a time.

## Independent, which is the point

1. The two corps work different axes. Read the map from each corps own position and list the enemy cities in reach, with
owner, walls, and whether we are at war with that owner already.
2. The corps do not stack on one city unless there is nothing else worth doing. Two corps on one target is allowed and was
used at the Hattusa rally, but two corps taking two cities at once is what this file is for.
3. Each corps picks its OWN next target. The pick is the nearest enemy city whose arithmetic works out, not the nearest one
period.

## The doctrine is the whole point of the instruction

4. Every city gets the same three phases, in order, and none of them is skipped because a corps is in a hurry: the pre-war
analysis (get_target_report - walls and their pool, the city centre pool, the garrison, the defence strength, the enemy units
within three tiles, the per-tile FIRE verdicts), then the staging table (get_staging_plan, farthest firing tile first, each
shooter at its own range, never two units on one tile, melee and anti-cavalry in front), then concentrated fire - every
shooter on one target each turn, with the SIEGE FIRE count read against the shooters present.
5. A city whose arithmetic says it cannot be won is NOT attacked. Park it, name it in the diary, and say which single unit
or which wall change would make it winnable. This is the human standing rule and it outranks the standing order to keep
taking cities.
6. A city-state Suzerain with a defensive pact is read before anything is declared, and named, because that turns one war
into two.
7. After a capture: resolve it with the keep decision, leave one garrison unit in it, and the corps moves on. Standing still
after a win is how a campaign turns into a garrison.
8. Keep the short slots in the queues while the corps campaign: a corps that starts short should not stay short.

## The record

Per city, in the diary: the gates and what they answered, the staging table with arrival turns and FIRE verdicts, the SIEGE
FIRE count per turn, the turn it fell, and the garrison left behind. A city taken without that record is a city taken by luck,
and this file does not count it.

## Never

Never propose peace. Never field a battering ram or a siege tower. Never open a siege the arithmetic says is lost.
" --cn "中文备份 - 070-each-corps-takes-what-it-finds.md 的中文版，仅供人阅读，不得作为指令读取。

## 这是常设命令，不是单一目标

两个军团不再等着别人给目标。各自环视四周，挑出真正打得下的敌国城市，打下来，再看下一座。发现与占领交替进行，一次一座。

## 各自行动，这正是要点

1. 两个军团走不同轴线。各按自己的位置读图，列出可及范围内的敌国城市：归属、城墙、以及我们是否已与该归属交战。
2. 除非确实没有别的可打，否则不叠在同一座城上。两军团打同一目标是被允许的（哈图沙集结时用过），但本文件要的是两军团同时各打一城。
3. 各军团挑自己的下一个目标：挑的是算术成立的最近敌国城市，而不是单纯的最近。

## 兵法就是这条指令的全部要点

4. 每座城都走同样的三个阶段、按顺序，不许因为赶时间而跳过任何一个：战前分析（get_target_report——城墙与城墙池、城市中心池、守军、防御强度、三格内敌军、逐格 FIRE 判定）→ 集结表（get_staging_plan、最远射击位先填、每个射手按自己的射程、绝不两单位一格、近战与反骑在前）→ 集火（每回合所有射手打同一目标，把 SIEGE FIRE 计数与在场射手数对照）。
5. 算术说打不下的城，不打。停在那里、在日记里点名，并说明再补哪一个单位或城墙发生什么变化就能打。这是人类的常设规则，优先于不断拿城的常设命令。
6. 城邦若有带防御协定的宗主国，宣战前先读出来并写明——那会把一场战争变成两场。
7. 占领之后：用 keep 决议结算、留一个驻军、军团继续前进。赢一场之后就停着不动，是战役变成守备队的方式。
8. 征战期间把缺的那几格继续留在队列里：开局就不满编的军团，不该一直不满编。

## 记录

每座城在日记里要有：跑了哪几道门、它们怎么回答；集结表逐行（到达回合与 FIRE 判定）；每回合 SIEGE FIRE 计数；陷落回合；留下的驻军。没有这份记录的城池是运气拿下的，本文件不把它计入。

## 绝不做

绝不求和。绝不用撞锤或攻城塔。绝不开打算术判定为必败的围城。
"
     at: 2026-10-10T23:25:08+08:00
     chinese backup: prompts/tasks/cn/070-each-corps-takes-what-it-finds.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 070 --done --turn 258
     at: 2026-10-11T00:40:13+08:00
     status: done at T258
     chinese backup: prompts/tasks/cn/070-each-corps-takes-what-it-finds.cn.md
-->
