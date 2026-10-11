# TEMP TASK 074 - Each siege corps picks its own enemy city and takes it

added:     2026-10-11 (human instruction: 两个攻城军团，各自挑选敌国目标城市，并占领)
expires:   turn 307 - 40 turn(s) from T267, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count >= 2 enemy cities have been captured since this file was published, at least one by each of
           the two siege corps, with the diary naming which corps took which city and when.
overrides: the retired task 067 and task 070 on target selection: each corps now chooses its own enemy city to
           take, instead of the first newly seen city being designated for it. Everything else
           stands - the four phases of the assault, the staging table before the first volley, the
           taking unit arithmetic, the concentration of fire, no battering ram, no siege tower and
           no peace.
scope:     both siege corps - their reconnaissance, the enemy city each one chooses, the siege it opens on it -
           plus the city queues that finish the slots they are short of while they campaign.

## The order

Two corps, two choices. Each one picks the enemy city it will take, and takes it. Neither waits for a designation and neither waits
for the other.

## How a target is chosen, and it is not taste

1. Read from each corps own position: which enemy cities are visible, who owns them, and whether we are already at war with that owner.
2. Read the two pools before the choice: get_target_report prints the walls and their pool, the city centre pool, the garrison, the defence strength
and the enemy units within three tiles. A city is a candidate only if the arithmetic on those numbers says the corps can break it.
3. The pick is the nearest city that passes step 2. Distance decides among the winnable, never over them.
4. A city-state Suzerain with a defensive pact is read before anything is declared, and named, because that turns one war into two.
5. Once the first volley is fired, the target is frozen. The corps does not shop for a better city mid-siege.
6. The two corps pick different cities unless there is only one worth taking. Two thin attacks kill neither; one city with the whole force kills
one.

## Then the four phases, every time

7. The pre-war analysis and its arithmetic in the diary, then the staging table from get_staging_plan - farthest firing tile first, each shooter at its
own range, never two units on one tile - and only then the first volley.
8. The walls to zero, then the city centre pool to zero, then the walk-in: a melee unit moves onto the city tile. Ranged and siege units never
capture.
9. The taking unit attack counts as pool damage, and the walk-in needs movement left - the choice between spending that attack and holding it is
written out in task 072.
10. Resolve the capture with the keep decision and leave one garrison unit. Never a battering ram, never a siege tower, never peace.

## The record

Per city: the two pools as read, the arithmetic, the staging table with its FIRE verdicts, the SIEGE FIRE count per turn, the turn it fell, the
garrison left behind, and which corps took it. A city taken without that record does not count for this file.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Each siege corps picks its own enemy city and takes it" --slug each-corps-picks-its-own-city --instruction 两个攻城军团，各自挑选敌国目标城市，并占领 --done-when "count >= 2 enemy cities have been captured since this file was published, at least one by each of the two siege corps, with the diary naming which corps took which city and when." --overrides "the retired task 067 and task 070 on target selection: each corps now chooses its own enemy city to take, instead of the first newly seen city being designated for it. Everything else stands - the four phases of the assault, the staging table before the first volley, the taking unit arithmetic, the concentration of fire, no battering ram, no siege tower and no peace." --scope "both siege corps - their reconnaissance, the enemy city each one chooses, the siege it opens on it - plus the city queues that finish the slots they are short of while they campaign." --why "let each siege corps choose its own enemy city and take it" --turns 40 --body "## The order

Two corps, two choices. Each one picks the enemy city it will take, and takes it. Neither waits for a designation and neither waits
for the other.

## How a target is chosen, and it is not taste

1. Read from each corps own position: which enemy cities are visible, who owns them, and whether we are already at war with that owner.
2. Read the two pools before the choice: get_target_report prints the walls and their pool, the city centre pool, the garrison, the defence strength
and the enemy units within three tiles. A city is a candidate only if the arithmetic on those numbers says the corps can break it.
3. The pick is the nearest city that passes step 2. Distance decides among the winnable, never over them.
4. A city-state Suzerain with a defensive pact is read before anything is declared, and named, because that turns one war into two.
5. Once the first volley is fired, the target is frozen. The corps does not shop for a better city mid-siege.
6. The two corps pick different cities unless there is only one worth taking. Two thin attacks kill neither; one city with the whole force kills
one.

## Then the four phases, every time

7. The pre-war analysis and its arithmetic in the diary, then the staging table from get_staging_plan - farthest firing tile first, each shooter at its
own range, never two units on one tile - and only then the first volley.
8. The walls to zero, then the city centre pool to zero, then the walk-in: a melee unit moves onto the city tile. Ranged and siege units never
capture.
9. The taking unit attack counts as pool damage, and the walk-in needs movement left - the choice between spending that attack and holding it is
written out in task 072.
10. Resolve the capture with the keep decision and leave one garrison unit. Never a battering ram, never a siege tower, never peace.

## The record

Per city: the two pools as read, the arithmetic, the staging table with its FIRE verdicts, the SIEGE FIRE count per turn, the turn it fell, the
garrison left behind, and which corps took it. A city taken without that record does not count for this file.
" --cn "中文备份 - 074-each-corps-picks-its-own-city.md 的中文版，仅供人阅读，不得作为指令读取。

## 命令

两个军团，两个选择。各自挑出自己要拿的敌国城市，然后拿下来。不等指派，也不等对方。

## 目标怎么挑——不是凭喜好

1. 各按自己的位置读图：哪些敌国城市可见、归属是谁、我们是否已与该归属交战。
2. 选择之前先读两条血条：get_target_report 打印城墙与城墙池、城市中心池、守军、防御强度，以及三格内的敌军。只有这些数字上的算术说明这支部队打得下，那座城才是候选。
3. 在通过第 2 步的城市里挑最近的。距离只在打得下的范围里做决定，绝不越过它。
4. 城邦若带防御协定的宗主国，宣战前读出并点名——那会把一场战争变成两场。
5. 第一轮齐射之后目标冻结，不在围城途中换一座更好的城。
6. 两个军团挑不同的城，除非只有一座值得打。两路薄攻，两路都打不死；一城集中全军，才打得死一城。

## 然后每次都走四个阶段

7. 战前分析与算术写进日记 → get_staging_plan 的集结表（最远射击位先填、各按自己射程、绝不两单位一格）→ 然后才第一轮齐射。
8. 先把墙打到 0，再把中心池打到 0，然后走进城：由近战单位移动到城格。远程与攻城单位永远不能占领。
9. 占城部队的攻击计入池伤害，且进城需要留有移动力——是花掉这一击还是留下移动力，写在 072 里。
10. 用 keep 决议结算并留一个驻军。绝不用撞锤、绝不用攻城塔、绝不求和。

## 记录

每座城要有：读到时的两条血条、算术、逐格 FIRE 的集结表、每回合 SIEGE FIRE 计数、陷落回合、留下的驻军、以及是哪支军团拿下的。没有这份记录的城，本文件不计。
"
     at: 2026-10-11T01:31:46+08:00
     chinese backup: prompts/tasks/cn/074-each-corps-picks-its-own-city.cn.md
-->
